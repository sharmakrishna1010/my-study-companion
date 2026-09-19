"""
config.py -- Centralised configuration for the Study Companion.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

import sys

if getattr(sys, 'frozen', False):
    # PyInstaller extracted temporary directory
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parents[1]

PROJECT_ROOT = BASE_DIR
ASSETS_DIR = BASE_DIR / "assets"
PET_ASSETS_DIR = ASSETS_DIR / "pet"
SPRITESHEET_PATH = PET_ASSETS_DIR / "Basic_Charakter_Spritesheet.png"

# ---------------------------------------------------------------------------
# Environment / API
# ---------------------------------------------------------------------------

env_candidates = []
if getattr(sys, 'frozen', False):
    exe_dir = Path(sys.executable).resolve().parent
    env_candidates.append(exe_dir / ".env")
    env_candidates.append(exe_dir.parent / ".env")
    env_candidates.append(exe_dir.parent.parent / ".env")

env_candidates.append(Path.cwd() / ".env")
env_candidates.append(Path(__file__).resolve().parents[1] / ".env")

for env_path in env_candidates:
    if env_path.is_file():
        load_dotenv(env_path)
        break
else:
    load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ---------------------------------------------------------------------------
# Gemini model
# ---------------------------------------------------------------------------

GEMINI_MODEL = "gemini-2.5-flash"

# Fallback chain tried in order when primary hits rate/quota limits
GEMINI_MODEL_FALLBACKS = [
    "gemini-2.5-flash-lite",   # lighter version, higher quota
    "gemini-3.5-flash-lite",   # next tier
    "gemini-1.5-flash",        # stable older model, generous limits
    "gemini-1.5-flash-8b",     # smallest / fastest, last resort
]

# ---------------------------------------------------------------------------
# Pet / sprite settings
# ---------------------------------------------------------------------------

SPRITE_FRAME_W = 48
SPRITE_FRAME_H = 48
SPRITE_COLS = 4
SPRITE_ROWS = 4

PET_SCALE = 4.0

ANIMATION_SPEED_MS = 150

# ---------------------------------------------------------------------------
# Animation frame indices (row-major into 4x4 grid)
# Row 0 -- front walk cycle (idle)
# Row 1 -- side walk cycle  (happy)
# Row 2 -- sit/sleep        (confused / sleeping)
# Row 3 -- spin / alert     (thinking)
# ---------------------------------------------------------------------------

ANIM_IDLE     = [0, 1, 2, 3]
ANIM_THINKING = [12, 13, 14, 15]
ANIM_HAPPY    = [4, 5, 6, 7]
ANIM_CONFUSED = [8, 9, 10, 11]
ANIM_SLEEPING = [8, 9]

# ---------------------------------------------------------------------------
# Global hotkey
# ---------------------------------------------------------------------------

HOTKEY_MODIFIERS = {"ctrl", "alt"}
HOTKEY_KEY = "s"

# Hotkey for "Explain Screen" (capture + auto-explain without typing)
EXPLAIN_HOTKEY_MODIFIERS = {"ctrl", "alt"}
EXPLAIN_HOTKEY_KEY = "e"

# The question sent automatically when "Explain Screen" is triggered
EXPLAIN_PROMPT = (
    "Please explain everything on my screen clearly. "
    "Describe what I'm looking at, what all the key elements mean, "
    "and any important concepts shown — as if explaining to a student."
)

# ---------------------------------------------------------------------------
# Chat window dimensions
# ---------------------------------------------------------------------------

CHAT_WINDOW_WIDTH  = 480
CHAT_WINDOW_HEIGHT = 600

SCREENSHOT_THUMB_W = 200
SCREENSHOT_THUMB_H = 112

# ---------------------------------------------------------------------------
# Debug
# ---------------------------------------------------------------------------

DEBUG_SAVE_SCREENSHOTS = False
DEBUG_SCREENSHOT_PATH  = PROJECT_ROOT / "debug_screenshot.png"
