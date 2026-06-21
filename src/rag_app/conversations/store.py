"""SQLite-backed conversation session and message history."""

from __future__ import annotations

import re
import sqlite3
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from rag_app.core.exceptions import ConversationStoreError
from rag_app.documents.store import DATABASE_FILENAME

ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"
ROLE_SYSTEM = "system"
ALLOWED_MESSAGE_ROLES = frozenset({ROLE_USER, ROLE_ASSISTANT, ROLE_SYSTEM})

DEFAULT_SESSION_TITLE = "New conversation"
SESSION_TITLE_MAX_LENGTH = 40


@dataclass(frozen=True)
class ConversationSession:
    """Stored conversation session metadata."""

    session_id: str
    title: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class ConversationMessage:
    """Stored conversation message."""

    message_id: str
    session_id: str
    role: str
    content: str
    created_at: str


@dataclass(frozen=True)
class ConversationWithMessages:
    """One conversation session with its ordered messages."""

    session: ConversationSession
    messages: list[ConversationMessage]


class ConversationStore:
    """Manage conversation sessions and message history in SQLite."""

    def __init__(
        self,
        *,
        sqlite_dir: Path,
        now_factory: Callable[[], datetime] | None = None,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        self.sqlite_dir = sqlite_dir
        self.database_path = get_conversation_database_path(sqlite_dir)
        self._now_factory = now_factory or (lambda: datetime.now(UTC))
        self._id_factory = id_factory or (lambda: uuid.uuid4().hex)

    def initialize(self) -> Path:
        """Create the SQLite database and conversation tables."""

        try:
            self.sqlite_dir.mkdir(parents=True, exist_ok=True)
            with self._connect() as connection:
                connection.execute("PRAGMA foreign_keys = ON")
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS conversation_sessions (
                        session_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS conversation_messages (
                        message_id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY(session_id)
                            REFERENCES conversation_sessions(session_id)
                            ON DELETE CASCADE
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_conversation_messages_session
                    ON conversation_messages(session_id, created_at, message_id)
                    """
                )
                connection.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_conversation_sessions_updated
                    ON conversation_sessions(updated_at)
                    """
                )
        except OSError as exc:
            raise ConversationStoreError(
                f"Failed to initialize conversation directory: {exc}"
            ) from exc
        except sqlite3.Error as exc:
            raise ConversationStoreError(
                f"Failed to initialize conversation database: {exc}"
            ) from exc

        return self.database_path

    def create_session(self, title: str | None = None) -> ConversationSession:
        """Create a new conversation session."""

        clean_title = _clean_title(title) if title is not None else DEFAULT_SESSION_TITLE
        session_id = self._id_factory()
        now = self._now()
        self.initialize()

        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO conversation_sessions (
                        session_id,
                        title,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (session_id, clean_title, now, now),
                )
        except sqlite3.Error as exc:
            raise ConversationStoreError(f"Failed to create conversation: {exc}") from exc

        session = self.get_session(session_id)
        if session is None:
            raise ConversationStoreError("Conversation was not found after creation.")
        return session

    def list_sessions(self) -> list[ConversationSession]:
        """Return all sessions, newest updated first."""

        self.initialize()
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    """
                    SELECT * FROM conversation_sessions
                    ORDER BY updated_at DESC, created_at DESC, session_id DESC
                    """
                ).fetchall()
        except sqlite3.Error as exc:
            raise ConversationStoreError(f"Failed to list conversations: {exc}") from exc
        return [_session_from_row(row) for row in rows]

    def get_session(self, session_id: str) -> ConversationSession | None:
        """Return one session by ID."""

        self.initialize()
        try:
            with self._connect() as connection:
                row = connection.execute(
                    "SELECT * FROM conversation_sessions WHERE session_id = ?",
                    (session_id,),
                ).fetchone()
        except sqlite3.Error as exc:
            raise ConversationStoreError(f"Failed to get conversation: {exc}") from exc
        return _session_from_row(row) if row else None

    def get_messages(self, session_id: str) -> list[ConversationMessage]:
        """Return messages for one session in chronological order."""

        self._require_session(session_id)
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    """
                    SELECT * FROM conversation_messages
                    WHERE session_id = ?
                    ORDER BY created_at ASC, message_id ASC
                    """,
                    (session_id,),
                ).fetchall()
        except sqlite3.Error as exc:
            raise ConversationStoreError(f"Failed to list conversation messages: {exc}") from exc
        return [_message_from_row(row) for row in rows]

    def get_conversation(self, session_id: str) -> ConversationWithMessages:
        """Return one session and its ordered messages."""

        session = self._require_session(session_id)
        return ConversationWithMessages(
            session=session,
            messages=self.get_messages(session_id),
        )

    def add_message(self, session_id: str, role: str, content: str) -> ConversationMessage:
        """Append a message and update the parent session timestamp."""

        self._require_session(session_id)
        clean_role = _clean_role(role)
        clean_content = _clean_content(content)
        message_id = self._id_factory()
        now = self._now()

        try:
            with self._connect() as connection:
                connection.execute("PRAGMA foreign_keys = ON")
                connection.execute(
                    """
                    INSERT INTO conversation_messages (
                        message_id,
                        session_id,
                        role,
                        content,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (message_id, session_id, clean_role, clean_content, now),
                )
                connection.execute(
                    """
                    UPDATE conversation_sessions
                    SET updated_at = ?
                    WHERE session_id = ?
                    """,
                    (now, session_id),
                )
        except sqlite3.Error as exc:
            raise ConversationStoreError(f"Failed to add conversation message: {exc}") from exc

        messages = self.get_messages(session_id)
        for message in messages:
            if message.message_id == message_id:
                return message
        raise ConversationStoreError("Conversation message was not found after creation.")

    def get_or_create_session_for_first_user_message(
        self,
        content: str,
        *,
        session_id: str | None = None,
    ) -> ConversationSession:
        """Return an existing session or create one titled from the first user message."""

        clean_content = _clean_content(content)
        if session_id:
            return self._require_session(session_id)
        return self.create_session(title=generate_title_from_first_message(clean_content))

    def rename_session(self, session_id: str, title: str) -> ConversationSession:
        """Rename one conversation session."""

        self._require_session(session_id)
        clean_title = _clean_title(title)
        now = self._now()

        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    UPDATE conversation_sessions
                    SET title = ?, updated_at = ?
                    WHERE session_id = ?
                    """,
                    (clean_title, now, session_id),
                )
        except sqlite3.Error as exc:
            raise ConversationStoreError(f"Failed to rename conversation: {exc}") from exc

        session = self.get_session(session_id)
        if session is None:
            raise ConversationStoreError(f"Conversation not found after rename: {session_id}")
        return session

    def delete_session(self, session_id: str) -> int:
        """Delete one session and its SQLite messages."""

        self._require_session(session_id)
        try:
            with self._connect() as connection:
                connection.execute("PRAGMA foreign_keys = ON")
                message_count = connection.execute(
                    "SELECT COUNT(*) FROM conversation_messages WHERE session_id = ?",
                    (session_id,),
                ).fetchone()[0]
                connection.execute(
                    "DELETE FROM conversation_sessions WHERE session_id = ?",
                    (session_id,),
                )
        except sqlite3.Error as exc:
            raise ConversationStoreError(f"Failed to delete conversation: {exc}") from exc
        return int(message_count)

    def _require_session(self, session_id: str) -> ConversationSession:
        session = self.get_session(session_id)
        if session is None:
            raise ConversationStoreError(f"Conversation not found: {session_id}")
        return session

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _now(self) -> str:
        return self._now_factory().astimezone(UTC).isoformat()


