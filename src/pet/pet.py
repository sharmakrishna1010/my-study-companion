"""
pet.py -- The animated desktop pet window.

The pet is a transparent, always-on-top Toplevel that displays the dog sprite.
It supports multiple named states (IDLE, THINKING, HAPPY, CONFUSED, SLEEPING),
each mapped to a subset of sprite frames from the 4x4 spritesheet.
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from PIL import Image, ImageTk

import config
from pet.drag import make_draggable


# Map state names to frame-index lists (defined in config.py)
STATE_FRAMES: dict[str, list[int]] = {
    "IDLE":     config.ANIM_IDLE,
    "THINKING": config.ANIM_THINKING,
    "HAPPY":    config.ANIM_HAPPY,
    "CONFUSED": config.ANIM_CONFUSED,
    "SLEEPING": config.ANIM_SLEEPING,
}


class Pet:
    """Animated desktop dog pet."""

    def __init__(self, root: tk.Tk, on_click_callback=None, on_quit_callback=None, on_explain_callback=None):
        self.root = root
        self._on_click_callback = on_click_callback
        self._on_quit_callback = on_quit_callback
        self._on_explain_callback = on_explain_callback

        # ----------------------------------------------------------------
        # Derived dimensions
        # ----------------------------------------------------------------
        self._scale = config.PET_SCALE
        self._fw = int(config.SPRITE_FRAME_W * self._scale)
        self._fh = int(config.SPRITE_FRAME_H * self._scale)
        self._animation_speed = config.ANIMATION_SPEED_MS

        # ----------------------------------------------------------------
        # Transparent borderless window
        # ----------------------------------------------------------------
        self.window = tk.Toplevel(root)
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)

        self._transparent_color = "#010101"   # unique colour used as chroma-key
        self.window.configure(bg=self._transparent_color)
        self.window.attributes("-transparentcolor", self._transparent_color)

        # ----------------------------------------------------------------
        # Canvas
        # ----------------------------------------------------------------
        self.canvas = tk.Canvas(
            self.window,
            width=self._fw,
            height=self._fh,
            bg=self._transparent_color,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack()

        # ----------------------------------------------------------------
        # Load all 16 sprite frames
        # ----------------------------------------------------------------
        self._all_frames: list[ImageTk.PhotoImage] = []
        self._load_sprites()

        # ----------------------------------------------------------------
        # Animation state
        # ----------------------------------------------------------------
        self._state = "IDLE"
        self._anim_frames: list[int] = STATE_FRAMES["IDLE"]
        self._anim_index = 0
        self._after_id = None

        # ----------------------------------------------------------------
        # Position: bottom-right of primary monitor
        # ----------------------------------------------------------------
        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()
        x = sw - self._fw - 60
        y = sh - self._fh - 80
        self.window.geometry(f"{self._fw}x{self._fh}+{x}+{y}")

        # ----------------------------------------------------------------
        # Drag + click + right-click menu
        # ----------------------------------------------------------------
        make_draggable(self.canvas, self.window)
        self.canvas.bind("<<PetClicked>>", self._on_click)
        self.canvas.bind("<Button-3>", self._show_context_menu)

        # Build right-click menu — warm cream palette matching the pet
        self._context_menu = tk.Menu(
            self.window, tearoff=0,
            bg="#f5ede0", fg="#3d2b1f",
            activebackground="#ede0cb", activeforeground="#3d2b1f",
            relief="flat", bd=0,
            font=("Segoe UI", 9),
        )
        self._context_menu.add_command(
            label="💬  Open Chat",
            command=self._on_click,
        )
        self._context_menu.add_command(
            label="✨  Explain Screen",
            command=self._on_explain,
        )
        self._context_menu.add_separator()
        self._context_menu.add_command(
            label="✕  Quit",
            command=self._quit,
        )

        # ----------------------------------------------------------------
        # Start animation loop
        # ----------------------------------------------------------------
        self._animate()

    # ------------------------------------------------------------------
    # Sprite loading
    # ------------------------------------------------------------------

    def _load_sprites(self) -> None:
        path = config.SPRITESHEET_PATH
        if not path.exists():
            print(f"[pet] Spritesheet not found: {path}")
            return

        sheet = Image.open(path).convert("RGBA")
        cols = config.SPRITE_COLS
        rows = config.SPRITE_ROWS
        fw = config.SPRITE_FRAME_W
        fh = config.SPRITE_FRAME_H

        target_size = (self._fw, self._fh)

        for row in range(rows):
            for col in range(cols):
                left   = col * fw
                upper  = row * fh
                right  = left + fw
                lower  = upper + fh
                frame  = sheet.crop((left, upper, right, lower))
                if target_size != (fw, fh):
                    frame = frame.resize(target_size, Image.NEAREST)
                self._all_frames.append(ImageTk.PhotoImage(frame))

    # ------------------------------------------------------------------
    # Animation loop
    # ------------------------------------------------------------------

    def _animate(self) -> None:
        if self._all_frames and self._anim_frames:
            self.canvas.delete("pet")
            idx = self._anim_frames[self._anim_index % len(self._anim_frames)]
            if idx < len(self._all_frames):
                self.canvas.create_image(
                    self._fw // 2,
                    self._fh // 2,
                    image=self._all_frames[idx],
                    tags="pet",
                )
            self._anim_index = (self._anim_index + 1) % len(self._anim_frames)

        self._after_id = self.window.after(self._animation_speed, self._animate)

    # ------------------------------------------------------------------
    # State control
    # ------------------------------------------------------------------

    def set_state(self, state: str) -> None:
        """Switch to a named animation state (IDLE, THINKING, HAPPY, etc.)."""
        state = state.upper()
        if state not in STATE_FRAMES:
            print(f"[pet] Unknown state: {state}")
            return
        if state == self._state:
            return
        self._state = state
        self._anim_frames = STATE_FRAMES[state]
        self._anim_index = 0

    def get_state(self) -> str:
        return self._state

    def set_animation_speed(self, ms: int) -> None:
        self._animation_speed = ms

    # ------------------------------------------------------------------
    # Visibility
    # ------------------------------------------------------------------

    def show(self) -> None:
        self.window.deiconify()

    def hide(self) -> None:
        self.window.withdraw()

    def destroy(self) -> None:
        if self._after_id:
            self.window.after_cancel(self._after_id)
        self.window.destroy()

    # ------------------------------------------------------------------
    # Interaction
    # ------------------------------------------------------------------

    def _on_click(self, event=None) -> None:
        if self._on_click_callback:
            self._on_click_callback()

    def _on_explain(self, event=None) -> None:
        if self._on_explain_callback:
            self._on_explain_callback()

    def _show_context_menu(self, event: tk.Event) -> None:
        try:
            self._context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self._context_menu.grab_release()

    def _quit(self) -> None:
        if self._on_quit_callback:
            self._on_quit_callback()
        else:
            self.root.quit()

