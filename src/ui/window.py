"""
window.py -- Study Companion chat window.

Colour scheme: warm cream / ivory inspired by the pixel-art pet sprite
  (cream body  →  #fdf8f0 backgrounds
   warm gold   →  #c8855a / #b87333 accents
   soft purple →  #9b8ec4 lavender highlights)
"""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk

import config
from ui.chat import ChatDisplay

# ---------------------------------------------------------------------------
# Pet-inspired palette
# ---------------------------------------------------------------------------
BG          = "#fdf8f0"   # warm ivory   — window background
BG2         = "#f5ede0"   # soft cream   — header / footer panels
BG3         = "#ede0cb"   # warm tan     — cards / input field
BG4         = "#e8d9c0"   # toasted parchment — thumb strip
BORDER      = "#d4bfa0"   # warm border hairline
ACCENT      = "#c8855a"   # amber-rust   — primary accent (pet warm tones)
ACCENT2     = "#9b8ec4"   # soft lavender — secondary accent (pet purple)
GREEN       = "#7aab8a"   # sage green   — send button
RED_SOFT    = "#c4736a"   # dusty rose   — danger / clear
YELLOW      = "#e8b84e"   # warm gold
FG          = "#3d2b1f"   # dark cocoa   — primary text
FG2         = "#7a6555"   # warm brown   — secondary text
FG3         = "#b09a88"   # muted tan    — metadata / placeholders

FONT_TITLE  = ("Segoe UI", 13, "bold")
FONT_SUB    = ("Segoe UI", 9)
FONT_BTN    = ("Segoe UI", 9, "bold")
FONT_BADGE  = ("Segoe UI", 8)
FONT_INPUT  = ("Segoe UI", 10)
FONT_STATUS = ("Segoe UI", 8)

THUMB_W = 100
THUMB_H = 60


def _btn(parent, text, cmd, bg, fg=BG, **kw):
    """Helper: styled flat button with hover tint."""
    b = tk.Button(
        parent, text=text, command=cmd,
        bg=bg, fg=fg, activebackground=_lighten(bg), activeforeground=fg,
        relief="flat", cursor="hand2", font=FONT_BTN, **kw,
    )
    b.bind("<Enter>", lambda e: b.config(bg=_lighten(bg)))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    return b


def _lighten(hex_color: str) -> str:
    try:
        r = min(255, int(hex_color[1:3], 16) + 18)
        g = min(255, int(hex_color[3:5], 16) + 18)
        b = min(255, int(hex_color[5:7], 16) + 18)
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return hex_color


