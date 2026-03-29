"""Chat service for persistent, context-grounded repository Q&A."""

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator, Optional

from app.config import get_settings
from app.models.schemas import (
    ChatExportFormat,
    ChatMessage,
    ChatMessageResponse,
    ChatMessagesResponse,
    ChatRole,
    ChatSessionCreateRequest,
    ChatSessionResponse,
    SourceCitation,
)
from app.repositories.chat_repository import ChatRepository
from app.services.podcast_service import get_podcast_service

settings = get_settings()
logger = logging.getLogger(__name__)

_chat_service_instance: Optional["ChatService"] = None


def get_chat_service() -> "ChatService":
    """Get the singleton ChatService instance."""
    global _chat_service_instance
    if _chat_service_instance is None:
        _chat_service_instance = ChatService()
    return _chat_service_instance


class ChatServiceError(Exception):
    """Service-level exception with typed API error code."""

    def __init__(self, *, code: str, message: str, status_code: int):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


@dataclass
class RetrievalChunk:
    """Retrieval unit used for ranking and citation."""

    path: str
    chunk_id: str
    source_type: str
    text: str
    score: float = 0.0


class ChatService:
    """Coordinates chat persistence, context retrieval, and answer generation."""

    def __init__(self, repository: Optional[ChatRepository] = None):
        self.repository = repository or ChatRepository(settings.chat_db_path)
        self._initialized = False

    def initialize(self):
        """Initialize SQLite schema once."""
        if self._initialized:
            return
        self.repository.initialize()
        self._initialized = True
        logger.info("Chat storage initialized", extra={"chat_db_path": str(settings.chat_db_path)})

    async def create_session(self, request: ChatSessionCreateRequest) -> ChatSessionResponse:
        """Create a persistent chat session."""
        self.initialize()
        context = self._resolve_session_context(
            repo_id=request.repo_id,
            podcast_id=request.podcast_id,
            selected_files=request.selected_files,
            script_path=request.script_path,
        )
        title = request.title or self._default_title(
            repo_id=context["repo_id"],
            podcast_id=context["podcast_id"],
        )
        record = self.repository.create_session(
            title=title,
            repo_id=context["repo_id"],
            podcast_id=context["podcast_id"],
            selected_files=context["selected_files"],
            script_path=context["script_path"],
        )
        return self._session_from_record(record)

    async def get_messages(self, session_id: str) -> ChatMessagesResponse:
        """Fetch all messages for one session."""
        self.initialize()
        session = self._require_session(session_id)
        messages = [self._message_from_record(row) for row in self.repository.list_messages(session_id)]
        return ChatMessagesResponse(
            session=self._session_from_record(session),
            messages=messages,
        )

    async def send_message(self, session_id: str, content: str) -> ChatMessageResponse:
        """Persist user/assistant messages and return both."""
        self.initialize()
        content = content.strip()
        if not content:
            raise ChatServiceError(
                code="EMPTY_MESSAGE",
                message="Message content cannot be empty.",
                status_code=422,
            )

        session = self._require_session(session_id)
        start_time = time.monotonic()
        user_record = self.repository.create_message(
            session_id=session_id,
            role=ChatRole.USER.value,
            content=content,
            sources=[],
        )
        context_chunks = await self._build_ranked_context(session=session, question=content)
        prompt_chars = len(content) + sum(len(chunk.text) for chunk in context_chunks)
        answer, citations = await self._generate_answer_with_retries(
            question=content,
            context_chunks=context_chunks,
        )
        assistant_record = self.repository.create_message(
            session_id=session_id,
            role=ChatRole.ASSISTANT.value,
            content=answer,
            sources=[citation.model_dump() for citation in citations],
        )
        logger.info(
            "Chat response generated",
            extra={
                "session_id": session_id,
                "prompt_chars": prompt_chars,
                "context_chunks": len(context_chunks),
                "sources": len(citations),
                "latency_ms": int((time.monotonic() - start_time) * 1000),
            },
        )
        return ChatMessageResponse(
            session_id=session_id,
            user_message=self._message_from_record(user_record),
            assistant_message=self._message_from_record(assistant_record),
        )

    async def stream_message(self, session_id: str, content: str) -> AsyncIterator[str]:
        """Stream an answer over SSE while persisting final assistant message."""
        self.initialize()
        content = content.strip()
        if not content:
            raise ChatServiceError(
                code="EMPTY_MESSAGE",
                message="Message content cannot be empty.",
                status_code=422,
            )

        session = self._require_session(session_id)
        user_record = self.repository.create_message(
            session_id=session_id,
            role=ChatRole.USER.value,
            content=content,
            sources=[],
        )
        context_chunks = await self._build_ranked_context(session=session, question=content)
        answer, citations = await self._generate_answer_with_retries(
            question=content,
            context_chunks=context_chunks,
        )
        assistant_record = self.repository.create_message(
            session_id=session_id,
            role=ChatRole.ASSISTANT.value,
            content=answer,
            sources=[citation.model_dump() for citation in citations],
        )

        user_schema = self._message_from_record(user_record)
        assistant_schema = self._message_from_record(assistant_record)
        yield self._format_sse(
            "start",
            {
                "session_id": session_id,
                "user_message": user_schema.model_dump(mode="json"),
            },
        )
        for token in re.findall(r"\S+\s*", answer):
            yield self._format_sse("chunk", {"delta": token})
            await asyncio.sleep(0.01)
        yield self._format_sse(
            "done",
            {
                "session_id": session_id,
                "user_message": user_schema.model_dump(mode="json"),
                "assistant_message": assistant_schema.model_dump(mode="json"),
            },
        )

    async def export_transcript(self, session_id: str, fmt: ChatExportFormat) -> tuple[str, str, str]:
        """Export chat transcript as markdown or JSON."""
        self.initialize()
        session = self._require_session(session_id)
        messages = [self._message_from_record(row) for row in self.repository.list_messages(session_id)]
        session_schema = self._session_from_record(session)

        if fmt == ChatExportFormat.JSON:
            payload = {
                "session": session_schema.model_dump(mode="json"),
                "messages": [message.model_dump(mode="json") for message in messages],
            }
            return (
                f"chat-{session_id}.json",
                "application/json",
                json.dumps(payload, indent=2),
            )

        lines = [
            f"# {session_schema.title}",
            "",
            f"- Session: `{session_schema.session_id}`",
            f"- Repo ID: `{session_schema.repo_id or 'n/a'}`",
            f"- Podcast ID: `{session_schema.podcast_id or 'n/a'}`",
            f"- Created: {session_schema.created_at.isoformat()}",
            "",
        ]
        for message in messages:
            lines.extend(
                [
                    f"## {message.role.value.title()} ({message.created_at.isoformat()})",
                    "",
                    message.content,
                    "",
                ]
            )
            if message.sources:
                lines.append("Sources:")
                for source in message.sources:
                    lines.append(
                        f"- `{source.path}` [{source.chunk_id}] ({source.source_type})"
                    )
                lines.append("")

        return (f"chat-{session_id}.md", "text/markdown", "\n".join(lines))

    def _resolve_session_context(
        self,
        *,
        repo_id: Optional[str],
        podcast_id: Optional[str],
        selected_files: list[str],
        script_path: Optional[str],
    ) -> dict:
        """Resolve missing context fields from podcast metadata when possible."""
        podcast_service = get_podcast_service()
        resolved_repo_id = repo_id
        resolved_podcast_id = podcast_id
        resolved_selected_files = list(selected_files)
        resolved_script_path = script_path

        if podcast_id:
            podcast = podcast_service.podcasts.get(podcast_id)
            if not podcast:
                raise ChatServiceError(
                    code="PODCAST_NOT_FOUND",
                    message="Podcast not found for chat session creation.",
                    status_code=404,
                )
            if not resolved_repo_id:
                resolved_repo_id = podcast.get("repo_id")
            if not resolved_selected_files:
                resolved_selected_files = list(podcast.get("selected_files") or [])
            if not resolved_script_path:
                resolved_script_path = podcast.get("script_output_path")

        if resolved_repo_id and resolved_repo_id not in podcast_service.repos:
            raise ChatServiceError(
                code="REPO_NOT_FOUND",
                message="Repository context was not found for this chat session.",
                status_code=404,
            )

        if resolved_script_path:
            path = Path(resolved_script_path)
            if not path.exists():
                logger.info(
                    "Chat session script path missing; falling back to repository-only context",
                    extra={"script_path": resolved_script_path},
                )
                resolved_script_path = None

        return {
            "repo_id": resolved_repo_id,
            "podcast_id": resolved_podcast_id,
            "selected_files": resolved_selected_files,
            "script_path": resolved_script_path,
        }

    def _default_title(self, *, repo_id: Optional[str], podcast_id: Optional[str]) -> str:
        """Create a stable default chat session title."""
        if podcast_id:
            return f"Podcast chat {podcast_id}"
        if repo_id:
            podcast_service = get_podcast_service()
            repo = podcast_service.repos.get(repo_id, {})
            repo_name = repo.get("name")
            if repo_name:
                return f"{repo_name} Q&A"
            return f"Repository chat {repo_id}"
        return "Repository Q&A"

    def _require_session(self, session_id: str) -> dict:
        """Return session record or raise typed not-found error."""
        session = self.repository.get_session(session_id)
        if session is None:
            raise ChatServiceError(
                code="SESSION_NOT_FOUND",
                message="Chat session not found.",
                status_code=404,
            )
        return session

    async def _generate_answer_with_retries(
        self,
        *,
        question: str,
        context_chunks: list[RetrievalChunk],
    ) -> tuple[str, list[SourceCitation]]:
        """Wrap answer generation with timeout and retry policy."""
        retries = max(settings.chat_generation_retries, 0)
        attempts = retries + 1
        last_error: Optional[Exception] = None
        for attempt in range(1, attempts + 1):
            try:
                return await asyncio.wait_for(
                    self._generate_answer(question=question, context_chunks=context_chunks),
                    timeout=settings.chat_generation_timeout_seconds,
                )
            except asyncio.TimeoutError as exc:
                last_error = exc
                logger.warning(
                    "Chat generation timed out",
                    extra={"attempt": attempt, "attempts": attempts},
                )
            except Exception as exc:  # pragma: no cover - defensive fallback
                last_error = exc
                logger.exception(
                    "Chat generation failed",
                    extra={"attempt": attempt, "attempts": attempts},
                )
            if attempt < attempts:
                await asyncio.sleep(0.08 * attempt)

        logger.error("Chat generation failed after retries", extra={"error": str(last_error)})
        return (
            "I could not generate a reliable answer right now. Please retry with a narrower question.",
            [],
        )

    async def _generate_answer(
        self,
        *,
        question: str,
        context_chunks: list[RetrievalChunk],
    ) -> tuple[str, list[SourceCitation]]:
        """Generate a grounded response from ranked context chunks."""
        if not context_chunks:
            return (
                "I do not have enough repository or script context for this question. "
                "Please regenerate the podcast or ask about files that were selected.",
                [],
            )

        top_chunks = context_chunks[:3]
        citations = [self._citation_from_chunk(chunk) for chunk in top_chunks]
        lines = [
            f'Question: "{question.strip()}"',
            "",
            "Grounded answer:",
        ]
        for index, chunk in enumerate(top_chunks, start=1):
            snippet = self._snippet(chunk.text, max_chars=260)
            lines.append(f"{index}. {snippet}")
        lines.append("")
        lines.append("Ask a follow-up with a specific file/function if you want deeper detail.")
        return ("\n".join(lines), citations)

    async def _build_ranked_context(self, *, session: dict, question: str) -> list[RetrievalChunk]:
        """Build, score, and trim retrieval chunks for the question."""
        script_chunks = self._load_script_chunks(session)
        file_chunks = self._load_repo_chunks(session)
        chunks = script_chunks + file_chunks
        if not chunks:
            return []

        terms = self._tokenize(question)
        for chunk in chunks:
            chunk.score = self._score_chunk(chunk=chunk, terms=terms)

        ranked = sorted(chunks, key=lambda item: item.score, reverse=True)
        top_k = max(settings.chat_retrieval_top_k, 1)
        max_chars = max(settings.chat_max_context_chars, 2000)
        selected: list[RetrievalChunk] = []
        current_chars = 0
        for chunk in ranked:
            if len(selected) >= top_k:
                break
            projected = current_chars + len(chunk.text)
            if selected and projected > max_chars:
                break
            selected.append(chunk)
            current_chars = projected
        return selected

    def _load_script_chunks(self, session: dict) -> list[RetrievalChunk]:
        """Load script output chunks if available."""
        script_path = session.get("script_path")
        if not script_path:
            return []
        path = Path(script_path)
        if not path.exists() or not path.is_file():
            return []
        text = self._read_text_file(path)
        if not text:
            return []
        return self._chunk_text(
            text=text,
            path=str(path),
            source_type="script",
        )

    def _load_repo_chunks(self, session: dict) -> list[RetrievalChunk]:
        """Load selected repository file chunks."""
        repo_id = session.get("repo_id")
        if not repo_id:
            return []

        podcast_service = get_podcast_service()
        repo = podcast_service.repos.get(repo_id)
        if not repo:
            return []

        repo_root = Path(repo["path"]).resolve()
        selected_files = session.get("selected_files") or []
        if selected_files:
            candidates = self._resolve_selected_paths(repo_root=repo_root, selected_files=selected_files)
        else:
            candidates = self._default_candidate_paths(repo_root=repo_root)

        chunks: list[RetrievalChunk] = []
        for file_path in candidates:
            text = self._read_text_file(file_path)
            if not text:
                continue
            rel_path = str(file_path.relative_to(repo_root))
            chunks.extend(self._chunk_text(text=text, path=rel_path, source_type="file"))
        return chunks

    def _resolve_selected_paths(self, *, repo_root: Path, selected_files: list[str]) -> list[Path]:
        """Resolve selected file/directory list into readable files."""
        root = repo_root.resolve()
        resolved: list[Path] = []
        for rel_path in selected_files:
            candidate = (root / rel_path).resolve()
            if not self._is_relative_to(candidate, root) or not candidate.exists():
                continue
            if candidate.is_dir():
                resolved.extend(self._iter_text_files(candidate))
            elif candidate.is_file():
                resolved.append(candidate)
        # Stable dedupe by path order.
        deduped: dict[str, Path] = {}
        for item in resolved:
            deduped[str(item)] = item
            if len(deduped) >= 40:
                break
        return list(deduped.values())

    def _default_candidate_paths(self, *, repo_root: Path) -> list[Path]:
        """Pick a bounded set of files when no explicit selection exists."""
        defaults: list[Path] = []
        readme = repo_root / "README.md"
        if readme.exists() and readme.is_file():
            defaults.append(readme)
        defaults.extend(self._iter_text_files(repo_root))
        # Keep this bounded for predictable prompt size and latency.
        deduped: dict[str, Path] = {}
        for item in defaults:
            deduped[str(item)] = item
            if len(deduped) >= 40:
                break
        return list(deduped.values())

    def _iter_text_files(self, path: Path) -> list[Path]:
        """Recursively gather likely-text source files."""
        ignored_dirs = {
            ".git",
            ".next",
            "node_modules",
            "__pycache__",
            ".venv",
            "venv",
            "dist",
            "build",
        }
        allowed_ext = {
            ".md",
            ".txt",
            ".py",
            ".js",
            ".ts",
            ".tsx",
            ".jsx",
            ".json",
            ".yaml",
            ".yml",
            ".toml",
            ".ini",
            ".java",
            ".go",
            ".rs",
            ".c",
            ".h",
            ".cpp",
            ".hpp",
            ".sh",
        }
        results: list[Path] = []
        if path.is_file():
            return [path] if path.suffix.lower() in allowed_ext else []

        for file_path in sorted(path.rglob("*")):
            if len(results) >= 80:
                break
            if not file_path.is_file():
                continue
            if any(part in ignored_dirs for part in file_path.parts):
                continue
            if file_path.suffix.lower() not in allowed_ext:
                continue
            results.append(file_path)
        return results

    def _chunk_text(self, *, text: str, path: str, source_type: str) -> list[RetrievalChunk]:
        """Split text into bounded, overlapping chunks."""
        chunk_size = max(settings.chat_chunk_size, 300)
        overlap = min(max(settings.chat_chunk_overlap, 0), chunk_size // 2)
        chunks: list[RetrievalChunk] = []
        idx = 0
        cursor = 0
        length = len(text)
        while cursor < length:
            window = text[cursor : cursor + chunk_size]
            if len(window.strip()) > 20:
                chunks.append(
                    RetrievalChunk(
                        path=path,
                        chunk_id=f"{source_type}-{idx}",
                        source_type=source_type,
                        text=window,
                    )
                )
            if cursor + chunk_size >= length:
                break
            cursor += chunk_size - overlap
            idx += 1
            if idx >= 200:
                break
        return chunks

    def _score_chunk(self, *, chunk: RetrievalChunk, terms: list[str]) -> float:
        """Score chunks using keyword overlap + small domain boosts."""
        text = chunk.text.lower()
        path = chunk.path.lower()
        if not terms:
            base = 0.01
        else:
            matches = sum(text.count(term) for term in terms)
            unique_hits = sum(1 for term in terms if term in text)
            base = float(matches + unique_hits * 1.3)

        if chunk.source_type == "script":
            base += 0.4
        if "readme" in path:
            base += 0.3
        if chunk.chunk_id.endswith("-0"):
            base += 0.1
        return base

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Extract lowercased query terms for retrieval scoring."""
        candidates = re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", text.lower())
        seen: set[str] = set()
        terms: list[str] = []
        for token in candidates:
            if token in seen:
                continue
            seen.add(token)
            terms.append(token)
            if len(terms) >= 24:
                break
        return terms

    @staticmethod
    def _snippet(text: str, *, max_chars: int) -> str:
        compact = re.sub(r"\s+", " ", text).strip()
        if len(compact) <= max_chars:
            return compact
        return compact[: max_chars - 3].rstrip() + "..."

    def _citation_from_chunk(self, chunk: RetrievalChunk) -> SourceCitation:
        """Convert retrieval chunk to source citation schema."""
        return SourceCitation(
            path=chunk.path,
            chunk_id=chunk.chunk_id,
            source_type=chunk.source_type,
            snippet=self._snippet(chunk.text, max_chars=180),
            score=round(chunk.score, 3),
        )

    @staticmethod
    def _format_sse(event: str, data: dict) -> str:
        return f"event: {event}\ndata: {json.dumps(data)}\n\n"

    @staticmethod
    def _read_text_file(path: Path) -> str:
        """Read text file with size guard and UTF-8 fallback behavior."""
        try:
            if path.stat().st_size > 180_000:
                return ""
            return path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return ""

    @staticmethod
    def _is_relative_to(path: Path, parent: Path) -> bool:
        try:
            path.relative_to(parent)
            return True
        except ValueError:
            return False

    @staticmethod
    def _session_from_record(record: dict) -> ChatSessionResponse:
        return ChatSessionResponse(
            session_id=record["id"],
            title=record["title"],
            repo_id=record.get("repo_id"),
            podcast_id=record.get("podcast_id"),
            selected_files=record.get("selected_files") or [],
            script_path=record.get("script_path"),
            created_at=datetime.fromisoformat(record["created_at"]),
            updated_at=datetime.fromisoformat(record["updated_at"]),
        )

    @staticmethod
    def _message_from_record(record: dict) -> ChatMessage:
        return ChatMessage(
            message_id=record["id"],
            session_id=record["session_id"],
            role=ChatRole(record["role"]),
            content=record["content"],
            sources=[SourceCitation(**item) for item in (record.get("sources") or [])],
            created_at=datetime.fromisoformat(record["created_at"]),
        )
