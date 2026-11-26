from __future__ import annotations

import logging
import re

from aiogram import Bot, F, Router, html
from aiogram.enums import ChatType
from aiogram.filters import ChatMemberUpdatedFilter, Command, IS_MEMBER, IS_NOT_MEMBER
from aiogram.types import ChatMemberUpdated, Message

from data.config import Settings
from services import build_responder_context, get_responder
from utils.db.database import UserRecord

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
        "Guruhda meni <code>@username savol</code> ko'rinishida chaqirishingiz mumkin."
    )


@router.my_chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def on_bot_added_to_group(event: ChatMemberUpdated) -> None:
    logger.info("Bot added to group: %s (%s)", event.chat.title, event.chat.id)
    await event.answer("👋 Assalomu alaykum! Meni guruhga qo'shganingiz uchun rahmat. /help")


@router.message(F.text | F.caption)
async def handle_group_mention(
    message: Message,
    bot: Bot,
    settings: Settings,
    db_user: UserRecord | None = None,
) -> None:
    """Respond when the bot IS a member of the group and is mentioned or replied to."""
    me = await bot.me()
    raw_text = message.text or message.caption or ""
    username = me.username or ""

    is_mentioned = bool(username and f"@{username.lower()}" in raw_text.lower())
    is_reply_to_bot = bool(
        message.reply_to_message
        and message.reply_to_message.from_user
        and message.reply_to_message.from_user.id == me.id
    )
    if not (is_mentioned or is_reply_to_bot):
        return

    question = (
        re.sub(rf"@{re.escape(username)}\b", "", raw_text, flags=re.IGNORECASE).strip()
        if username
        else raw_text.strip()
    )
    caller_name = message.from_user.full_name if message.from_user else "Foydalanuvchi"
    caller_id = message.from_user.id if message.from_user else None

    ctx = build_responder_context(
        user_id=caller_id,
        user_name=caller_name,
        db_user=db_user,
        settings=settings,
        source="group",
    )
    reply_text = await get_responder().generate(question, ctx)
    await message.reply(f"🤖 {html.quote(reply_text)}")
