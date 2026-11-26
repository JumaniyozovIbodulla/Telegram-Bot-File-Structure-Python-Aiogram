from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from aiogram import Bot, F, Router, html
from aiogram.exceptions import TelegramAPIError
from aiogram.types import (
    CallbackQuery,
    ChosenInlineResult,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

from data.config import Settings
from keyboards.callbacks import InlineCD
from utils.db.database import UserRecord

router = Router(name="users_inline")


def _generate_answer(question: str, db_user: UserRecord | None, settings: Settings) -> str:
    """
    Build a structured response for an inline question.
    Replace or extend this function with your AI/LLM/DB lookup logic.
    """
    q_lower = question.lower().strip()
    role = db_user.role if db_user else "guest"

    if any(word in q_lower for word in ("salom", "hello", "hi", "assalom")):
        reply = "Va alaykum assalom! Men inline rejimda ham ishlayman. Menga istalgan savol bering."
    elif "guest" in q_lower:
        if db_user and db_user.is_guest:
            reply = (
                f"Siz hozir Guest Mode'dasiz ({db_user.guest_requests_today}/{settings.guest_daily_limit} "
                "kunlik so'rov)."
            )
        else:
            reply = f"Sizning rolingiz: {role}. Guest Mode cheklovlari sizga tatbiq etilmaydi."
    elif "aiogram" in q_lower or "api" in q_lower:
        reply = "Bu bot aiogram 3.34.0 va Telegram Bot API 10.5 da ishlamoqda."
    else:
        reply = (
            f"Savolingiz qabul qilindi ({len(question)} belgi). "
            "Bu yerga AI/LLM yoki ma'lumotlar bazasi javobini ulashingiz mumkin."
        )

    return (
        f"❓ <b>Savol:</b> {html.quote(question)}\n\n"
        f"🤖 <b>Javob:</b> {html.quote(reply)}\n"
        f"<i>Rejim: {role}</i>"
    )


def _inline_reply_markup(bot_username: str | None) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="🔄 Vaqtni yangilash",
                callback_data=InlineCD(action="refresh").pack(),
            )
        ]
    ]
    if bot_username:
        buttons[0].append(
            InlineKeyboardButton(
                text="🤖 Botga o'tish",
                url=f"https://t.me/{bot_username}?start=inline",
            )
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.inline_query()
async def handle_inline_query(
    inline_query: InlineQuery,
    bot: Bot,
    settings: Settings,
    db_user: UserRecord | None = None,
) -> None:
    query = inline_query.query.strip()
    me = await bot.me()
    markup = _inline_reply_markup(me.username)

    if not query:
        results = [
            InlineQueryResultArticle(
                id="inline_help",
                title="💬 Savol berish uchun matn yozing",
                description=f"Masalan: @{me.username} aiogram nima?",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        f"💡 <b>Inline Mode Qo'llanma</b>\n\n"
                        f"Istalgan chatda <code>@{me.username} savolingiz</code> deb yozing "
                        f"va natijani tanlang!"
                    ),
                ),
                reply_markup=markup,
            )
        ]
        await inline_query.answer(results=results, cache_time=5, is_personal=True)
        return

    result_id = hashlib.sha256(query.encode("utf-8")).hexdigest()[:16]
    answer_text = _generate_answer(query, db_user, settings)

    results = [
        InlineQueryResultArticle(
            id=f"ans_{result_id}",
            title=f"🤖 Javob olish: {query[:45]}",
            description="Savol va javobni chatga yuborish",
            input_message_content=InputTextMessageContent(
                message_text=answer_text,
            ),
            reply_markup=markup,
        ),
        InlineQueryResultArticle(
            id=f"echo_{result_id}",
            title=f"📝 Faqat savolni yuborish: {query[:45]}",
            description="Savolni chiroyli formatda yuborish",
            input_message_content=InputTextMessageContent(
                message_text=f"💬 <b>Savol:</b> {html.quote(query)}",
            ),
        ),
    ]
    await inline_query.answer(results=results, cache_time=0, is_personal=True)


@router.chosen_inline_result()
async def handle_chosen_inline_result(chosen: ChosenInlineResult) -> None:
    """
    Triggered when a user picks an inline result (if /setinlinefeedback is enabled in @BotFather).
    If `chosen.inline_message_id` is present, you can asynchronously edit the sent message later.
    """
    _ = chosen


@router.callback_query(InlineCD.filter(F.action == "refresh"))
async def cb_inline_refresh(callback: CallbackQuery, bot: Bot) -> None:
    if not callback.inline_message_id:
        await callback.answer("Bu tugma faqat inline xabarlarda ishlaydi.", show_alert=True)
        return

    now_utc = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
    me = await bot.me()
    try:
        await bot.edit_message_text(
            inline_message_id=callback.inline_message_id,
            text=(
                f"🔄 <b>Inline xabar yangilandi!</b>\n"
                f"🕒 Vaqt: <code>{now_utc}</code>\n"
                f"👤 Yangiladi: {html.quote(callback.from_user.full_name)}"
            ),
            reply_markup=_inline_reply_markup(me.username),
        )
        await callback.answer("Yangilandi ✅")
    except TelegramAPIError as exc:
        await callback.answer(f"Yangilab bo'lmadi: {exc}", show_alert=True)
