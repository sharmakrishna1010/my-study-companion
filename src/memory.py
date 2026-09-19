"""
memory.py -- In-memory session state for the Study Companion.

Supports multiple screenshots per context window.
"""

from PIL import Image


class Memory:
    """Holds all session state for one study session."""

    def __init__(self):
        self._screenshots: list[Image.Image] = []
        self._messages: list[dict] = []   # {"role": "user"|"model", "text": str}
        self._pet_state: str = "IDLE"

    # ------------------------------------------------------------------
    # Screenshots (multi-screenshot support)
    # ------------------------------------------------------------------

    def add_screenshot(self, image: Image.Image) -> None:
        """Append a screenshot to the context. Does NOT clear history."""
        self._screenshots.append(image)

    def set_screenshot(self, image: Image.Image) -> None:
        """Replace all screenshots with one and reset conversation."""
        self._screenshots = [image]
        self._messages = []

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

    def get_history(self) -> list[dict]:
        return list(self._messages)

    def clear_context(self) -> None:
        """Clear all screenshots and conversation history."""
        self._screenshots = []
        self._messages = []

    # ------------------------------------------------------------------
    # Pet state
    # ------------------------------------------------------------------

    def set_pet_state(self, state: str) -> None:
        self._pet_state = state

    def get_pet_state(self) -> str:
        return self._pet_state
