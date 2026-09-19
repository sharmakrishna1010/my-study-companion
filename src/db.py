"""
db.py -- Lightweight SQLite database for persistent chat session history.
"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

import config

DB_PATH = config.PROJECT_ROOT / "study_companion.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize database tables if they do not exist."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            );
        """)
        conn.commit()


def create_session(title: str | None = None) -> str:
    """Create a new chat session and return its ID."""
    init_db()
    session_id = str(uuid.uuid4())
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not title:
        title = f"Chat {datetime.now().strftime('%b %d, %H:%M')}"

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (session_id, title, now, now),
        )
        conn.commit()

    return session_id


def clean_empty_sessions() -> None:
    """Remove any session entries that have 0 messages in DB."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM sessions WHERE id NOT IN (
                SELECT DISTINCT session_id FROM messages
            )
        """)
        conn.commit()


def get_all_sessions() -> list[dict]:
    """Retrieve non-empty chat sessions sorted by updated_at descending."""
    clean_empty_sessions()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions ORDER BY updated_at DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def load_session_messages(session_id: str) -> list[dict]:
    """Load all messages for a given session_id."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role, content, timestamp FROM messages WHERE session_id = ? ORDER BY id ASC",
            (session_id,),
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def save_message(session_id: str, role: str, content: str) -> None:
    """Save a message into SQLite and update session timestamp & title."""
    init_db()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (session_id, role, content, now),
        )
        # Update session title if first user question
        if role == "user":
            cursor.execute("SELECT COUNT(*) as count FROM messages WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            if row and row["count"] <= 1:
                # Set title to snippet of question
                title_snippet = content.replace("\n", " ")[:35]
                if len(content) > 35:
                    title_snippet += "..."
                cursor.execute(
                    "UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?",
                    (title_snippet, now, session_id),
                )
            else:
                cursor.execute(
                    "UPDATE sessions SET updated_at = ? WHERE id = ?",
                    (now, session_id),
                )
        else:
            cursor.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (now, session_id),
            )
        conn.commit()


def delete_session(session_id: str) -> None:
    """Delete a chat session and its messages."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()


def delete_all_sessions() -> None:
    """Clear all chat history."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages")
        cursor.execute("DELETE FROM sessions")
        conn.commit()
