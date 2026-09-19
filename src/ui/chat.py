"""
chat.py -- Chat display with Markdown rendering.

Colour palette: warm cream / ivory derived from the pixel-art pet sprite
  (cream body, warm gold accents, soft lavender highlights).
"""

from __future__ import annotations

import re
import tkinter as tk
from tkinter import ttk

# ---------------------------------------------------------------------------
# Palette  (pet-inspired: cream, warm gold, soft lavender)
# ---------------------------------------------------------------------------
BG_CHAT      = "#fdf8f0"   # warm ivory  — main chat background
BG_USER_MSG  = "#ede0cb"   # warm tan    — user bubble
BG_AI_MSG    = "#f5ede0"   # soft cream  — AI bubble
BG_CODE      = "#e8d9c0"   # toasted parchment — code blocks
FG_MAIN      = "#3d2b1f"   # dark cocoa  — primary text
FG_BOLD      = "#2a1a10"   # deepest brown for bold
FG_CODE      = "#7c5cbf"   # soft lavender-purple (pet accent)
FG_HEADING   = "#b87333"   # warm copper-gold (pet accent)
FG_LABEL     = "#a08060"   # muted warm tan — sender names
FG_SYSTEM    = "#b8a090"   # dusty rose-tan — system notices
FG_BULLET    = "#c8855a"   # amber rust — bullet markers
BORDER       = "#ddd0bb"   # hairline border

FONT_BASE    = ("Segoe UI", 10)
FONT_BOLD    = ("Segoe UI", 10, "bold")
FONT_ITALIC  = ("Segoe UI", 10, "italic")
FONT_BI      = ("Segoe UI", 10, "bold italic")
FONT_CODE    = ("Consolas", 9)
FONT_H1      = ("Segoe UI", 14, "bold")
FONT_H2      = ("Segoe UI", 12, "bold")
FONT_H3      = ("Segoe UI", 11, "bold")
FONT_LABEL   = ("Segoe UI", 8, "bold")
FONT_SYSTEM  = ("Segoe UI", 8, "italic")


# ---------------------------------------------------------------------------
# Markdown renderer
# ---------------------------------------------------------------------------

def _render_markdown(text_widget: tk.Text, text: str, fg: str) -> None:
    text_widget.tag_configure("normal",      font=FONT_BASE,   foreground=fg)
    text_widget.tag_configure("bold",        font=FONT_BOLD,   foreground=FG_BOLD)
    text_widget.tag_configure("italic",      font=FONT_ITALIC, foreground=fg)
    text_widget.tag_configure("bold_italic", font=FONT_BI,     foreground=FG_BOLD)
    text_widget.tag_configure("code_inline", font=FONT_CODE,   foreground=FG_CODE,
                              background=BG_CODE)
    text_widget.tag_configure("code_block",  font=FONT_CODE,   foreground=FG_CODE,
                              background=BG_CODE, lmargin1=8, lmargin2=8,
                              spacing1=2, spacing3=2)
    text_widget.tag_configure("h1",  font=FONT_H1, foreground=FG_HEADING)
    text_widget.tag_configure("h2",  font=FONT_H2, foreground=FG_HEADING)
    text_widget.tag_configure("h3",  font=FONT_H3, foreground=FG_HEADING)
    text_widget.tag_configure("bullet",        font=FONT_BASE, foreground=fg,
                              lmargin1=12, lmargin2=24)
    text_widget.tag_configure("bullet_marker", font=FONT_BOLD, foreground=FG_BULLET)
    text_widget.tag_configure("numbered",      font=FONT_BASE, foreground=fg,
                              lmargin1=12, lmargin2=28)

    lines = text.split("\n")
    in_code_block = False
    i = 0
    while i < len(lines):
        line = lines[i]

        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            if not in_code_block:
                text_widget.insert(tk.END, "\n")
            i += 1
            continue

        if in_code_block:
            text_widget.insert(tk.END, line + "\n", "code_block")
            i += 1
            continue

        m_h3 = re.match(r"^###\s+(.*)", line)
        m_h2 = re.match(r"^##\s+(.*)",  line)
        m_h1 = re.match(r"^#\s+(.*)",   line)
        if m_h1:
            text_widget.insert(tk.END, m_h1.group(1) + "\n", "h1"); i += 1; continue
        if m_h2:
            text_widget.insert(tk.END, m_h2.group(1) + "\n", "h2"); i += 1; continue
        if m_h3:
            text_widget.insert(tk.END, m_h3.group(1) + "\n", "h3"); i += 1; continue

        bullet = re.match(r"^[\-\*\•]\s+(.*)", line)
        if bullet:
            text_widget.insert(tk.END, "•  ", "bullet_marker")
            _insert_inline(text_widget, bullet.group(1), fg)
            text_widget.insert(tk.END, "\n")
            i += 1; continue

        numbered = re.match(r"^(\d+)[.)]\s+(.*)", line)
        if numbered:
            text_widget.insert(tk.END, numbered.group(1) + ".  ", "bullet_marker")
            _insert_inline(text_widget, numbered.group(2), fg)
            text_widget.insert(tk.END, "\n")
            i += 1; continue

        if line.strip() == "":
            text_widget.insert(tk.END, "\n"); i += 1; continue

        _insert_inline(text_widget, line, fg)
        text_widget.insert(tk.END, "\n")
        i += 1


