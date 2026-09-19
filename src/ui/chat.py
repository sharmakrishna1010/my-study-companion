"""
chat.py -- Bulletproof Chat Display with Fluid Kinetic Physics Scrolling & Keyboard Navigation.

Colour palette: warm cream / ivory derived from the pixel-art pet sprite.
"""

from __future__ import annotations

import re
import tkinter as tk
from tkinter import ttk

# ---------------------------------------------------------------------------
# Palette  (pet-inspired: cream, warm gold, soft lavender)
# ---------------------------------------------------------------------------
BG_CHAT      = "#fdf8f0"   # warm ivory  — main chat background
BG_CODE      = "#ede0cb"   # toasted parchment — code blocks / inline code
FG_MAIN      = "#3d2b1f"   # dark cocoa  — primary text
FG_BOLD      = "#2a1a10"   # deepest brown for bold
FG_CODE      = "#7c5cbf"   # soft lavender-purple (pet accent)
FG_HEADING   = "#b87333"   # warm copper-gold (pet accent)
FG_LABEL     = "#8c603e"   # warm cocoa — sender names
FG_SYSTEM    = "#a08060"   # muted tan — system notices
FG_BULLET    = "#c8855a"   # amber rust — bullet markers
BORDER       = "#ddd0bb"   # hairline border


