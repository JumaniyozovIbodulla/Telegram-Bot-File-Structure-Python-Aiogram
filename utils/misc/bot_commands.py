from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import (
    BotCommand,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeChat,
)

logger = logging.getLogger(__name__)

PRIVATE_COMMANDS: list[BotCommand] = [
    BotCommand(command="start", description="Botni ishga tushirish / Bosh menyu"),
    BotCommand(command="guest", description="Guest Mode holati va imkoniyatlari"),
    BotCommand(command="register", description="To'liq foydalanuvchi sifatida ro'yxatdan o'tish"),
    BotCommand(command="profile", description="Shaxsiy profil va rol"),
    BotCommand(command="features", description="Aiogram 3.34 & Bot API 10.5 demo"),
    BotCommand(command="botinfo", description="BotFullInfo va sozlamalar"),
    BotCommand(command="help", description="Yordam va qo'llanma"),
]

GROUP_COMMANDS: list[BotCommand] = [
    BotCommand(command="help", description="Guruhda botdan foydalanish"),
    BotCommand(command="ping", description="Bot holatini tekshirish"),
]

ADMIN_COMMANDS: list[BotCommand] = PRIVATE_COMMANDS + [
    BotCommand(command="admin", description="Admin panel va statistika"),
]


async def setup_bot_commands(bot: Bot, admin_ids: list[int]) -> None:
    """Register scoped bot commands for private chats, groups, and admins."""
    try:
        await bot.set_my_commands(
            commands=PRIVATE_COMMANDS,
            scope=BotCommandScopeAllPrivateChats(),
        )
        await bot.set_my_commands(
            commands=GROUP_COMMANDS,
            scope=BotCommandScopeAllGroupChats(),
        )
    except TelegramAPIError as exc:
        logger.warning("Failed to set global bot commands: %s", exc)

    for admin_id in admin_ids:
        try:
            await bot.set_my_commands(
                commands=ADMIN_COMMANDS,
                scope=BotCommandScopeChat(chat_id=admin_id),
            )
        except TelegramAPIError as exc:
            logger.debug("Could not set admin commands for %s: %s", admin_id, exc)
