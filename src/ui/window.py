"""
window.py -- Study Companion chat window with History Drawer, Text Zoom, Thumbnail Cross Buttons, & Interrupt Thinking.

Colour scheme: warm cream / ivory inspired by the pixel-art pet sprite.
"""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk

import config
import db
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
RED_SOFT    = "#c4736a"   # dusty rose   — danger / stop / clear
YELLOW      = "#e8b84e"   # warm gold
FG          = "#3d2b1f"   # dark cocoa   — primary text
FG2         = "#7a6555"   # warm brown   — secondary text
FG3         = "#b09a88"   # muted tan    — metadata / placeholders

FONT_TITLE  = ("Segoe UI", 12, "bold")
FONT_SUB    = ("Segoe UI", 8)
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
        self._interrupted = False

        self._send_btn: tk.Button | None = None
        self._thumb_widgets: list[tk.Frame] = []
        self._thumb_imgs: list[ImageTk.PhotoImage] = []
        self._thumb_strip: tk.Frame | None = None
        self._ss_canvas: tk.Canvas | None = None

        self._history_panel: tk.Frame | None = None
        self._history_visible = False
        self._history_sessions: list[dict] = []

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
        win.geometry("500x640")
        win.minsize(420, 560)
        win.resizable(True, True)
        win.attributes("-topmost", True)
        win.protocol("WM_DELETE_WINDOW", self.hide)

        # ================================================================
        # 1. HEADER (DOCKS TOP)
        # ================================================================
        header = tk.Frame(win, bg=BG2, pady=6)
        header.pack(side="top", fill="x")
        tk.Frame(win, bg=BORDER, height=1).pack(side="top", fill="x")

        row = tk.Frame(header, bg=BG2)
        row.pack(fill="x", padx=10)

        tk.Label(row, text="🐾", bg=BG2, fg=FG, font=("Segoe UI", 18)).pack(side="left")

        col = tk.Frame(row, bg=BG2)
        col.pack(side="left", padx=(6, 0))
        tk.Label(col, text="Study Buddy", bg=BG2, fg=FG, font=FONT_TITLE).pack(anchor="w")
        tk.Label(col, text="Your study companion ✨", bg=BG2, fg=FG2, font=FONT_SUB).pack(anchor="w")

        # Right side header buttons
        tk.Button(
            row, text="✕", command=self.hide,
            bg=BG2, fg=FG3, activebackground=BG3, activeforeground=RED_SOFT,
            relief="flat", cursor="hand2", font=("Segoe UI", 11),
        ).pack(side="right", padx=(4, 0))

        # Text Zoom buttons (A- / A+)
        _btn(row, "A+", lambda: self._chat.zoom_in() if self._chat else None,
             BG3, fg=FG, padx=6, pady=1).pack(side="right", padx=(2, 0))
        _btn(row, "A-", lambda: self._chat.zoom_out() if self._chat else None,
             BG3, fg=FG, padx=6, pady=1).pack(side="right", padx=(4, 0))

        # New Chat button
        _btn(row, "➕ New", self._start_new_chat,
             ACCENT, fg="#fdf8f0", padx=7, pady=1).pack(side="right", padx=(4, 0))

        # History drawer toggle button
        _btn(row, "📜 History", self._toggle_history_panel,
             ACCENT2, fg="#fdf8f0", padx=7, pady=1).pack(side="right", padx=(4, 0))

        # Sub-row for model badge
        row2 = tk.Frame(header, bg=BG2)
        row2.pack(fill="x", padx=10, pady=(2, 0))
        tk.Label(
            row2, textvariable=self._model_var,
            bg=BG3, fg=ACCENT2, font=FONT_BADGE, padx=6, pady=1,
        ).pack(side="right")
        tk.Label(row2, text="via ", bg=BG2, fg=FG3, font=FONT_BADGE).pack(side="right")

        # ================================================================
        # 2. BOTTOM PANELS (STATUS BAR + INPUT ENTRY - DOCKS BOTTOM FIRST!)
        # ================================================================
        status_bar = tk.Frame(win, bg=BG2)
        status_bar.pack(side="bottom", fill="x")

        tk.Label(status_bar, textvariable=self._status_var,
                 bg=BG2, fg=FG3, font=FONT_STATUS, anchor="w",
                 ).pack(side="left", padx=10, pady=(0, 4))

        tk.Label(status_bar, textvariable=self._ss_count_var,
                 bg=BG2, fg=ACCENT2, font=FONT_STATUS, anchor="e",
                 ).pack(side="right", padx=10, pady=(0, 4))

        tk.Frame(win, bg=BORDER, height=1).pack(side="bottom", fill="x")

        input_panel = tk.Frame(win, bg=BG2, pady=8)
        input_panel.pack(side="bottom", fill="x")

        input_row = tk.Frame(input_panel, bg=BG2)
        input_row.pack(fill="x", padx=10)

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
        self._input_entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 6))
        self._input_entry.bind("<Return>", lambda _e: self._on_action_btn_click())

        # Dynamic Send / Stop Button
        self._send_btn = tk.Button(
            input_row, text="Send ➤", command=self._on_action_btn_click,
            bg=GREEN, fg="#fdf8f0", activebackground=_lighten(GREEN), activeforeground="#fdf8f0",
            relief="flat", cursor="hand2", font=FONT_BTN, padx=14, pady=5,
        )
        self._send_btn.pack(side="left")

        # ================================================================
        # 3. SCREENSHOT PANEL (DOCKS TOP BELOW HEADER)
        # ================================================================
        ss_panel = tk.Frame(win, bg=BG, pady=4)
        ss_panel.pack(side="top", fill="x", padx=10)

        # Top row: label + buttons
        ss_top = tk.Frame(ss_panel, bg=BG)
        ss_top.pack(fill="x", pady=(0, 4))

        tk.Label(ss_top, text="📸  Screenshots", bg=BG, fg=FG2, font=FONT_BTN).pack(side="left")

        _btn(ss_top, "+ Add", self._add_screenshot,
             ACCENT2, fg="#fdf8f0", padx=8, pady=1).pack(side="right", padx=(3, 0))
        _btn(ss_top, "↺ Retake", self._retake,
             BG3, fg=FG, padx=8, pady=1).pack(side="right", padx=(3, 0))
        _btn(ss_top, "✕ Clear All", self._clear_screenshots,
             RED_SOFT, fg="#fdf8f0", padx=8, pady=1).pack(side="right")

        # Scrollable horizontal thumbnail strip
        strip_wrap = tk.Frame(ss_panel, bg=BG4, relief="flat")
        strip_wrap.pack(fill="x")

        ss_canvas = tk.Canvas(strip_wrap, bg=BG4, highlightthickness=0, height=THUMB_H + 32)
        ss_canvas.pack(side="top", fill="x", expand=True)

        ss_hbar = ttk.Scrollbar(strip_wrap, orient="horizontal", command=ss_canvas.xview)
        ss_hbar.pack(side="bottom", fill="x")
        ss_canvas.configure(xscrollcommand=ss_hbar.set)

        self._thumb_strip = tk.Frame(ss_canvas, bg=BG4)
        _id = ss_canvas.create_window((0, 0), window=self._thumb_strip, anchor="nw")
        self._thumb_strip.bind(
            "<Configure>",
            lambda e: ss_canvas.configure(scrollregion=ss_canvas.bbox("all")),
        )
        self._ss_canvas = ss_canvas

        tk.Frame(win, bg=BORDER, height=1).pack(side="top", fill="x", pady=(4, 0))

        # ================================================================
        # 4. MAIN CHAT CONTENT AREA (EXPANDS TO FILL REMAINING MIDDLE SPACE)
        # ================================================================
        content_container = tk.Frame(win, bg=BG)
        content_container.pack(side="top", fill="both", expand=True)

        # Chat display widget
        self._chat = ChatDisplay(content_container)
        self._chat.pack(fill="both", expand=True)

        # Load existing messages if session has history, else system welcome
        msgs = self._memory.get_history()
        if msgs:
            for m in msgs:
                if m["role"] == "user":
                    self._chat.append_user(m["text"])
                else:
                    self._chat.append_ai(m["text"])
        else:
            self._chat.append_system(
                "👋  Hi! I'm Buddy. Press Ctrl+Alt+S to capture your screen "
                "or Ctrl+Alt+E to explain it instantly!"
            )

        # History panel container (hidden overlay)
        self._history_panel = tk.Frame(content_container, bg=BG2, highlightthickness=1, highlightbackground=BORDER)

        self._input_entry.focus_set()

    # ------------------------------------------------------------------
    # History Drawer Panel
    # ------------------------------------------------------------------

    def _toggle_history_panel(self) -> None:
        if self._history_panel is None:
            return
        if self._history_visible:
            self._history_panel.place_forget()
            self._history_visible = False
        else:
            self._render_history_panel()
            self._history_panel.place(x=0, y=0, relwidth=1.0, relheight=1.0)
            self._history_panel.lift()
            self._history_visible = True

    def _render_history_panel(self) -> None:
        if self._history_panel is None:
            return
        for w in self._history_panel.winfo_children():
            w.destroy()

        # Header of history panel
        head = tk.Frame(self._history_panel, bg=BG3, pady=8, padx=12)
        head.pack(fill="x")

        tk.Label(head, text="📜 Chat History", bg=BG3, fg=FG, font=FONT_TITLE).pack(side="left")

        tk.Button(
            head, text="✕ Close", command=self._toggle_history_panel,
            bg=BG3, fg=RED_SOFT, activebackground=BG4, activeforeground=RED_SOFT,
            relief="flat", cursor="hand2", font=FONT_BTN,
        ).pack(side="right")

        # Session Listbox + Scrollbar
        list_frame = tk.Frame(self._history_panel, bg=BG2, padx=10, pady=10)
        list_frame.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        lb = tk.Listbox(
            list_frame,
            bg=BG, fg=FG,
            selectbackground=ACCENT, selectforeground="#fdf8f0",
            font=("Segoe UI", 10),
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER,
            yscrollcommand=scrollbar.set,
            activestyle="none",
        )
        lb.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=lb.yview)

        sessions = db.get_all_sessions()
        self._history_sessions = sessions

        if not sessions:
            lb.insert(tk.END, "  No saved chat sessions yet")
        else:
            for s in sessions:
                lb.insert(tk.END, f"  💬 {s['title']} ({s['updated_at']})")

        # Buttons footer in history drawer
        btn_bar = tk.Frame(self._history_panel, bg=BG3, pady=8, padx=12)
        btn_bar.pack(fill="x")

        _btn(btn_bar, "Load Selected", lambda: self._on_load_selected_session(lb),
             GREEN, fg="#fdf8f0", padx=12, pady=4).pack(side="left")

        _btn(btn_bar, "Delete Selected", lambda: self._on_delete_selected_session(lb),
             RED_SOFT, fg="#fdf8f0", padx=12, pady=4).pack(side="right")

    def _on_load_selected_session(self, lb: tk.Listbox) -> None:
        sel = lb.curselection()
        if not sel or not self._history_sessions:
            return
        idx = sel[0]
        if idx < len(self._history_sessions):
            session_id = self._history_sessions[idx]["id"]
            self._switch_to_session(session_id)

    def _on_delete_selected_session(self, lb: tk.Listbox) -> None:
        sel = lb.curselection()
        if not sel or not self._history_sessions:
            return
        idx = sel[0]
        if idx < len(self._history_sessions):
            session_id = self._history_sessions[idx]["id"]
            db.delete_session(session_id)
            if session_id == self._memory.get_current_session_id():
                self._start_new_chat()
            self._render_history_panel()

    def _switch_to_session(self, session_id: str) -> None:
        msgs = self._memory.load_session(session_id)
        if self._chat:
            self._chat.clear()
            if msgs:
                for m in msgs:
                    if m["role"] == "user":
                        self._chat.append_user(m["text"])
                    else:
                        self._chat.append_ai(m["text"])
            else:
                self._chat.append_system("Empty chat session.")
        self._refresh_thumb_strip()
        self._toggle_history_panel()

    def _start_new_chat(self) -> None:
        self._memory.start_new_session()
        if self._chat:
            self._chat.clear()
            self._chat.append_system("Started a new chat session! Press Ctrl+Alt+S to capture screen.")
        self._refresh_thumb_strip()
        if self._history_visible and self._history_panel:
            self._render_history_panel()

    # ------------------------------------------------------------------
    # Screenshot strip (with explicit '✕' cross buttons)
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
                bg=BG4, fg=FG3, font=FONT_STATUS, padx=16, pady=16,
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
                        padx=4, pady=3, relief="flat",
                        highlightthickness=1, highlightbackground=BORDER)
        card.pack(side="left", padx=4, pady=4)

        # Top row: label (#1, #2) on left, explicit '✕' cross button on right
        top_row = tk.Frame(card, bg=BG3)
        top_row.pack(fill="x", pady=(0, 2))

        tk.Label(top_row, text=f"#{idx + 1}", bg=BG3, fg=ACCENT,
                 font=FONT_BADGE).pack(side="left")

        i = idx
        btn_x = tk.Button(
            top_row, text="✕",
            command=lambda: self._remove_screenshot(i),
            bg=BG3, fg=RED_SOFT, activebackground=BG4, activeforeground=RED_SOFT,
            relief="flat", cursor="hand2", font=("Segoe UI", 9, "bold"),
            padx=2, pady=0,
        )
        btn_x.pack(side="right")

        # Thumbnail image below top row
        tk.Label(card, image=tk_img, bg=BG3, cursor="hand2").pack()

        self._thumb_widgets.append(card)

    def _remove_screenshot(self, idx: int) -> None:
        self._memory.remove_screenshot(idx)
        self._refresh_thumb_strip()

    def _update_ss_count(self) -> None:
        n = self._memory.screenshot_count()
        if n == 0:
            self._ss_count_var.set("")
        else:
            self._ss_count_var.set(
                f"{n} screenshot{'s' if n > 1 else ''} in context"
            )

    # ------------------------------------------------------------------
    # Actions & Generation Control
    # ------------------------------------------------------------------

    def _add_screenshot(self) -> None:
        self._on_retake(add_only=True)
        self._refresh_thumb_strip()

    def _retake(self) -> None:
        self._on_retake(add_only=False)
        self._refresh_thumb_strip()

    def _clear_screenshots(self) -> None:
        self._memory._screenshots.clear()
        if self._chat:
            self._chat.append_system("Screenshots cleared for current session.")
        self._refresh_thumb_strip()

    def _on_action_btn_click(self) -> None:
        """Handle click on the dynamic Send / Stop button."""
        if self._sending:
            self._interrupt_thinking()
        else:
            self._send()

    def _interrupt_thinking(self) -> None:
        """Interrupt active AI generation."""
        if not self._sending:
            return
        self._interrupted = True
        self._sending = False
        if self._send_btn:
            self._send_btn.config(text="Send ➤", bg=GREEN, activebackground=_lighten(GREEN))
        self._set_status("Generation stopped")
        self._on_pet_state("IDLE")
        if self._chat:
            self._chat.append_system("⏹  AI generation stopped.")

    def _send(self) -> None:
        if self._sending:
            return
        question = self._input_var.get().strip()
        if not question:
            return

        self._input_var.set("")
        if self._chat:
            self._chat.append_user(question)

        # Add message to memory & DB FIRST
        self._memory.add_message("user", question)
        history_snapshot = self._memory.get_history()[:-1]
        screenshots_snapshot = self._memory.get_screenshots()

        self._set_status("Buddy is thinking...")
        self._on_pet_state("THINKING")
        self._sending = True
        self._interrupted = False

        if self._send_btn:
            self._send_btn.config(text="⏹ Stop", bg=RED_SOFT, activebackground=_lighten(RED_SOFT))

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
        if self._interrupted:
            return
        self._memory.add_message("model", reply)
        if self._chat:
            self._chat.append_ai(reply)
        self._model_var.set(model_used)
        self._set_status("Ready")
        self._on_pet_state("HAPPY")
        self._sending = False
        if self._send_btn:
            self._send_btn.config(text="Send ➤", bg=GREEN, activebackground=_lighten(GREEN))

    def _on_ai_error(self, error: str) -> None:
        if self._interrupted:
            return
        print(f"[window] AI error: {error}")
        if self._chat:
            self._chat.append_system(f"⚠  {error[:300]}")
        self._set_status("Error — try again")
        self._on_pet_state("CONFUSED")
        self._sending = False
        if self._send_btn:
            self._send_btn.config(text="Send ➤", bg=GREEN, activebackground=_lighten(GREEN))

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
        self._interrupted = False
        if self._send_btn:
            self._send_btn.config(text="⏹ Stop", bg=RED_SOFT, activebackground=_lighten(RED_SOFT))
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
