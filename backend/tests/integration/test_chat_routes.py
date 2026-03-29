"""Integration tests for chat API routes."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import (
    ChatMessage,
    ChatMessageResponse,
    ChatMessagesResponse,
    ChatRole,
    ChatSessionResponse,
    SourceCitation,
)
from app.services.chat_service import ChatServiceError


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_chat_service():
    now = datetime.utcnow()
    session = ChatSessionResponse(
        session_id="ses1234567890",
        title="Podcast chat",
        repo_id="repo1234",
        podcast_id="pod1234",
        selected_files=["README.md"],
        script_path="/tmp/script.md",
        created_at=now,
        updated_at=now,
    )
    user_message = ChatMessage(
        message_id="msg-user-1",
        session_id=session.session_id,
        role=ChatRole.USER,
        content="What is this repository about?",
        sources=[],
        created_at=now,
    )
    assistant_message = ChatMessage(
        message_id="msg-assistant-1",
        session_id=session.session_id,
        role=ChatRole.ASSISTANT,
        content="It contains a FastAPI backend and Next.js frontend.",
        sources=[
            SourceCitation(
                path="README.md",
                chunk_id="file-0",
                source_type="file",
                snippet="Podcast-Anything converts repos to educational audio.",
                score=1.2,
            )
        ],
        created_at=now,
    )

    service = MagicMock()
    service.create_session = AsyncMock(return_value=session)
    service.get_messages = AsyncMock(
        return_value=ChatMessagesResponse(session=session, messages=[user_message, assistant_message])
    )
    service.send_message = AsyncMock(
        return_value=ChatMessageResponse(
            session_id=session.session_id,
            user_message=user_message,
            assistant_message=assistant_message,
        )
    )

    async def stream_message(session_id: str, content: str):
        yield "event: start\ndata: {\"session_id\":\"ses1234567890\"}\n\n"
        yield "event: chunk\ndata: {\"delta\":\"hello \"}\n\n"
        yield "event: done\ndata: {\"session_id\":\"ses1234567890\"}\n\n"

    service.stream_message = stream_message
    service.export_transcript = AsyncMock(
        return_value=("chat-ses1234567890.md", "text/markdown", "# Chat export")
    )
    return service


class TestChatRoutes:
    @patch("app.api.routes.chat.get_chat_service")
    def test_create_session(self, mock_get_service, client, mock_chat_service):
        mock_get_service.return_value = mock_chat_service
        response = client.post("/api/v1/chat/sessions", json={"podcast_id": "pod1234"})

        assert response.status_code == 201
        data = response.json()
        assert data["session_id"] == "ses1234567890"
        assert data["podcast_id"] == "pod1234"

    @patch("app.api.routes.chat.get_chat_service")
    def test_get_messages(self, mock_get_service, client, mock_chat_service):
        mock_get_service.return_value = mock_chat_service
        response = client.get("/api/v1/chat/ses1234567890/messages")

        assert response.status_code == 200
        data = response.json()
        assert data["session"]["session_id"] == "ses1234567890"
        assert len(data["messages"]) == 2

    @patch("app.api.routes.chat.get_chat_service")
    def test_send_message(self, mock_get_service, client, mock_chat_service):
        mock_get_service.return_value = mock_chat_service
        response = client.post(
            "/api/v1/chat/ses1234567890/messages",
            json={"content": "Explain the architecture"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["assistant_message"]["role"] == "assistant"
        assert data["assistant_message"]["sources"][0]["path"] == "README.md"

    @patch("app.api.routes.chat.get_chat_service")
    def test_stream_message(self, mock_get_service, client, mock_chat_service):
        mock_get_service.return_value = mock_chat_service
        response = client.get(
            "/api/v1/chat/ses1234567890/stream",
            params={"question": "What are entry points?"},
        )

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        assert "event: done" in response.text

    @patch("app.api.routes.chat.get_chat_service")
    def test_export_transcript(self, mock_get_service, client, mock_chat_service):
        mock_get_service.return_value = mock_chat_service
        response = client.get(
            "/api/v1/chat/ses1234567890/export",
            params={"format": "markdown"},
        )

        assert response.status_code == 200
        assert response.headers["content-disposition"] == 'attachment; filename="chat-ses1234567890.md"'
        assert response.text == "# Chat export"

    @patch("app.api.routes.chat.get_chat_service")
    def test_typed_error_response(self, mock_get_service, client):
        service = MagicMock()
        service.create_session = AsyncMock(
            side_effect=ChatServiceError(
                code="PODCAST_NOT_FOUND",
                message="Podcast not found for chat session creation.",
                status_code=404,
            )
        )
        mock_get_service.return_value = service

        response = client.post("/api/v1/chat/sessions", json={"podcast_id": "missing"})
        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "PODCAST_NOT_FOUND"
