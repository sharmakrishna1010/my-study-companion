"""
memory.py -- In-memory session state & SQLite database integration for the Study Companion.

Supports multiple screenshots per context window and persistent chat session storage.
"""

from __future__ import annotations

from PIL import Image
import db


class Memory:
    """Holds all session state for study companion sessions."""

    def __init__(self):
        self._screenshots: list[Image.Image] = []
        self._messages: list[dict] = []   # {"role": "user"|"model", "text": str}
        self._pet_state: str = "IDLE"
        self._session_id: str | None = None

    # ------------------------------------------------------------------
    # Database Sessions
    # ------------------------------------------------------------------

    def start_new_session(self, title: str | None = None) -> None:
        """Reset session memory. Session is saved to DB lazily on first message."""
        self._session_id = None
        self._messages = []
        self._screenshots = []

    def load_session(self, session_id: str) -> list[dict]:
        """Load an existing chat session from SQLite."""
        self._session_id = session_id
        db_msgs = db.load_session_messages(session_id)
        self._messages = [{"role": m["role"], "text": m["content"]} for m in db_msgs]
        self._screenshots = []  # Screenshots are per active live turn
        return list(self._messages)

    def get_current_session_id(self) -> str | None:
        return self._session_id

    # ------------------------------------------------------------------
    # Screenshots (multi-screenshot support)
    # ------------------------------------------------------------------

    def add_screenshot(self, image: Image.Image) -> None:
        """Append a screenshot to the context. Does NOT clear history."""
        self._screenshots.append(image)

    def set_screenshot(self, image: Image.Image) -> None:
        """Replace all screenshots with one."""
        self._screenshots = [image]

    def remove_screenshot(self, index: int) -> None:
        """Remove the screenshot at the given index."""
        if 0 <= index < len(self._screenshots):
            self._screenshots.pop(index)

    def get_screenshots(self) -> list[Image.Image]:
        return list(self._screenshots)

    def get_screenshot(self) -> Image.Image | None:
        """Return the most-recent screenshot (or None)."""
        return self._screenshots[-1] if self._screenshots else None

    def has_screenshot(self) -> bool:
        return len(self._screenshots) > 0

    def screenshot_count(self) -> int:
        return len(self._screenshots)

    # ------------------------------------------------------------------
    # Conversation history
    # ------------------------------------------------------------------

    def add_message(self, role: str, text: str) -> None:
        assert role in ("user", "model"), f"Unknown role: {role}"
        self._messages.append({"role": role, "text": text})

        # Lazy creation of session in DB on first message
        if self._session_id is None:
            self._session_id = db.create_session()

        db.save_message(self._session_id, role, text)

    def get_history(self) -> list[dict]:
        return list(self._messages)

    def clear_context(self) -> None:
        """Clear all screenshots and start a fresh session context."""
        self._screenshots = []
        self.start_new_session()

    # ------------------------------------------------------------------
    # Pet state
    # ------------------------------------------------------------------

    def set_pet_state(self, state: str) -> None:
        self._pet_state = state

    def get_pet_state(self) -> str:
        return self._pet_state