class ChatWindow:
    """The main study chat window."""

    def __init__(self, root, memory, ai_client, on_retake, on_pet_state):
        self._root = root
        self._memory = memory
        self._ai_client = ai_client
        self._on_retake = on_retake
        self._on_pet_state = on_pet_state

        self._window: tk.Toplevel | None = None
        self._chat: ChatDisplay | None = None
        self._input_var = tk.StringVar()
        self._status_var = tk.StringVar(value="Ready")
        self._model_var = tk.StringVar(value=config.GEMINI_MODEL)
        self._ss_count_var = tk.StringVar(value="")
        self._sending = False

        self._thumb_widgets: list[tk.Frame] = []
        self._thumb_imgs: list[ImageTk.PhotoImage] = []
        self._thumb_strip: tk.Frame | None = None
        self._ss_canvas: tk.Canvas | None = None

    # ------------------------------------------------------------------
    # Show / hide
    # ------------------------------------------------------------------

    def show(self) -> None:
        if self._window is None or not self._window.winfo_exists():
            self._build()
        else:
            self._window.deiconify()
            self._window.lift()
        self._refresh_thumb_strip()

    def hide(self) -> None:
        if self._window and self._window.winfo_exists():
            self._window.withdraw()

    def is_visible(self) -> bool:
        return (
            self._window is not None
            and self._window.winfo_exists()
            and self._window.state() != "withdrawn"
        )

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _build(self) -> None:
        win = tk.Toplevel(self._root)
        self._window = win
        win.title("Study Buddy")
        win.configure(bg=BG)
        win.geometry(f"{config.CHAT_WINDOW_WIDTH}x{config.CHAT_WINDOW_HEIGHT}")
        win.minsize(400, 520)
        win.resizable(True, True)
        win.attributes("-topmost", True)
        win.protocol("WM_DELETE_WINDOW", self.hide)

        # ================================================================
        # HEADER  — warm cream panel
        # ================================================================
        header = tk.Frame(win, bg=BG2, pady=10)
        header.pack(fill="x")
        tk.Frame(win, bg=BORDER, height=1).pack(fill="x")

        row = tk.Frame(header, bg=BG2)
        row.pack(fill="x", padx=14)

        tk.Label(row, text="🐾", bg=BG2, fg=FG,
                 font=("Segoe UI", 22)).pack(side="left")

        col = tk.Frame(row, bg=BG2)
        col.pack(side="left", padx=(8, 0))
        tk.Label(col, text="Study Buddy", bg=BG2, fg=FG,
                 font=FONT_TITLE).pack(anchor="w")
        tk.Label(col, text="Your pixel-art study companion ✨",
                 bg=BG2, fg=FG2, font=FONT_SUB).pack(anchor="w")

        # Close
        tk.Button(
            row, text="✕", command=self.hide,
            bg=BG2, fg=FG3, activebackground=BG3, activeforeground=RED_SOFT,
            relief="flat", cursor="hand2", font=("Segoe UI", 13),
        ).pack(side="right")

        # Model badge
        tk.Label(
            row, textvariable=self._model_var,
            bg=BG3, fg=ACCENT2, font=FONT_BADGE, padx=7, pady=2,
        ).pack(side="right", padx=(0, 10))
        tk.Label(row, text="via", bg=BG2, fg=FG3,
                 font=FONT_BADGE).pack(side="right")

        # ================================================================
        # SCREENSHOT PANEL
        # ================================================================
        ss_panel = tk.Frame(win, bg=BG, pady=6)
        ss_panel.pack(fill="x", padx=12)

        # Top row: label + buttons
        ss_top = tk.Frame(ss_panel, bg=BG)
        ss_top.pack(fill="x", pady=(0, 5))

        tk.Label(ss_top, text="📸  Screenshots", bg=BG, fg=FG2,
                 font=FONT_BTN).pack(side="left")

        _btn(ss_top, "+ Add", self._add_screenshot,
             ACCENT2, fg="#fdf8f0", padx=10, pady=2).pack(side="right", padx=(3, 0))
        _btn(ss_top, "↺ Retake", self._retake,
             BG3, fg=FG, padx=10, pady=2).pack(side="right", padx=(3, 0))
        _btn(ss_top, "✕ Clear All", self._clear_context,
             RED_SOFT, fg="#fdf8f0", padx=10, pady=2).pack(side="right")

        # Scrollable horizontal thumbnail strip
        strip_wrap = tk.Frame(ss_panel, bg=BG4, relief="flat")
        strip_wrap.pack(fill="x")

        ss_canvas = tk.Canvas(strip_wrap, bg=BG4, highlightthickness=0,
                              height=THUMB_H + 32)
        ss_canvas.pack(side="top", fill="x", expand=True)

        ss_hbar = ttk.Scrollbar(strip_wrap, orient="horizontal",
                                command=ss_canvas.xview)
        ss_hbar.pack(side="bottom", fill="x")
        ss_canvas.configure(xscrollcommand=ss_hbar.set)

        self._thumb_strip = tk.Frame(ss_canvas, bg=BG4)
        _id = ss_canvas.create_window((0, 0), window=self._thumb_strip, anchor="nw")
        self._thumb_strip.bind(
            "<Configure>",
            lambda e: ss_canvas.configure(scrollregion=ss_canvas.bbox("all")),
        )
        self._ss_canvas = ss_canvas

        # ================================================================
        # DIVIDER
        # ================================================================
        tk.Frame(win, bg=BORDER, height=1).pack(fill="x", pady=(6, 0))

        # ================================================================
        # CHAT AREA
        # ================================================================
        self._chat = ChatDisplay(win)
        self._chat.pack(fill="both", expand=True)
        self._chat.append_system(
            "👋  Hi! I'm Buddy. Press Ctrl+Alt+S to capture your screen "
            "then ask me anything about what you're studying!"
        )

        # ================================================================
        # INPUT AREA
        # ================================================================
        tk.Frame(win, bg=BORDER, height=1).pack(fill="x")

        input_panel = tk.Frame(win, bg=BG2, pady=8)
        input_panel.pack(fill="x")

        input_row = tk.Frame(input_panel, bg=BG2)
        input_row.pack(fill="x", padx=12)

        self._input_entry = tk.Entry(
            input_row,
            textvariable=self._input_var,
            bg=BG3, fg=FG,
            insertbackground=ACCENT,
            relief="flat", font=FONT_INPUT,
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=ACCENT,
        )
        self._input_entry.pack(side="left", fill="x", expand=True,
                               ipady=8, padx=(0, 8))
        self._input_entry.bind("<Return>", lambda _e: self._send())

        _btn(input_row, "Send ➤", self._send,
             GREEN, fg="#fdf8f0", padx=16, pady=6).pack(side="left")

        # ================================================================
        # STATUS BAR
        # ================================================================
        status_bar = tk.Frame(win, bg=BG2)
        status_bar.pack(fill="x")

        tk.Label(status_bar, textvariable=self._status_var,
                 bg=BG2, fg=FG3, font=FONT_STATUS, anchor="w",
                 ).pack(side="left", padx=12, pady=(0, 5))

        tk.Label(status_bar, textvariable=self._ss_count_var,
                 bg=BG2, fg=ACCENT2, font=FONT_STATUS, anchor="e",
                 ).pack(side="right", padx=12, pady=(0, 5))

        self._input_entry.focus_set()

    # ------------------------------------------------------------------
    # Screenshot strip
    # ------------------------------------------------------------------

    def _refresh_thumb_strip(self) -> None:
        if self._thumb_strip is None:
            return
        for w in self._thumb_strip.winfo_children():
            w.destroy()
        self._thumb_imgs.clear()
        self._thumb_widgets.clear()

        shots = self._memory.get_screenshots()
        if not shots:
            tk.Label(
                self._thumb_strip,
                text="No screenshots yet — press Ctrl+Alt+S to capture",
                bg=BG4, fg=FG3, font=FONT_STATUS, padx=16, pady=22,
            ).pack(side="left")
        else:
            for idx, img in enumerate(shots):
                self._add_thumb_widget(idx, img)

        self._update_ss_count()

    def _add_thumb_widget(self, idx: int, img: Image.Image) -> None:
        thumb = img.copy()
        thumb.thumbnail((THUMB_W, THUMB_H), Image.LANCZOS)
        tk_img = ImageTk.PhotoImage(thumb)
        self._thumb_imgs.append(tk_img)

        card = tk.Frame(self._thumb_strip, bg=BG3,
                        padx=3, pady=3, relief="flat",
                        highlightthickness=1, highlightbackground=BORDER)
        card.pack(side="left", padx=5, pady=5)

        tk.Label(card, text=f"#{idx + 1}", bg=BG3, fg=ACCENT,
                 font=FONT_BADGE).pack(anchor="nw")

        tk.Label(card, image=tk_img, bg=BG3, cursor="hand2").pack()

        i = idx
        tk.Button(
            card, text="✕ remove",
            command=lambda: self._remove_screenshot(i),
            bg=BG3, fg=RED_SOFT, relief="flat", cursor="hand2",
            font=("Segoe UI", 7),
        ).pack(fill="x")

        self._thumb_widgets.append(card)

    def _remove_screenshot(self, idx: int) -> None:
        self._memory.remove_screenshot(idx)
        self._refresh_thumb_strip()
        if not self._memory.has_screenshot() and self._chat:
            self._chat.append_system(
                "Screenshot removed. Context now has no screenshots."
            )

    def _update_ss_count(self) -> None:
        n = self._memory.screenshot_count()
        if n == 0:
            self._ss_count_var.set("")
        else:
            self._ss_count_var.set(
                f"{n} screenshot{'s' if n > 1 else ''} in context"
            )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _add_screenshot(self) -> None:
        self._on_retake(add_only=True)
        self._refresh_thumb_strip()

    def _retake(self) -> None:
        self._on_retake(add_only=False)
        self._refresh_thumb_strip()

    def _clear_context(self) -> None:
        self._memory.clear_context()
        if self._chat:
            self._chat.clear()
            self._chat.append_system(
                "Context cleared. Press Ctrl+Alt+S to start fresh."
            )
        self._refresh_thumb_strip()
        self._on_pet_state("IDLE")

    def _send(self) -> None:
        if self._sending:
            return
        question = self._input_var.get().strip()
        if not question:
            return
        if not self._memory.has_screenshot():
            messagebox.showinfo(
                "No Screenshot",
                "Capture a screenshot first (Ctrl+Alt+S) or use + Add.",
            )
            return

        self._input_var.set("")
        self._chat.append_user(question)

        # Add to memory FIRST, then snapshot history WITHOUT the just-added msg
        # (the current question is sent separately as the new user turn to Gemini)
        self._memory.add_message("user", question)
        history_snapshot = self._memory.get_history()[:-1]  # all previous turns
        screenshots_snapshot = self._memory.get_screenshots()

        self._set_status("Buddy is thinking...")
        self._on_pet_state("THINKING")
        self._sending = True

        threading.Thread(
            target=self._ask_ai,
            args=(question, screenshots_snapshot, history_snapshot),
            daemon=True,
        ).start()

    def _ask_ai(self, question, screenshots, history) -> None:
        try:
            reply, model_used = self._ai_client.ask(question, screenshots, history)
            self._root.after(0, self._on_ai_success, reply, model_used)
        except Exception as exc:
            self._root.after(0, self._on_ai_error, str(exc))

    def _on_ai_success(self, reply: str, model_used: str) -> None:
        self._memory.add_message("model", reply)
        if self._chat:
            self._chat.append_ai(reply)
        self._model_var.set(model_used)
        self._set_status("Ready")
        self._on_pet_state("HAPPY")
        self._sending = False

    def _on_ai_error(self, error: str) -> None:
        print(f"[window] AI error: {error}")
        if self._chat:
            self._chat.append_system(f"⚠  {error[:300]}")
        self._set_status("Error — try again")
        self._on_pet_state("CONFUSED")
        self._sending = False

    def auto_ask(self, question: str) -> None:
        """
        Programmatically send a question — used by 'Explain Screen'.
        Opens the window, shows the question, then fires the AI call.
        """
        self.show()
        if not self._memory.has_screenshot():
            if self._chat:
                self._chat.append_system(
                    "⚠  No screenshot in context. Capture one first (Ctrl+Alt+S)."
                )
            return
        if self._sending:
            return
        if self._chat:
            self._chat.append_user(question)
        self._memory.add_message("user", question)
        history_snapshot = self._memory.get_history()[:-1]
        screenshots_snapshot = self._memory.get_screenshots()
        self._set_status("Buddy is thinking...")
        self._on_pet_state("THINKING")
        self._sending = True
        threading.Thread(
            target=self._ask_ai,
            args=(question, screenshots_snapshot, history_snapshot),
            daemon=True,
        ).start()

    def notify_screenshot(self) -> None:
        """Called after hotkey/retake (replace mode)."""
        if self._chat:
            self._chat.append_system("📸  Screenshot captured! Ask me anything.")
        self._refresh_thumb_strip()

    def notify_screenshot_added(self) -> None:
        """Called after + Add capture."""
        if self._chat:
            n = self._memory.screenshot_count()
            self._chat.append_system(f"📸  Screenshot #{n} added to context.")
        self._refresh_thumb_strip()

    def _set_status(self, msg: str) -> None:
        self._status_var.set(msg)
