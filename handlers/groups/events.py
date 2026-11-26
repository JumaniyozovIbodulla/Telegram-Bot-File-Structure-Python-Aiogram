from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import ChatMemberUpdatedFilter, Command, IS_MEMBER, IS_NOT_MEMBER
from aiogram.types import ChatMemberUpdated, Message

logger = logging.getLogger(__name__)

router = Router(name="groups_events")
router.message.filter(F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))


@router.message(Command("ping"))
async def cmd_group_ping(message: Message) -> None:
    await message.reply("🏓 Pong! Bot guruhda faol ishlamoqda.")


@router.message(Command("help"))
async def cmd_group_help(message: Message) -> None:
    await message.reply(
        "🤖 <b>Guruh komandalari:</b>\n"
        "• /ping — Bot holatini tekshirish\n"
        "• /help — Yordam\n\n"
        "To'liq Guest Mode va boshqa funksiyalar uchun bot bilan shaxsiy chatda gaplashing."
    )


@router.my_chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def on_bot_added_to_group(event: ChatMemberUpdated) -> None:
    logger.info("Bot added to group: %s (%s)", event.chat.title, event.chat.id)
    await event.answer("👋 Assalomu alaykum! Meni guruhga qo'shganingiz uchun rahmat. /help")
