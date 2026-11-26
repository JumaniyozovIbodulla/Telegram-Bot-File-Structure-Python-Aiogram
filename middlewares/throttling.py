from __future__ import annotations

import time
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, User

from data.config import Settings


class ThrottlingMiddleware(BaseMiddleware):
    """
    Per-user rate limiter with stricter cooldown for Guest Mode users
    and relaxed cooldown for registered users. Admins bypass throttling.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._last_seen: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user: User | None = data.get("event_from_user")
        if tg_user is None or tg_user.is_bot:
            return await handler(event, data)

        if data.get("is_admin") or tg_user.id in self.settings.admins:
            return await handler(event, data)

        is_guest = bool(data.get("is_guest", True))
        cooldown = (
            self.settings.rate_limit_guest if is_guest else self.settings.rate_limit_user
        )
        if cooldown <= 0:
            return await handler(event, data)

        now = time.monotonic()
        last = self._last_seen.get(tg_user.id, 0.0)
        if now - last < cooldown:
            if isinstance(event, CallbackQuery):
                await event.answer("⏳ Biroz kuting...", show_alert=False)
            elif isinstance(event, Message):
                await event.answer(
                    f"⏳ Juda tez yozmoqdasiz. {cooldown:.1f}s kuting."
                )
            return None

        self._last_seen[tg_user.id] = now
        return await handler(event, data)
