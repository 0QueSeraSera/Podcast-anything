"""SQLite repository for persistent chat sessions and messages."""

import json
import sqlite3
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional


class ChatRepository:
    """Repository layer over a local SQLite database."""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self._write_lock = threading.Lock()

    def initialize(self):
        """Create database file and tables if they do not exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    repo_id TEXT,
                    podcast_id TEXT,
                    selected_files_json TEXT NOT NULL,
                    script_path TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS chat_messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    sources_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_chat_messages_session_created
                    ON chat_messages(session_id, created_at);
                """
            )
            conn.commit()

    def create_session(
        self,
        *,
        title: str,
        repo_id: Optional[str],
        podcast_id: Optional[str],
        selected_files: list[str],
        script_path: Optional[str],
    ) -> dict:
        """Persist and return a new chat session record."""
        now = datetime.utcnow().isoformat()
        session_id = uuid.uuid4().hex[:12]
        with self._write_lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO chat_sessions (
                    id, title, repo_id, podcast_id, selected_files_json,
                    script_path, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    title,
                    repo_id,
                    podcast_id,
                    json.dumps(selected_files),
                    script_path,
                    now,
                    now,
                ),
            )
            conn.commit()
        return self.get_session(session_id=session_id) or {}

    def touch_session(self, session_id: str):
        """Update session updated_at timestamp."""
        with self._write_lock, self._connect() as conn:
            conn.execute(
                "UPDATE chat_sessions SET updated_at = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), session_id),
            )
            conn.commit()

    def get_session(self, session_id: str) -> Optional[dict]:
        """Return one chat session by id."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM chat_sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
        return self._parse_session_row(row) if row else None

    def create_message(
        self,
        *,
        session_id: str,
        role: str,
        content: str,
        sources: Optional[list[dict]] = None,
    ) -> dict:
        """Persist and return one chat message."""
        message_id = uuid.uuid4().hex[:12]
        created_at = datetime.utcnow().isoformat()
        payload_sources = sources or []
        with self._write_lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO chat_messages (id, session_id, role, content, sources_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    message_id,
                    session_id,
                    role,
                    content,
                    json.dumps(payload_sources),
                    created_at,
                ),
            )
            conn.execute(
                "UPDATE chat_sessions SET updated_at = ? WHERE id = ?",
                (created_at, session_id),
            )
            conn.commit()
        return self.get_message(message_id=message_id) or {}

    def get_message(self, message_id: str) -> Optional[dict]:
        """Return one message by id."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM chat_messages WHERE id = ?",
                (message_id,),
            ).fetchone()
        return self._parse_message_row(row) if row else None

    def list_messages(self, session_id: str) -> list[dict]:
        """Return all messages for a given session ordered by creation time."""
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM chat_messages
                WHERE session_id = ?
                ORDER BY created_at ASC
                """,
                (session_id,),
            ).fetchall()
        return [self._parse_message_row(row) for row in rows]

    def _connect(self) -> sqlite3.Connection:
        """Create a SQLite connection configured for dict-like access."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @staticmethod
    def _parse_session_row(row: sqlite3.Row) -> dict:
        return {
            "id": row["id"],
            "title": row["title"],
            "repo_id": row["repo_id"],
            "podcast_id": row["podcast_id"],
            "selected_files": json.loads(row["selected_files_json"] or "[]"),
            "script_path": row["script_path"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    @staticmethod
    def _parse_message_row(row: sqlite3.Row) -> dict:
        return {
            "id": row["id"],
            "session_id": row["session_id"],
            "role": row["role"],
            "content": row["content"],
            "sources": json.loads(row["sources_json"] or "[]"),
            "created_at": row["created_at"],
        }
