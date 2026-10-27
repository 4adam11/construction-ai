import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-5-5")
CLAUDE_EFFORT = os.getenv("CLAUDE_EFFORT", "medium")
# Server-side refusal fallback: if a request is declined, the API re-runs it on
# a fallback model inside the same call. Set to false to disable.
CLAUDE_FALLBACKS = _bool("CLAUDE_FALLBACKS", True)

# MOCK_MODE=auto -> mock only when no API key is configured.
_mock = os.getenv("MOCK_MODE", "auto").strip().lower()
MOCK_MODE = (not ANTHROPIC_API_KEY) if _mock == "auto" else _mock in {"1", "true", "yes", "on"}

CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5174").split(",") if o.strip()]

MAX_IMAGE_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
