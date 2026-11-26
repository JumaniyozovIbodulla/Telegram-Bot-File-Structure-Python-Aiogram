from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from data.config import Settings
from utils.db.database import UserRecord

ResponseSource = Literal["private", "guest_message", "inline", "group"]


@dataclass(frozen=True, slots=True)
class ResponderContext:
    """Normalized request context passed to any responder/Cloud API implementation."""

    user_id: int | None
    user_name: str
    role: str
    source: ResponseSource
    guest_requests_today: int = 0
    guest_daily_limit: int = 20


class BaseResponder(Protocol):
    """Interface for response providers (Default, OpenAI, Gemini, custom Cloud API)."""

    async def generate(self, prompt: str, ctx: ResponderContext) -> str:
        """Generate a plain-text (or safe) response for the given prompt and context."""
        ...


class DefaultResponder:
    """
    Production-ready default responder.
    Swap this class with a Cloud API implementation (e.g. httpx call to OpenAI/Gemini/custom backend)
    without modifying any Telegram handlers.
    """

    async def generate(self, prompt: str, ctx: ResponderContext) -> str:
        text = prompt.strip()
        if not text:
            return (
                f"Salom, {ctx.user_name}! Savolingizni yozing — "
                "hozircha default javob rejimi faol, keyinchalik Cloud API ulanadi."
            )

        lower = text.lower()
        if any(greet in lower for greet in ("salom", "assalom", "hello", "hi")):
            return (
                f"Va alaykum assalom, {ctx.user_name}! "
                f"Men {ctx.source} rejimida ishlayapman. Savolingizni yuboring."
            )

        if "guest" in lower:
            if ctx.role == "guest":
                return (
                    f"Siz Guest Mode'dasiz ({ctx.guest_requests_today}/{ctx.guest_daily_limit} "
                    "kunlik so'rov). To'liq rejim uchun /register dan foydalaning."
                )
            return f"Sizning rolingiz: {ctx.role}. Guest cheklovlari yo'q."

        if "aiogram" in lower or "api" in lower or "versiya" in lower:
            return "Bot aiogram 3.34.0 va Telegram Bot API 10.5 (Native Guest Mode) da ishlamoqda."

        return (
            f"Savolingiz qabul qilindi: «{text[:200]}».\n"
            "Hozircha DefaultResponder javob bermoqda — Cloud API ulangach "
            "bu yerga real AI/backend javobi chiqadi."
        )


def build_responder_context(
    *,
    user_id: int | None,
    user_name: str,
    db_user: UserRecord | None,
    settings: Settings,
    source: ResponseSource,
) -> ResponderContext:
    """Create a ResponderContext from database user record and settings."""
    return ResponderContext(
        user_id=user_id,
        user_name=user_name,
        role=db_user.role if db_user else "guest",
        source=source,
        guest_requests_today=db_user.guest_requests_today if db_user else 0,
        guest_daily_limit=settings.guest_daily_limit,
    )


def get_responder() -> BaseResponder:
    """Factory returning the active responder (swap here when connecting Cloud API)."""
    return DefaultResponder()
