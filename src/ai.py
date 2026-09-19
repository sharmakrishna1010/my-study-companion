"""
ai.py -- Gemini AI client for the Study Companion.

Features:
  - Sends multiple screenshots as visual context
  - Automatic model fallback on rate-limit / quota errors
  - Returns (reply_text, model_used) tuple
"""

from __future__ import annotations

import io

from google import genai
from google.genai import types
from PIL import Image

import config

SYSTEM_INSTRUCTION = """You are a friendly and knowledgeable AI study companion.
You help students by analysing their screenshots and answering questions clearly.

Guidelines:
- Use ALL provided screenshots as visual context.
- Answer the student's specific question directly and concisely.
- Explain diagrams, flowcharts, and architecture drawings step-by-step.
- Explain code snippets with clear reasoning about what each part does.
- Explain equations, graphs, and tables: plain language first, then precisely.
- For textbook or PDF screenshots, explain the concepts shown, not the layout.
- Highlight key exam points or common misconceptions when relevant.
- If something in the image is unclear or cut off, say so explicitly.
- Do NOT hallucinate details that cannot be seen in the images.
- Do NOT describe irrelevant screen elements (taskbars, wallpapers, etc.).
- Use Markdown formatting: **bold** for key terms, bullet lists for steps,
  code blocks for code. This makes your answers easier to read.
- Keep your tone encouraging, patient, and student-friendly.
"""

# Errors that indicate a rate-limit / quota issue worth retrying on another model
_RATE_LIMIT_SIGNALS = (
    "429",
    "quota",
    "rate",
    "resource_exhausted",
    "resourceexhausted",
    "too many requests",
    "per day",
    "per minute",
    "not_found",       # model unavailable / deprecated
    "not found",
)


def _is_rate_or_quota_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(sig in msg for sig in _RATE_LIMIT_SIGNALS)


class AIClient:
    """Wrapper around the Gemini API with multi-screenshot + model-fallback support."""

    def __init__(self, api_key: str, model: str = config.GEMINI_MODEL):
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. "
                "Add it to your .env file: GEMINI_API_KEY=<your-key>"
            )
        self._client = genai.Client(api_key=api_key)
        self._primary_model = model
        self._fallbacks = list(config.GEMINI_MODEL_FALLBACKS)

    def ask(
        self,
        question: str,
        screenshots: list[Image.Image] | Image.Image | None,
        history: list[dict],
    ) -> tuple[str, str]:
        """
        Send question + screenshots + history to Gemini.

        Returns
        -------
        (reply_text, model_name_used)
        """
        # Normalise screenshots to a list
        if screenshots is None:
            shots: list[Image.Image] = []
        elif isinstance(screenshots, list):
            shots = screenshots
        else:
            shots = [screenshots]

        contents = self._build_contents(question, shots, history)
        model_chain = [self._primary_model] + self._fallbacks
        last_exc = None

        for model in model_chain:
            try:
                reply = self._call(model, contents)
                return reply, model
            except Exception as exc:
                last_exc = exc
                if _is_rate_or_quota_error(exc):
                    print(f"[ai] {model} hit limit ({exc.__class__.__name__}), trying next model...")
                    continue
                # Non-rate error: raise immediately
                raise

        raise RuntimeError(
            f"All models exhausted. Last error: {last_exc}"
        ) from last_exc

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_contents(
        self,
        question: str,
        screenshots: list[Image.Image],
        history: list[dict],
    ) -> list[types.Content]:
        contents: list[types.Content] = []

        # History turns (text only — screenshots are always in the latest turn)
        for msg in history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg["text"])],
                )
            )

        # Current user turn: screenshots + question
        parts: list[types.Part] = []

        for img in screenshots:
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            parts.append(
                types.Part.from_bytes(data=buf.getvalue(), mime_type="image/png")
            )

        parts.append(types.Part.from_text(text=question))
        contents.append(types.Content(role="user", parts=parts))
        return contents

    def _call(self, model: str, contents: list[types.Content]) -> str:
        response = self._client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.4,
            ),
        )
        return response.text or "(No response received)"
