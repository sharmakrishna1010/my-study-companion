"""
pet.py -- The animated desktop pet window with FSM, pacing thinking animation, & 8-direction walking.

The pet is a transparent, always-on-top Toplevel window.
An FSM manages states (IDLE, WALKING, THINKING, HAPPY, CONFUSED, SLEEPING).
In IDLE state, the pet periodically walks in 8 directions (Left, Right, Up, Down, Diagonals)
constrained within monitor screen boundaries.
In THINKING state, the pet paces back and forth (left and right) in a small area while thinking.
"""

from __future__ import annotations

import random
import tkinter as tk
from PIL import Image, ImageTk

import config
from pet.drag import make_draggable


# ---------------------------------------------------------------------------
# FSM States
# ---------------------------------------------------------------------------

class PetState:
    """Base class for pet FSM states."""
    name: str = "BASE"

    def enter(self, pet: "Pet") -> None:
        pass

    def update(self, pet: "Pet") -> None:
        pass

    def exit(self, pet: "Pet") -> None:
        pass


class IdleState(PetState):
    name = "IDLE"

    def __init__(self):
        # Randomly idle for 80 to 180 ticks (~12 to 25 seconds)
        self.idle_ticks = random.randint(80, 180)

    def enter(self, pet: "Pet") -> None:
        pet.set_frame_cycle(pet.frames_idle)

    def update(self, pet: "Pet") -> None:
        self.idle_ticks -= 1
        if self.idle_ticks <= 0:
            directions = [
                (1, 0),   # Right
                (-1, 0),  # Left
                (0, 1),   # Down
                (0, -1),  # Up
                (1, 1),   # Down-Right
                (-1, 1),  # Down-Left
                (1, -1),  # Up-Right
                (-1, -1)  # Up-Left
            ]
            dx, dy = random.choice(directions)
            distance = random.randint(80, 240)
            pet.fsm.change_state(WalkingState(dx, dy, distance))


class WalkingState(PetState):
    name = "WALKING"

    def __init__(self, dx: int, dy: int, distance: int):
        self.dx = dx  # -1, 0, 1
        self.dy = dy  # -1, 0, 1
        self.remaining_distance = distance
        self.speed = 3  # pixels per tick

    def enter(self, pet: "Pet") -> None:
        self.update_animation(pet)

    def update_animation(self, pet: "Pet") -> None:
        if self.dy < 0 and self.dx == 0:
            pet.set_frame_cycle(pet.frames_walk_up)
        elif self.dy > 0 and self.dx == 0:
            pet.set_frame_cycle(pet.frames_walk_down)
        elif self.dx < 0:
            pet.set_frame_cycle(pet.frames_walk_left)
        elif self.dx > 0:
            pet.set_frame_cycle(pet.frames_walk_right)
        elif self.dy < 0:
            pet.set_frame_cycle(pet.frames_walk_up)
        else:
            pet.set_frame_cycle(pet.frames_walk_down)

    def update(self, pet: "Pet") -> None:
        curr_x = pet.window.winfo_x()
        curr_y = pet.window.winfo_y()
        sw = pet.window.winfo_screenwidth()
        sh = pet.window.winfo_screenheight()
        pet_w = pet.get_width()
        pet_h = pet.get_height()

        new_x = curr_x + (self.dx * self.speed)
        new_y = curr_y + (self.dy * self.speed)

        # Screen boundary checks
        min_x, max_x = 10, sw - pet_w - 10
        min_y, max_y = 10, sh - pet_h - 70

        bounced = False
        if new_x < min_x:
            new_x = min_x
            self.dx = -self.dx
            bounced = True
        elif new_x > max_x:
            new_x = max_x
            self.dx = -self.dx
            bounced = True

        if new_y < min_y:
            new_y = min_y
            self.dy = -self.dy
            bounced = True
        elif new_y > max_y:
            new_y = max_y
            self.dy = -self.dy
            bounced = True

        if bounced:
            self.update_animation(pet)

        pet.window.geometry(f"+{int(new_x)}+{int(new_y)}")
        self.remaining_distance -= self.speed

        if self.remaining_distance <= 0:
            pet.fsm.change_state(IdleState())


class ThinkingState(PetState):
    """Pet paces left and right continuously in a small area while thinking."""
    name = "THINKING"

    def __init__(self):
        self.origin_x: int | None = None
        self.direction = -1  # -1 = left, 1 = right
        self.pace_range = 35  # pixels left and right
        self.speed = 2

    def enter(self, pet: "Pet") -> None:
        self.origin_x = pet.window.winfo_x()
        if self.direction < 0:
            pet.set_frame_cycle(pet.frames_walk_left)
        else:
            pet.set_frame_cycle(pet.frames_walk_right)

    def update(self, pet: "Pet") -> None:
        if self.origin_x is None:
            self.origin_x = pet.window.winfo_x()

        curr_x = pet.window.winfo_x()
        curr_y = pet.window.winfo_y()
        sw = pet.window.winfo_screenwidth()
        pet_w = pet.get_width()

        new_x = curr_x + (self.direction * self.speed)

        min_x = max(10, self.origin_x - self.pace_range)
        max_x = min(sw - pet_w - 10, self.origin_x + self.pace_range)

        if new_x <= min_x:
            new_x = min_x
            self.direction = 1  # Pace right
            pet.set_frame_cycle(pet.frames_walk_right)
        elif new_x >= max_x:
            new_x = max_x
            self.direction = -1  # Pace left
            pet.set_frame_cycle(pet.frames_walk_left)

        pet.window.geometry(f"+{int(new_x)}+{int(curr_y)}")