def _insert_inline(text_widget: tk.Text, text: str, fg: str) -> None:
    pattern = re.compile(
        r"(\*\*\*(.+?)\*\*\*|\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`)", re.DOTALL
    )
    cursor = 0
    for m in pattern.finditer(text):
        if m.start() > cursor:
            text_widget.insert(tk.END, text[cursor:m.start()], "normal")
        full = m.group(0)
        if full.startswith("***"):
            text_widget.insert(tk.END, m.group(2), "bold_italic")
        elif full.startswith("**"):
            text_widget.insert(tk.END, m.group(3), "bold")
        elif full.startswith("*"):
            text_widget.insert(tk.END, m.group(4), "italic")
        elif full.startswith("`"):
            text_widget.insert(tk.END, m.group(5), "code_inline")
        cursor = m.end()
    if cursor < len(text):
        text_widget.insert(tk.END, text[cursor:], "normal")


# ---------------------------------------------------------------------------
# ChatDisplay widget
# ---------------------------------------------------------------------------

class ChatDisplay(tk.Frame):
    """Scrollable warm-cream chat area with Markdown rendering."""

    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, bg=BG_CHAT, **kwargs)

        self._canvas = tk.Canvas(self, bg=BG_CHAT, highlightthickness=0)
        self._scrollbar = ttk.Scrollbar(
            self, orient="vertical", command=self._canvas.yview
        )
        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        self._inner = tk.Frame(self._canvas, bg=BG_CHAT)
        self._inner_id = self._canvas.create_window(
            (0, 0), window=self._inner, anchor="nw"
        )

        self._canvas.pack(side="left", fill="both", expand=True)
        self._scrollbar.pack(side="right", fill="y")

        self._inner.bind("<Configure>", self._on_inner_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self._canvas_width = 440

    def _on_inner_configure(self, _=None):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self._canvas_width = event.width
        self._canvas.itemconfig(self._inner_id, width=event.width)

    def _on_mousewheel(self, event):
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def append_user(self, text: str) -> None:
        self._add_plain("You", text, FG_MAIN, BG_USER_MSG, anchor="e")

    def append_ai(self, text: str) -> None:
        self._add_markdown("Buddy", text, FG_MAIN, BG_AI_MSG)

    def append_system(self, text: str) -> None:
        tk.Label(
            self._inner, text=text,
            bg=BG_CHAT, fg=FG_SYSTEM,
            font=FONT_SYSTEM, wraplength=400, justify="center", pady=3,
        ).pack(fill="x", padx=16, pady=2)
        self._scroll_to_bottom()

    def clear(self) -> None:
        for w in self._inner.winfo_children():
            w.destroy()

    # ------------------------------------------------------------------
    # Builders
    # ------------------------------------------------------------------

    def _add_plain(self, sender, text, fg, bg, anchor):
        outer = tk.Frame(self._inner, bg=BG_CHAT)
        outer.pack(fill="x", padx=10, pady=(6, 2))

        tk.Label(outer, text=sender, bg=BG_CHAT, fg=FG_LABEL,
                 font=FONT_LABEL).pack(anchor=anchor)

        bubble = tk.Label(
            outer, text=text, bg=bg, fg=fg, font=FONT_BASE,
            wraplength=max(180, self._canvas_width - 60),
            justify="left", padx=12, pady=8, relief="flat",
        )
        bubble.pack(anchor=anchor)
        self._scroll_to_bottom()

    def _add_markdown(self, sender, text, fg, bg):
        outer = tk.Frame(self._inner, bg=BG_CHAT)
        outer.pack(fill="x", padx=10, pady=(6, 2))

        tk.Label(outer, text=sender, bg=BG_CHAT, fg=FG_LABEL,
                 font=FONT_LABEL).pack(anchor="w")

        bubble = tk.Frame(outer, bg=bg, padx=4, pady=6)
        bubble.pack(anchor="w", fill="x")

        txt = tk.Text(
            bubble, bg=bg, fg=fg, font=FONT_BASE,
            wrap="word", relief="flat", borderwidth=0,
            highlightthickness=0, state="normal",
            cursor="arrow", width=1, height=1,
            padx=8, pady=4, spacing1=1, spacing3=2,
        )
        txt.pack(fill="x", expand=True)

        _render_markdown(txt, text, fg)
        txt.configure(state="disabled")

        txt.update_idletasks()
        line_count = int(txt.index(tk.END).split(".")[0])
        txt.configure(height=max(1, line_count))

        self._scroll_to_bottom()

    def _scroll_to_bottom(self) -> None:
        self._inner.update_idletasks()
        self._canvas.yview_moveto(1.0)
