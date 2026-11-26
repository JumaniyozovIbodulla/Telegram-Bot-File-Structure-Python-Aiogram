from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import (
    CallbackQuery,
    InlineQuery,
    InlineQueryResultsButton,
    Message,
    TelegramObject,
    User,
)

from data.config import Settings
from utils.db.database import Database


class UserContextMiddleware(BaseMiddleware):
    """
    Injects `db_user`, `is_guest`, `is_admin`, and `guest_mode_enabled`
    into handler data for every incoming Message or CallbackQuery.
    """

    def __init__(self, db: Database, settings: Settings) -> None:
        self.db = db
        self.settings = settings

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user: User | None = data.get("event_from_user")
        if tg_user is None or tg_user.is_bot:
            return await handler(event, data)

        is_admin = tg_user.id in self.settings.admins
        db_user = await self.db.get_or_create_user(
            user_id=tg_user.id,
            username=tg_user.username,
            full_name=tg_user.full_name,
            is_admin=is_admin,
        )

        if db_user.is_banned:
            if isinstance(event, Message) and event.guest_query_id:
                return None
            if isinstance(event, Message):
                await event.answer("⛔️ Sizning hisobingiz bloklangan.")
            elif isinstance(event, CallbackQuery):
                await event.answer("⛔️ Sizning hisobingiz bloklangan.", show_alert=True)
            elif isinstance(event, InlineQuery):
                await event.answer([], cache_time=5, is_personal=True)
            return None

        guest_mode_enabled = await self.db.is_guest_mode_enabled(
            default=self.settings.guest_mode_default
        )

        if db_user.is_guest and not guest_mode_enabled and not is_admin:
            # Allow /start, /register, and upgrade callbacks even when guest mode is disabled
            allowed = False
            if isinstance(event, Message) and event.text:
                cmd = event.text.split()[0].lower()
                allowed = cmd in ("/start", "/register", "/help")
            elif isinstance(event, CallbackQuery) and event.data:
                allowed = event.data.startswith("guest:upgrade") or event.data.startswith("menu:")

            if not allowed:
                if isinstance(event, Message) and event.guest_query_id:
                    return None
                msg = (
                    "🔒 <b>Guest Mode hozircha o'chirilgan.</b>\n"
                    "Botdan to'liq foydalanish uchun /register orqali ro'yxatdan o'ting."
                )
                if isinstance(event, Message):
                    await event.answer(msg)
                elif isinstance(event, CallbackQuery):
                    await event.answer("Guest Mode o'chirilgan. /register bosing.", show_alert=True)
                elif isinstance(event, InlineQuery):
                    await event.answer(
                        [],
                        cache_time=0,
                        is_personal=True,
                        button=InlineQueryResultsButton(
                            text="🔒 Ro'yxatdan o'tish (/register)",
                            start_parameter="register",
                        ),
                    )
                return None

        if db_user.is_guest:
            requests_today = await self.db.increment_guest_requests(tg_user.id)
            db_user.guest_requests_today = requests_today

        data["db_user"] = db_user
        data["is_guest"] = db_user.is_guest
        data["is_admin"] = is_admin or db_user.role == "admin"
        data["guest_mode_enabled"] = guest_mode_enabled
        return await handler(event, data)