class HappyState(PetState):
    name = "HAPPY"

    def __init__(self):
        self.ticks = 25  # Hold for ~3.5 seconds

    def enter(self, pet: "Pet") -> None:
        pet.set_frame_cycle(pet.frames_happy)

    def update(self, pet: "Pet") -> None:
        self.ticks -= 1
        if self.ticks <= 0:
            pet.fsm.change_state(IdleState())


class ConfusedState(PetState):
    name = "CONFUSED"

    def __init__(self):
        self.ticks = 25

    def enter(self, pet: "Pet") -> None:
        pet.set_frame_cycle(pet.frames_confused)

    def update(self, pet: "Pet") -> None:
        self.ticks -= 1
        if self.ticks <= 0:
            pet.fsm.change_state(IdleState())


class SleepingState(PetState):
    name = "SLEEPING"

    def enter(self, pet: "Pet") -> None:
        pet.set_frame_cycle(pet.frames_sleeping)


class PetStateMachine:
    """Finite State Machine Manager for Pet behavior."""

    def __init__(self, pet: "Pet"):
        self.pet = pet
        self.current_state: PetState = IdleState()
        self.current_state.enter(pet)

    def change_state(self, new_state: PetState) -> None:
        if self.current_state:
            self.current_state.exit(self.pet)
        self.current_state = new_state
        self.current_state.enter(self.pet)

    def update(self) -> None:
        if self.current_state:
            self.current_state.update(self.pet)


# ---------------------------------------------------------------------------
# Pet Class
# ---------------------------------------------------------------------------

