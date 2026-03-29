"""Unit tests for chat SQLite repository."""

from app.repositories.chat_repository import ChatRepository


def test_chat_repository_persists_sessions_and_messages(tmp_path):
    db_path = tmp_path / "chat.sqlite3"
    repository = ChatRepository(str(db_path))
    repository.initialize()

    session = repository.create_session(
        title="Podcast chat",
        repo_id="repo1234",
        podcast_id="pod1234",
        selected_files=["src/main.py", "README.md"],
        script_path="/tmp/script.md",
    )

    repository.create_message(
        session_id=session["id"],
        role="user",
        content="How does the service layer work?",
        sources=[],
    )
    repository.create_message(
        session_id=session["id"],
        role="assistant",
        content="It coordinates repository analysis and audio synthesis.",
        sources=[{"path": "src/main.py", "chunk_id": "file-0", "source_type": "file"}],
    )

    reloaded = ChatRepository(str(db_path))
    reloaded.initialize()
    loaded_session = reloaded.get_session(session["id"])
    loaded_messages = reloaded.list_messages(session["id"])

    assert loaded_session is not None
    assert loaded_session["repo_id"] == "repo1234"
    assert loaded_session["selected_files"] == ["src/main.py", "README.md"]
    assert len(loaded_messages) == 2
    assert loaded_messages[0]["role"] == "user"
    assert loaded_messages[1]["sources"][0]["path"] == "src/main.py"
