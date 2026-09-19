"""
screen.py -- Screen capture utilities.

Primary backend: MSS (fast, cross-platform).
Fallback:        PIL.ImageGrab (Windows-only, no dependencies beyond Pillow).
"""

from __future__ import annotations

import io

import config


def capture_primary():
    """
    Capture the primary monitor and return a PIL Image (RGB).

    Tries MSS first; falls back to PIL.ImageGrab if MSS fails
    (e.g. on some RDP / service-account contexts).
    """
    from PIL import Image

    # -- MSS attempt --
    try:
        import mss
        with mss.mss() as sct:
            monitor = sct.monitors[1]   # index 1 = primary monitor
            screenshot = sct.grab(monitor)
            img = Image.frombytes(
                "RGB",
                screenshot.size,
                screenshot.bgra,
                "raw",
                "BGRX",
            )
    except Exception as mss_err:
        print(f"[screen] MSS failed ({mss_err}); falling back to ImageGrab.")
        from PIL import ImageGrab
        img = ImageGrab.grab()
        if img.mode != "RGB":
            img = img.convert("RGB")

    if config.DEBUG_SAVE_SCREENSHOTS:
        img.save(str(config.DEBUG_SCREENSHOT_PATH))
        print(f"[screen] Screenshot saved to {config.DEBUG_SCREENSHOT_PATH}")

    return img


def image_to_bytes(image, fmt: str = "PNG") -> bytes:
    """Convert a PIL Image to raw bytes (e.g. for Gemini)."""
    buf = io.BytesIO()
    image.save(buf, format=fmt)
    return buf.getvalue()
