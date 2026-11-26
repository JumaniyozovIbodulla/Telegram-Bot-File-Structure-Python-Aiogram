from __future__ import annotations

import logging
from typing import Any

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import BotFullInfo

logger = logging.getLogger(__name__)


async def get_bot_full_info(bot: Bot) -> BotFullInfo:
    """Fetch cached BotFullInfo (aiogram 3.34+ / Bot API 10.5)."""
    return await bot.me()


async def apply_bot_settings(
    bot: Bot,
    *,
    supports_guest_queries: bool | None = None,
    has_topics_enabled: bool | None = None,
    allows_users_to_create_topics: bool | None = None,
    has_topic_sidebar: bool | None = None,
    inline_query_placeholder: str | None = None,
) -> tuple[bool, str | None]:
    """
    Safely apply Bot API 10.5 `set_my_settings` options.

    Returns `(success, error_message)` so unsupported account-level flags
    never crash the bot.
    """
    payload: dict[str, Any] = {}
    if supports_guest_queries is not None:
        payload["supports_guest_queries"] = supports_guest_queries
    if has_topics_enabled is not None:
        payload["has_topics_enabled"] = has_topics_enabled
    if allows_users_to_create_topics is not None:
        payload["allows_users_to_create_topics"] = allows_users_to_create_topics
    if has_topic_sidebar is not None:
        payload["has_topic_sidebar"] = has_topic_sidebar
    if inline_query_placeholder is not None:
        payload["inline_query_placeholder"] = inline_query_placeholder

    if not payload:
        return True, None

    try:
        result = await bot.set_my_settings(**payload)
        return bool(result), None
    except TelegramAPIError as exc:
        logger.warning("set_my_settings failed for %s: %s", payload, exc)
        return False, str(exc)