class ChatDisplay(tk.Frame):
    """Bulletproof scrollable chat display widget with kinetic scrolling & arrow key navigation."""

    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, bg=BG_CHAT, **kwargs)

        self._font_scale: float = 1.0
        self._scroll_velocity: float = 0.0
        self._scroll_job = None

        # Scrollbar
        self._scrollbar = ttk.Scrollbar(self, orient="vertical")
        self._scrollbar.pack(side="right", fill="y")

        # Main Text Widget
        self._txt = tk.Text(
            self,
            bg=BG_CHAT,
            fg=FG_MAIN,
            wrap="word",
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            yscrollcommand=self._scrollbar.set,
            padx=14,
            pady=10,
            cursor="arrow",
        )
        self._txt.pack(side="left", fill="both", expand=True)
        self._scrollbar.config(command=self._txt.yview)

        # Configure initial tags
        self._setup_tags()

        # Keyboard Zoom Shortcuts (Ctrl+Plus, Ctrl+Minus, Ctrl+0)
        parent.bind_all("<Control-plus>", lambda e: self.zoom_in())
        parent.bind_all("<Control-equal>", lambda e: self.zoom_in())
        parent.bind_all("<Control-minus>", lambda e: self.zoom_out())
        parent.bind_all("<Control-0>", lambda e: self.reset_zoom())

        # Fluid Kinetic MouseWheel Scrolling
        self._txt.bind("<MouseWheel>", self._on_mousewheel)
        self.bind("<MouseWheel>", self._on_mousewheel)

        # Keyboard Arrow Key & Page Navigation (works even when text is disabled!)
        self._txt.bind("<Up>", lambda e: self._on_key_scroll(-2))
        self._txt.bind("<Down>", lambda e: self._on_key_scroll(2))
        self._txt.bind("<Prior>", lambda e: self._on_key_page(-1))  # PageUp
        self._txt.bind("<Next>", lambda e: self._on_key_page(1))    # PageDown
        self._txt.bind("<Home>", lambda e: self._on_key_home())
        self._txt.bind("<End>", lambda e: self._on_key_end())

        # Global Alt+Up / Alt+Down fallback
        parent.bind_all("<Alt-Up>", lambda e: self._on_key_scroll(-2))
        parent.bind_all("<Alt-Down>", lambda e: self._on_key_scroll(2))

    # ------------------------------------------------------------------
    # High-Precision MouseWheel & Trackpad Scrolling
    # ------------------------------------------------------------------

    def _on_mousewheel(self, event) -> str:
        """High-precision, instant, zero-deadzone mousewheel & trackpad scrolling."""
        raw_delta = event.delta
        if raw_delta == 0:
            return "break"

        # Scale step units proportionally: 1 line per 40 delta units (handles trackpads & notched wheels)
        if abs(raw_delta) >= 120:
            units = int(-2 * (raw_delta / 120.0))
        else:
            units = -1 if raw_delta > 0 else 1

        self._txt.yview_scroll(units, "units")
        return "break"

    # ------------------------------------------------------------------
    # Keyboard Navigation
    # ------------------------------------------------------------------

    def _on_key_scroll(self, units: int) -> str:
        self._txt.yview_scroll(units, "units")
        return "break"

    def _on_key_page(self, pages: int) -> str:
        self._txt.yview_scroll(pages, "pages")
        return "break"

    def _on_key_home(self) -> str:
        self._txt.yview_moveto(0.0)
        return "break"

    def _on_key_end(self) -> str:
        self._txt.yview_moveto(1.0)
        return "break"

    # ------------------------------------------------------------------
    # Tag Configuration & Dynamic Zooming
    # ------------------------------------------------------------------

    def _get_fonts(self) -> dict:
        s = self._font_scale
        return {
            "base":   ("Segoe UI", max(8, int(10 * s))),
            "bold":   ("Segoe UI", max(8, int(10 * s)), "bold"),
            "italic": ("Segoe UI", max(8, int(10 * s)), "italic"),
            "bi":     ("Segoe UI", max(8, int(10 * s)), "bold italic"),
            "code":   ("Consolas", max(8, int(9 * s))),
            "h1":     ("Segoe UI", max(11, int(14 * s)), "bold"),
            "h2":     ("Segoe UI", max(10, int(12 * s)), "bold"),
            "h3":     ("Segoe UI", max(9, int(11 * s)), "bold"),
            "label_user": ("Segoe UI", max(8, int(9 * s)), "bold"),
            "label_ai":   ("Segoe UI", max(8, int(9 * s)), "bold"),
            "system":     ("Segoe UI", max(8, int(9 * s)), "italic"),
        }

    def _setup_tags(self) -> None:
        f = self._get_fonts()
        t = self._txt

        t.tag_configure("user_header", font=f["label_user"], foreground=FG_LABEL, spacing1=10, spacing3=2)
        t.tag_configure("ai_header",   font=f["label_ai"],   foreground=FG_HEADING, spacing1=12, spacing3=2)
        t.tag_configure("system_msg",  font=f["system"],     foreground=FG_SYSTEM, justify="center", spacing1=8, spacing3=8)

        t.tag_configure("normal",      font=f["base"],   foreground=FG_MAIN, spacing1=1, spacing3=2)
        t.tag_configure("bold",        font=f["bold"],   foreground=FG_BOLD)
        t.tag_configure("italic",      font=f["italic"], foreground=FG_MAIN)
        t.tag_configure("bold_italic", font=f["bi"],     foreground=FG_BOLD)

        t.tag_configure("code_inline", font=f["code"],   foreground=FG_CODE, background=BG_CODE)
        t.tag_configure("code_block",  font=f["code"],   foreground=FG_CODE, background=BG_CODE,
                        lmargin1=14, lmargin2=14, spacing1=3, spacing3=3)

        t.tag_configure("h1", font=f["h1"], foreground=FG_HEADING, spacing1=8, spacing3=3)
        t.tag_configure("h2", font=f["h2"], foreground=FG_HEADING, spacing1=6, spacing3=2)
        t.tag_configure("h3", font=f["h3"], foreground=FG_HEADING, spacing1=4, spacing3=2)

        t.tag_configure("bullet",        font=f["base"], foreground=FG_MAIN, lmargin1=12, lmargin2=24)
        t.tag_configure("bullet_marker", font=f["bold"], foreground=FG_BULLET)
        t.tag_configure("numbered",      font=f["base"], foreground=FG_MAIN, lmargin1=12, lmargin2=28)

    def zoom_in(self) -> None:
        if self._font_scale < 2.0:
            self._font_scale = round(self._font_scale + 0.15, 2)
            self._setup_tags()

    def zoom_out(self) -> None:
        if self._font_scale > 0.7:
            self._font_scale = round(self._font_scale - 0.15, 2)
            self._setup_tags()

    def reset_zoom(self) -> None:
        self._font_scale = 1.0
        self._setup_tags()

    # ------------------------------------------------------------------
    # Public Append API
    # ------------------------------------------------------------------

    def append_user(self, text: str) -> None:
        self._txt.configure(state="normal")
        self._txt.insert(tk.END, "👤 You\n", "user_header")
        self._txt.insert(tk.END, text.strip() + "\n", "normal")
        self._txt.configure(state="disabled")
        self.scroll_to_bottom()

    def append_ai(self, text: str) -> None:
        self._txt.configure(state="normal")
        self._txt.insert(tk.END, "🐾 Buddy\n", "ai_header")
        self._render_markdown(text.strip())
        self._txt.insert(tk.END, "\n")
        self._txt.configure(state="disabled")
        self.scroll_to_bottom()

    def append_system(self, text: str) -> None:
        self._txt.configure(state="normal")
        self._txt.insert(tk.END, text.strip() + "\n", "system_msg")
        self._txt.configure(state="disabled")
        self.scroll_to_bottom()

    def clear(self) -> None:
        self._txt.configure(state="normal")
        self._txt.delete("1.0", tk.END)
        self._txt.configure(state="disabled")

    def scroll_to_bottom(self) -> None:
        self._txt.update_idletasks()
        self._txt.see(tk.END)
        self.after(50, lambda: self._txt.see(tk.END))

    # ------------------------------------------------------------------
    # Markdown Parser
    # ------------------------------------------------------------------

    def _render_markdown(self, text: str) -> None:
        lines = text.split("\n")
        in_code_block = False
        i = 0
        while i < len(lines):
            line = lines[i]

            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                i += 1
                continue

            if in_code_block:
                self._txt.insert(tk.END, line + "\n", "code_block")
                i += 1
                continue

            m_h3 = re.match(r"^###\s+(.*)", line)
            m_h2 = re.match(r"^##\s+(.*)",  line)
            m_h1 = re.match(r"^#\s+(.*)",   line)
            if m_h1:
                self._txt.insert(tk.END, m_h1.group(1) + "\n", "h1")
                i += 1
                continue
            if m_h2:
                self._txt.insert(tk.END, m_h2.group(1) + "\n", "h2")
                i += 1
                continue
            if m_h3:
                self._txt.insert(tk.END, m_h3.group(1) + "\n", "h3")
                i += 1
                continue

            bullet = re.match(r"^[\-\*\•]\s+(.*)", line)
            if bullet:
                self._txt.insert(tk.END, "•  ", "bullet_marker")
                self._insert_inline(bullet.group(1))
                self._txt.insert(tk.END, "\n")
                i += 1
                continue

            numbered = re.match(r"^(\d+)[.)]\s+(.*)", line)
            if numbered:
                self._txt.insert(tk.END, numbered.group(1) + ".  ", "bullet_marker")
                self._insert_inline(numbered.group(2))
                self._txt.insert(tk.END, "\n")
                i += 1
                continue

            if line.strip() == "":
                self._txt.insert(tk.END, "\n")
                i += 1
                continue

            self._insert_inline(line)
            self._txt.insert(tk.END, "\n")
            i += 1

    def _insert_inline(self, text: str) -> None:
        pattern = re.compile(
            r"(\*\*\*(.+?)\*\*\*|\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`)", re.DOTALL
        )
        cursor = 0
        for m in pattern.finditer(text):
            if m.start() > cursor:
                self._txt.insert(tk.END, text[cursor:m.start()], "normal")
            full = m.group(0)
            if full.startswith("***"):
                self._txt.insert(tk.END, m.group(2), "bold_italic")
            elif full.startswith("**"):
                self._txt.insert(tk.END, m.group(3), "bold")
            elif full.startswith("*"):
                self._txt.insert(tk.END, m.group(4), "italic")
            elif full.startswith("`"):
                self._txt.insert(tk.END, m.group(5), "code_inline")
            cursor = m.end()
        if cursor < len(text):
            self._txt.insert(tk.END, text[cursor:], "normal")