class Pet:
    """Animated desktop dog pet with FSM, pacing thinking, and 8-direction walking physics."""

    def __init__(self, root: tk.Tk, on_click_callback=None, on_quit_callback=None, on_explain_callback=None):
        self.root = root
        self._on_click_callback = on_click_callback
        self._on_quit_callback = on_quit_callback
        self._on_explain_callback = on_explain_callback

        # Dimensions
        self._scale = config.PET_SCALE
        self._fw = int(config.SPRITE_FRAME_W * self._scale)
        self._fh = int(config.SPRITE_FRAME_H * self._scale)
        self._animation_speed = config.ANIMATION_SPEED_MS

        # Window
        self.window = tk.Toplevel(root)
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)

        self._transparent_color = "#010101"
        self.window.configure(bg=self._transparent_color)
        self.window.attributes("-transparentcolor", self._transparent_color)

        # Canvas
        self.canvas = tk.Canvas(
            self.window,
            width=self._fw,
            height=self._fh,
            bg=self._transparent_color,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack()

        # Sprite Frame Categories
        self.frames_idle: list[ImageTk.PhotoImage] = []
        self.frames_walk_down: list[ImageTk.PhotoImage] = []
        self.frames_walk_up: list[ImageTk.PhotoImage] = []
        self.frames_walk_right: list[ImageTk.PhotoImage] = []
        self.frames_walk_left: list[ImageTk.PhotoImage] = []
        self.frames_thinking: list[ImageTk.PhotoImage] = []
        self.frames_happy: list[ImageTk.PhotoImage] = []
        self.frames_confused: list[ImageTk.PhotoImage] = []
        self.frames_sleeping: list[ImageTk.PhotoImage] = []

        self._load_sprites()

        # Current frame cycle & animation index
        self._active_frames: list[ImageTk.PhotoImage] = self.frames_idle
        self._anim_index = 0
        self._after_id = None

        # FSM State Machine
        self.fsm = PetStateMachine(self)

        # Position: bottom-right of primary monitor
        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()
        x = sw - self._fw - 60
        y = sh - self._fh - 80
        self.window.geometry(f"{self._fw}x{self._fh}+{x}+{y}")

        # Drag + Click + Right-click menu
        make_draggable(self.canvas, self.window)
        self.canvas.bind("<<PetClicked>>", self._on_click)
        self.canvas.bind("<Button-3>", self._show_context_menu)

        # Build Context Menu
        self._context_menu = tk.Menu(
            self.window, tearoff=0,
            bg="#f5ede0", fg="#3d2b1f",
            activebackground="#ede0cb", activeforeground="#3d2b1f",
            relief="flat", bd=0, font=("Segoe UI", 9),
        )
        self._context_menu.add_command(label="💬  Open Chat", command=self._on_click)
        self._context_menu.add_command(label="✨  Explain Screen", command=self._on_explain)

        self._scale_menu = tk.Menu(
            self._context_menu, tearoff=0,
            bg="#f5ede0", fg="#3d2b1f",
            activebackground="#ede0cb", activeforeground="#3d2b1f",
            relief="flat", bd=0, font=("Segoe UI", 9),
        )
        for s in [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]:
            lbl = f"{s:.1f}x" if s != int(s) else f"{int(s)}.0x"
            if s == 4.0:
                lbl += " (Default)"
            self._scale_menu.add_command(label=lbl, command=lambda sc=s: self.set_scale(sc))

        self._context_menu.add_cascade(label="🔍  Pet Scale", menu=self._scale_menu)
        self._context_menu.add_separator()
        self._context_menu.add_command(label="✕  Quit", command=self._quit)

        # Start main loop
        self._animate()

    def get_width(self) -> int:
        return self._fw

    def get_height(self) -> int:
        return self._fh

    def set_frame_cycle(self, frames: list[ImageTk.PhotoImage]) -> None:
        if frames:
            self._active_frames = frames
            self._anim_index = 0

    # ------------------------------------------------------------------
    # Sprite Loading & Slicing
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

        sliced_grid: list[list[Image.Image]] = []
        for r in range(rows):
            row_frames = []
            for c in range(cols):
                box = (c * fw, r * fh, (c + 1) * fw, (r + 1) * fh)
                row_frames.append(sheet.crop(box))
            sliced_grid.append(row_frames)

        def to_tk_list(images: list[Image.Image], flip_h: bool = False) -> list[ImageTk.PhotoImage]:
            result = []
            for img in images:
                if flip_h:
                    img = img.transpose(Image.FLIP_LEFT_RIGHT)
                if target_size != (fw, fh):
                    img = img.resize(target_size, Image.NEAREST)
                result.append(ImageTk.PhotoImage(img))
            return result

        # Map 4x4 Spritesheet Rows:
        # Row 0: Front facing (Down / Front Idle)
        # Row 1: Back facing (Up)
        # Row 2: Left facing
        # Row 3: Right facing
        self.frames_idle = to_tk_list(sliced_grid[0])
        self.frames_walk_down = to_tk_list(sliced_grid[0])
        self.frames_walk_up = to_tk_list(sliced_grid[1])
        self.frames_walk_left = to_tk_list(sliced_grid[2])
        self.frames_walk_right = to_tk_list(sliced_grid[3])

        self.frames_happy = to_tk_list(sliced_grid[0])
        self.frames_confused = to_tk_list(sliced_grid[2])
        self.frames_sleeping = to_tk_list(sliced_grid[2][:2])
        self.frames_thinking = to_tk_list(sliced_grid[3])

    # ------------------------------------------------------------------
    # Main Animation & FSM Loop
    # ------------------------------------------------------------------

    def _animate(self) -> None:
        # Update FSM
        self.fsm.update()

        # Render frame
        if self._active_frames:
            self.canvas.delete("pet")
            idx = self._anim_index % len(self._active_frames)
            self.canvas.create_image(
                self._fw // 2,
                self._fh // 2,
                image=self._active_frames[idx],
                tags="pet",
            )
            self._anim_index = (self._anim_index + 1) % len(self._active_frames)

        self._after_id = self.window.after(self._animation_speed, self._animate)

    # ------------------------------------------------------------------
    # State Control
    # ------------------------------------------------------------------

    def set_state(self, state: str) -> None:
        """Switch FSM state by string name."""
        state = state.upper()
        if state == "IDLE":
            self.fsm.change_state(IdleState())
        elif state == "THINKING":
            self.fsm.change_state(ThinkingState())
        elif state == "HAPPY":
            self.fsm.change_state(HappyState())
        elif state == "CONFUSED":
            self.fsm.change_state(ConfusedState())
        elif state == "SLEEPING":
            self.fsm.change_state(SleepingState())

    def get_state(self) -> str:
        return self.fsm.current_state.name

    def set_scale(self, scale: float) -> None:
        """Dynamically resize pet scale and refresh frames."""
        if scale <= 0:
            return
        self._scale = scale
        config.PET_SCALE = scale
        self._fw = int(config.SPRITE_FRAME_W * self._scale)
        self._fh = int(config.SPRITE_FRAME_H * self._scale)
        self.canvas.configure(width=self._fw, height=self._fh)
        self._load_sprites()
        self.window.geometry(f"{self._fw}x{self._fh}")
        self.set_state(self.get_state())

    def set_animation_speed(self, ms: int) -> None:
        self._animation_speed = ms

    # ------------------------------------------------------------------
    # Interaction Handlers
    # ------------------------------------------------------------------

    def _on_click(self, event=None) -> None:
        # Interrupt walking/pacing if clicked/dragged
        if self.fsm.current_state.name in ("WALKING", "THINKING"):
            self.fsm.change_state(IdleState())
        if self._on_click_callback:
            self._on_click_callback()

    def _on_explain(self, event=None) -> None:
        if self.fsm.current_state.name in ("WALKING", "THINKING"):
            self.fsm.change_state(IdleState())
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

    def destroy(self) -> None:
        if self._after_id:
            self.window.after_cancel(self._after_id)
        self.window.destroy()
