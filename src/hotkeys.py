"""
hotkeys.py -- Global hotkey management using pynput.

Supports registering multiple hotkey combinations in a single listener.
All callbacks fire on the main tkinter thread via root.after(0, cb).
"""

from __future__ import annotations

from typing import Callable
from pynput import keyboard
import config


class HotkeyManager:
    """
    Manages one or more global hotkey combinations.

    Usage
    -----
    mgr = HotkeyManager()
    mgr.register(config.HOTKEY_MODIFIERS, config.HOTKEY_KEY, my_callback)
    mgr.register({"ctrl", "alt"}, "e", another_callback)
    mgr.start()
    ...
    mgr.stop()
    """

    def __init__(self):
        self._hotkey_map: dict[str, Callable] = {}
        self._listener: keyboard.GlobalHotKeys | None = None

    @staticmethod
    def build_string(modifiers: set[str], key: str) -> str:
        """Build the pynput hotkey string, e.g. '<ctrl>+<alt>+s'."""
        parts = []
        for mod in ("ctrl", "alt", "shift"):
            if mod in modifiers:
                parts.append(f"<{mod}>")
        parts.append(key.lower())
        return "+".join(parts)

    def register(
        self,
        modifiers: set[str],
        key: str,
        callback: Callable[[], None],
    ) -> str:
        """Register a hotkey. Returns the hotkey string for logging."""
        hotkey_str = self.build_string(modifiers, key)
        self._hotkey_map[hotkey_str] = callback
        return hotkey_str

    def start(self) -> None:
        """Start a single GlobalHotKeys listener for all registered hotkeys."""
        if not self._hotkey_map:
            print("[hotkeys] No hotkeys registered.")
            return
        for k in self._hotkey_map:
            print(f"[hotkeys] Registered: {k}")
        try:
            self._listener = keyboard.GlobalHotKeys(self._hotkey_map)
            self._listener.start()
        except Exception as exc:
            print(f"[hotkeys] Failed to start listener: {exc}")

    def stop(self) -> None:
        if self._listener is not None:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None