def initialize_conversation_store(sqlite_dir: Path) -> Path:
    """Initialize the conversation SQLite tables and return the database path."""

    store = ConversationStore(sqlite_dir=sqlite_dir)
    return store.initialize()


def get_conversation_database_path(sqlite_dir: Path) -> Path:
    """Return the resolved SQLite database path for conversation history."""

    return sqlite_dir.expanduser().resolve() / DATABASE_FILENAME


def generate_title_from_first_message(content: str) -> str:
    """Generate a deterministic short title from the first user message."""

    clean_content = _clean_content(content)
    title = re.sub(r"\s+", " ", clean_content).strip()
    return title[:SESSION_TITLE_MAX_LENGTH]


def _clean_title(title: str | None) -> str:
    if title is None:
        raise ConversationStoreError("Conversation title must not be empty.")
    clean_title = re.sub(r"\s+", " ", title).strip()
    if not clean_title:
        raise ConversationStoreError("Conversation title must not be empty.")
    return clean_title[:SESSION_TITLE_MAX_LENGTH]


def _clean_role(role: str) -> str:
    clean_role = role.strip().lower()
    if clean_role not in ALLOWED_MESSAGE_ROLES:
        allowed = ", ".join(sorted(ALLOWED_MESSAGE_ROLES))
        raise ConversationStoreError(
            f"Unsupported conversation message role: {role}. Allowed roles: {allowed}."
        )
    return clean_role


def _clean_content(content: str) -> str:
    clean_content = content.strip()
    if not clean_content:
        raise ConversationStoreError("Conversation message content must not be empty.")
    return clean_content


def _session_from_row(row: sqlite3.Row) -> ConversationSession:
    return ConversationSession(
        session_id=row["session_id"],
        title=row["title"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _message_from_row(row: sqlite3.Row) -> ConversationMessage:
    return ConversationMessage(
        message_id=row["message_id"],
        session_id=row["session_id"],
        role=row["role"],
        content=row["content"],
        created_at=row["created_at"],
    )
