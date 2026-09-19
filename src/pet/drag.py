"""
drag.py -- Makes a tkinter window draggable by binding mouse events.

Usage
-----
    from drag import make_draggable
    make_draggable(widget, window)

`widget` is the widget the user drags (e.g. a Canvas).
`window` is the Toplevel that actually moves.
"""

from __future__ import annotations

import tkinter as tk


def make_draggable(widget: tk.Widget, window: tk.Toplevel) -> None:
    """
    Attach drag handlers to `widget` so that dragging it moves `window`.

    We track whether the mouse moved between ButtonPress and ButtonRelease
    so that a stationary click is still treated as a normal click event
    and propagated to other bindings (e.g. on_click).
    """
    state = {"x": 0, "y": 0, "dragging": False}

    def on_press(event: tk.Event) -> None:
        state["x"] = event.x_root
        state["y"] = event.y_root
        state["dragging"] = False

    def on_drag(event: tk.Event) -> None:
        dx = event.x_root - state["x"]
        dy = event.y_root - state["y"]
        if abs(dx) > 3 or abs(dy) > 3:
            state["dragging"] = True
        if state["dragging"]:
            x = window.winfo_x() + dx
            y = window.winfo_y() + dy
            window.geometry(f"+{x}+{y}")
            state["x"] = event.x_root
            state["y"] = event.y_root

    def on_release(event: tk.Event) -> None:
        # If we did not actually drag, let the click propagate normally.
        if not state["dragging"]:
            widget.event_generate("<<PetClicked>>")

    widget.bind("<ButtonPress-1>", on_press, add="+")
    widget.bind("<B1-Motion>", on_drag, add="+")
    widget.bind("<ButtonRelease-1>", on_release, add="+")
