"""
app.py -- Application entry point for the Study Companion.

Run with:
    python src/app.py
"""

from __future__ import annotations

import sys
import os
import traceback
import tkinter as tk
from tkinter import messagebox

# Ensure src/ is on sys.path so sibling modules resolve correctly
_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

import config
import screen as screen_module
from memory import Memory
from ai import AIClient
from pet.pet import Pet
from ui.window import ChatWindow
from hotkeys import HotkeyManager


class App:
    """Top-level application controller."""

    def __init__(self):
        # ----------------------------------------------------------------
        # 1. Create the ONE tkinter root first (hidden).
        #    All messageboxes and Toplevels must come after this.
        # ----------------------------------------------------------------
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title("Study Companion")

        # ----------------------------------------------------------------
        # 2. Validate API key
        # ----------------------------------------------------------------
        if not config.GEMINI_API_KEY:
            messagebox.showerror(
                "Missing API Key",
                "GEMINI_API_KEY is not set in your .env file.\n\n"
                "Add the following line to .env:\n"
                "GEMINI_API_KEY=<your-gemini-api-key>",
            )
            self.root.destroy()
            sys.exit(1)

        # ----------------------------------------------------------------
        # 3. Core components
        # ----------------------------------------------------------------
        self.memory = Memory()

        try:
            self.ai_client = AIClient(
                api_key=config.GEMINI_API_KEY,
                model=config.GEMINI_MODEL,
            )
        except ValueError as exc:
            messagebox.showerror("AI Init Error", str(exc))
            self.root.destroy()
            sys.exit(1)

        # ----------------------------------------------------------------
        # 4. Pet
        # ----------------------------------------------------------------
        self.pet = Pet(
            self.root,
            on_click_callback=self._open_chat,
            on_quit_callback=self._quit,
            on_explain_callback=self._explain_screen,
        )

        # ----------------------------------------------------------------
        # 5. Chat window
        # ----------------------------------------------------------------
        self.chat_window = ChatWindow(
            root=self.root,
            memory=self.memory,
            ai_client=self.ai_client,
            on_retake=self._retake_screenshot,
            on_pet_state=self._set_pet_state,
        )

        # ----------------------------------------------------------------
        # 6. Global hotkeys
        #    Ctrl+Alt+S  — capture + open chat
        #    Ctrl+Alt+E  — capture + auto-explain (one-shot, no typing needed)
        # ----------------------------------------------------------------
        self.hotkey_manager = HotkeyManager()
        self.hotkey_manager.register(
            config.HOTKEY_MODIFIERS,
            config.HOTKEY_KEY,
            self._hotkey_capture,
        )
        self.hotkey_manager.register(
            config.EXPLAIN_HOTKEY_MODIFIERS,
            config.EXPLAIN_HOTKEY_KEY,
            self._hotkey_explain,
        )
        try:
            self.hotkey_manager.start()
        except Exception as exc:
            print(f"[app] Hotkey registration failed: {exc}")

        # ----------------------------------------------------------------
        # 7. Clean exit hook
        # ----------------------------------------------------------------
        self.root.protocol("WM_DELETE_WINDOW", self._quit)

        print(
            "[app] Study Companion started.\n"
            f"      Model : {config.GEMINI_MODEL}\n"
            f"      Scale : {config.PET_SCALE}x\n"
            "      Ctrl+Alt+S — Capture screen & open chat\n"
            "      Ctrl+Alt+E — Capture screen & auto-explain\n"
            "      Right-click the dog for the menu."
        )

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _hotkey_capture(self) -> None:
        """Ctrl+Alt+S: capture screen then open chat."""
        self.root.after(0, self._capture_and_open)

    def _hotkey_explain(self) -> None:
        """Ctrl+Alt+E: capture screen then auto-explain."""
        self.root.after(0, self._explain_screen)

    def _capture_and_open(self) -> None:
        """Capture screenshot (replace mode), store it, open chat window."""
        try:
            img = screen_module.capture_primary()
            self.memory.set_screenshot(img)
            self._set_pet_state("THINKING")
        except Exception as exc:
            print(f"[app] Screenshot error: {exc}")
            self._set_pet_state("CONFUSED")
            messagebox.showerror("Screenshot Error", str(exc))
            return

        self.chat_window.show()
        self.chat_window.notify_screenshot()
        self._set_pet_state("HAPPY")

    def _explain_screen(self) -> None:
        """Capture screen and immediately auto-explain — no typing needed."""
        try:
            img = screen_module.capture_primary()
            self.memory.set_screenshot(img)
            self._set_pet_state("THINKING")
        except Exception as exc:
            print(f"[app] Screenshot error: {exc}")
            self._set_pet_state("CONFUSED")
            messagebox.showerror("Screenshot Error", str(exc))
            return

        self.chat_window.auto_ask(config.EXPLAIN_PROMPT)


    def _retake_screenshot(self, add_only: bool = False) -> None:
        """Capture a screenshot.  add_only=True appends; False replaces."""
        try:
            img = screen_module.capture_primary()
            if add_only:
                self.memory.add_screenshot(img)
                self.chat_window.notify_screenshot_added()
            else:
                self.memory.set_screenshot(img)
                self.chat_window.notify_screenshot()
            self._set_pet_state("HAPPY")
        except Exception as exc:
            print(f"[app] Screenshot error: {exc}")
            self._set_pet_state("CONFUSED")
            messagebox.showerror("Screenshot Error", str(exc))

    def _open_chat(self) -> None:
        """Called when the user left-clicks the pet dog."""
        self.chat_window.show()

    def _set_pet_state(self, state: str) -> None:
        """Update pet animation state. Transient states auto-revert to IDLE."""
        self.memory.set_pet_state(state)
        self.pet.set_state(state)

        # Cancel any pending revert
        if hasattr(self, "_idle_after_id") and self._idle_after_id:
            try:
                self.root.after_cancel(self._idle_after_id)
            except Exception:
                pass
            self._idle_after_id = None

        # HAPPY and CONFUSED are transient: return to IDLE after 3 s
        if state in ("HAPPY", "CONFUSED"):
            self._idle_after_id = self.root.after(3000, self._revert_to_idle)

    def _revert_to_idle(self) -> None:
        self._idle_after_id = None
        self.memory.set_pet_state("IDLE")
        self.pet.set_state("IDLE")

    # ------------------------------------------------------------------
    # Run / quit
    # ------------------------------------------------------------------

    def run(self) -> None:
        try:
            self.root.mainloop()
        finally:
            self._quit()

    def _quit(self) -> None:
        print("[app] Shutting down...")
        self.hotkey_manager.stop()
        try:
            self.root.destroy()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        app = App()
        app.run()
    except Exception:
        # Last-resort: print traceback so we can see it even without a terminal
        err = traceback.format_exc()
        print(err, file=sys.stderr)
        # Try to show it in a messagebox too
        try:
            _r = tk.Tk()
            _r.withdraw()
            messagebox.showerror("Study Companion crashed", err[:800])
            _r.destroy()
        except Exception:
            pass
        sys.exit(1)
