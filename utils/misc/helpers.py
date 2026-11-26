from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup, Message

from data.config import Settings
from utils.db.database import Database
from utils.misc.bot_commands import setup_bot_commands

logger = logging.getLogger(__name__)


async def safe_edit_text(
    message: Message,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> bool:
    """
    Safely edit a message's text, ignoring Telegram's 'message is not modified' error
    when a user clicks the same inline button twice.
    """
    try:
        await message.edit_text(text=text, reply_markup=reply_markup)
        return True
    except TelegramBadRequest as exc:
        if "message is not modified" in str(exc).lower():
            return False
        raise


async def notify_admins(bot: Bot, admin_ids: list[int], text: str) -> None:
    """Send a message to all configured admins without crashing on unreachable chats."""
    for admin_id in admin_ids:
        try:
            await bot.send_message(chat_id=admin_id, text=text)
        except TelegramAPIError as exc:
            logger.warning("Failed to notify admin %s: %s", admin_id, exc)


async def on_startup(bot: Bot, db: Database, settings: Settings) -> None:
    """Run startup lifecycle tasks: DB init, scoped commands, and admin notification."""
    await db.connect()
    await setup_bot_commands(bot, settings.admins)
    me = await bot.me()
    logger.info("Bot started: @%s (id=%s)", me.username, me.id)
    await notify_admins(
        bot,
        settings.admins,
        f"✅ <b>Bot ishga tushdi</b>\n🤖 @{me.username} (aiogram 3.34.0 / Bot API 10.5)",
    )


async def on_shutdown(bot: Bot, db: Database, settings: Settings) -> None:
    """Run shutdown lifecycle tasks: notify admins and close DB cleanly."""
    await notify_admins(bot, settings.admins, "🛑 <b>Bot to'xtatildi</b>")
    await db.close()
    logger.info("Bot shutdown complete.")
