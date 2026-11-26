from __future__ import annotations

import hashlib
import logging
import re

from aiogram import Bot, Router, html
from aiogram.exceptions import TelegramAPIError
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Message,
)

from data.config import Settings
from keyboards.callbacks import InlineCD
from services import build_responder_context, get_responder
from utils.db.database import UserRecord

logger = logging.getLogger(__name__)

router = Router(name="users_guest_queries")


def _strip_bot_mention(text: str, bot_username: str | None) -> str:
    if not text:
        return ""
    if bot_username:
        pattern = re.compile(rf"@{re.escape(bot_username)}\b", re.IGNORECASE)
        text = pattern.sub("", text)
    return text.strip()


def _guest_reply_markup(bot_username: str | None) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="🔄 Yangilash",
                callback_data=InlineCD(action="refresh").pack(),
            )
        ]
    ]
    if bot_username:
        buttons[0].append(
            InlineKeyboardButton(
                text="🤖 Botga o'tish",
                url=f"https://t.me/{bot_username}?start=guest",
            )
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.guest_message()
async def handle_guest_message(
    message: Message,
    bot: Bot,
    settings: Settings,
    db_user: UserRecord | None = None,
) -> None:
    """
    Handle native Telegram Bot API Guest Mode updates (`Update.guest_message`).
    Triggered when a user mentions @bot_username or replies to the bot in any chat
    where the bot is NOT a member.
    """
    logger.info(
        "Received guest_message: query_id=%s caller=%s chat=%s",
        message.guest_query_id,
        getattr(message.guest_bot_caller_user, "id", None),
        getattr(message.guest_bot_caller_chat, "id", None),
    )
    if not message.guest_query_id:
        return

    me = await bot.me()
    raw_text = message.text or message.caption or ""
    question = _strip_bot_mention(raw_text, me.username)

    caller = message.guest_bot_caller_user or message.from_user
    caller_name = caller.full_name if caller else "Mehmon"
    caller_id = caller.id if caller else None

    ctx = build_responder_context(
        user_id=caller_id,
        user_name=caller_name,
        db_user=db_user,
        settings=settings,
        source="guest_message",
    )
    reply_text = await get_responder().generate(question, ctx)

    if question:
        formatted = (
            f"❓ <b>Savol ({html.quote(caller_name)}):</b> {html.quote(question)}\n\n"
            f"🤖 <b>Javob:</b> {html.quote(reply_text)}"
        )
    else:
        formatted = f"🤖 <b>Javob:</b> {html.quote(reply_text)}"

    result_id = hashlib.sha256(
        f"{message.guest_query_id}:{question}".encode("utf-8")
    ).hexdigest()[:16]

    article = InlineQueryResultArticle(
        id=f"guest_{result_id}",
        title="Guest Mode javobi",
        input_message_content=InputTextMessageContent(message_text=formatted),
        reply_markup=_guest_reply_markup(me.username),
    )

    try:
        sent = await bot.answer_guest_query(
            guest_query_id=message.guest_query_id,
            result=article,
        )
        logger.info(
            "Answered guest_query_id=%s (inline_message_id=%s)",
            message.guest_query_id,
            sent.inline_message_id,
        )
    except TelegramAPIError as exc:
        logger.warning("answer_guest_query failed: %s", exc)
