"""Thin wrapper around the Anthropic SDK that always returns a validated Pydantic model."""

import base64
from typing import Optional, TypeVar

import anthropic
from pydantic import BaseModel

from . import config

T = TypeVar("T", bound=BaseModel)

SYSTEM_PROMPT = (
    "You are the analysis engine of a construction intelligence platform used by site engineers, "
    "safety officers, project managers and property professionals. Give practical, specific, "
    "field-ready guidance grounded in recognised construction practice (OSHA, IS/BIS codes, ACI, "
    "Eurocode, NBC as relevant). Be honest about uncertainty: when an image is unclear or data is "
    "missing, say so in the relevant text field and lower confidence or severity estimates "
    "accordingly rather than inventing detail. Your analysis supports, and never replaces, "
    "inspection by a qualified professional."
)


class AIError(Exception):
    """Raised with a user-safe message when the model call fails."""


_client: Optional[anthropic.AsyncAnthropic] = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY or None)
    return _client


def image_block(data: bytes, media_type: str) -> dict:
    return {
        "type": "image",
        "source": {"type": "base64", "media_type": media_type, "data": base64.standard_b64encode(data).decode()},
    }


async def generate(schema: type[T], prompt: str, images: Optional[list[dict]] = None) -> T:
    content = [*(images or []), {"type": "text", "text": prompt}]
    extra = {}
    if config.CLAUDE_FALLBACKS:
        extra = {
            "extra_headers": {"anthropic-beta": "server-side-fallback-2026-07-01"},
            "extra_body": {"fallbacks": "default"},
        }
    try:
        response = await _get_client().messages.parse(
            model=config.CLAUDE_MODEL,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            output_config={"effort": config.CLAUDE_EFFORT},
            messages=[{"role": "user", "content": content}],
            output_format=schema,
            **extra,
        )
    except anthropic.AuthenticationError as e:
        raise AIError("The AI service rejected the API key. Check ANTHROPIC_API_KEY.") from e
    except anthropic.RateLimitError as e:
        raise AIError("The AI service is rate limited right now. Try again in a minute.") from e
    except anthropic.BadRequestError as e:
        raise AIError(f"The AI service rejected the request: {e.message}") from e
    except anthropic.APIStatusError as e:
        raise AIError(f"The AI service returned an error ({e.status_code}). Try again.") from e
    except anthropic.APIConnectionError as e:
        raise AIError("Could not reach the AI service. Check your network connection.") from e

    if response.stop_reason == "refusal":
        raise AIError("The AI declined to analyse this request.")
    if response.stop_reason == "max_tokens" or response.parsed_output is None:
        raise AIError("The AI response was incomplete. Try a shorter or simpler request.")
    return response.parsed_output
