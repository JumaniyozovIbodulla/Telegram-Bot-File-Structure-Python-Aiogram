from __future__ import annotations

import asyncio

from aiogram import Bot, F, Router, html
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InputChecklist,
    InputChecklistTask,
    LinkPreviewOptions,
    Message,
    ReactionTypeEmoji,
)
from aiogram.utils.chat_action import ChatActionSender

from keyboards.callbacks import FeatureCD, MenuCD
from keyboards.inline import get_features_inline_keyboard
from utils.misc.bot_settings import get_bot_full_info
from utils.misc.helpers import safe_edit_text

router = Router(name="users_features")
router.message.filter(F.chat.type == ChatType.PRIVATE)

# Built-in Telegram message effect IDs (Private chats)
FIRE_EFFECT_ID = "5104841245755180586"


async def _format_bot_info(bot: Bot) -> str:
    info = await get_bot_full_info(bot)
    usernames = await bot.usernames()
    return (
        "🤖 <b>BotFullInfo (aiogram 3.34.0 / Bot API 10.5)</b>\n\n"
        f"• <b>ID:</b> {html.code(str(info.id))}\n"
        f"• <b>Name:</b> {html.quote(info.first_name)}\n"
        f"• <b>Usernames:</b> {', '.join('@' + u for u in usernames) if usernames else 'yoq'}\n"
        f"• <b>supports_guest_queries:</b> {info.supports_guest_queries}\n"
        f"• <b>supports_inline_queries:</b> {info.supports_inline_queries}\n"
        f"• <b>has_topics_enabled:</b> {info.has_topics_enabled}\n"
        f"• <b>has_topic_sidebar:</b> {info.has_topic_sidebar}\n"
        f"• <b>can_join_groups:</b> {info.can_join_groups}\n"
        f"• <b>can_connect_to_business:</b> {info.can_connect_to_business}\n"
        f"• <b>can_manage_bots:</b> {info.can_manage_bots}"
    )


@router.message(Command("features"))
@router.message(F.text == "🚀 Bot API Features")
async def cmd_features(message: Message) -> None:
    await message.answer(
        "🚀 <b>aiogram 3.34.0 & Telegram Bot API 10.5</b>\n\n"
        "Sinab ko'rmoqchi bo'lgan funksiyani tanlang:",
        reply_markup=get_features_inline_keyboard(),
    )


@router.message(Command("botinfo"))
async def cmd_botinfo(message: Message, bot: Bot) -> None:
    await message.answer(await _format_bot_info(bot))


@router.callback_query(MenuCD.filter(F.section == "features"))
async def cb_features_menu(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await safe_edit_text(
            callback.message,
            "🚀 <b>aiogram 3.34.0 & Telegram Bot API 10.5</b>\n\n"
            "Sinab ko'rmoqchi bo'lgan funksiyani tanlang:",
            reply_markup=get_features_inline_keyboard(),
        )


@router.callback_query(FeatureCD.filter(F.demo == "draft"))
async def cb_demo_draft(callback: CallbackQuery, bot: Bot) -> None:
    await callback.answer("Draft streaming ishga tushdi...")
    if not callback.message:
        return

    chat_id = callback.message.chat.id
    chunks = [
        "⚡️ <b>AI / Draft Streaming (Bot API 10.x)</b>\n\nMatn yozilmoqda.",
        "⚡️ <b>AI / Draft Streaming (Bot API 10.x)</b>\n\nMatn yozilmoqda..",
        "⚡️ <b>AI / Draft Streaming (Bot API 10.x)</b>\n\nMatn yozilmoqda...",
    ]
    try:
        for idx, text in enumerate(chunks, start=1):
            await bot.send_message_draft(
                chat_id=chat_id,
                draft_id=101,
                text=text,
                keep_on_stop=True,
            )
            await asyncio.sleep(0.4)
        await callback.message.answer(
            "✅ <code>send_message_draft</code> muvaffaqiyatli bajarildi!"
        )
    except TelegramAPIError as exc:
        # Fallback if the current bot/client does not support draft streaming
        msg = await callback.message.answer(chunks[0])
        for text in chunks[1:]:
            await asyncio.sleep(0.4)
            await msg.edit_text(text)
        await msg.edit_text(
            f"✅ <b>Draft Fallback:</b>\n<code>send_message_draft</code> API javobi: {html.quote(str(exc))}"
        )


@router.callback_query(FeatureCD.filter(F.demo == "effect"))
async def cb_demo_effect(callback: CallbackQuery, bot: Bot) -> None:
    await callback.answer("Effekt yuborilmoqda!")
    if not callback.message:
        return

    try:
        sent = await callback.message.answer(
            "🔥 <b>Message Effect + Reaction Demo!</b>\n"
            "Bu xabar maxsus animatsion effekt (<code>message_effect_id</code>) bilan yuborildi.",
            message_effect_id=FIRE_EFFECT_ID,
        )
        await bot.set_message_reaction(
            chat_id=sent.chat.id,
            message_id=sent.message_id,
            reaction=[ReactionTypeEmoji(emoji="🔥")],
        )
    except TelegramAPIError as exc:
        await callback.message.answer(f"⚠️ Effekt yuborishda xatolik: {html.quote(str(exc))}")


@router.callback_query(FeatureCD.filter(F.demo == "typing"))
async def cb_demo_typing(callback: CallbackQuery, bot: Bot) -> None:
    await callback.answer("Typing indikatorini kuzating...")
    if not callback.message:
        return

    async with ChatActionSender.typing(bot=bot, chat_id=callback.message.chat.id):
        await asyncio.sleep(2.0)
        await callback.message.answer(
            "⏳ <b>ChatActionSender.typing</b>\n"
            "Uzoq davom etadigan AI/DB operatsiyalar paytida foydalanuvchiga "
            "avtomatik <i>typing...</i> statusini ko'rsatib turadi."
        )


@router.callback_query(FeatureCD.filter(F.demo == "formatting"))
async def cb_demo_formatting(callback: CallbackQuery) -> None:
    await callback.answer()
    if not callback.message:
        return

    quote_text = html.expandable_blockquote(
        "Bu yig'iladigan iqtibos (expandable blockquote).\n"
        "Katta loglar, AI javoblari yoki hujjatlarni ixcham ko'rsatish uchun juda qulay!\n"
        "aiogram.html yordamida XSS-xavfsiz formatlash ishlatilgan."
    )
    spoiler_text = html.spoiler("Yashirin maxfiy matn (Spoiler)")

    await callback.message.answer(
        "📖 <b>Zamonaviy HTML Formatlash & LinkPreviewOptions</b>\n\n"
        f"{quote_text}\n\n"
        f"🔐 Spoiler: {spoiler_text}\n"
        "🔗 Link: https://docs.aiogram.dev/en/v3.34.0/",
        link_preview_options=LinkPreviewOptions(is_disabled=False, prefer_small_media=True),
    )


@router.callback_query(FeatureCD.filter(F.demo == "checklist"))
async def cb_demo_checklist(callback: CallbackQuery) -> None:
    await callback.answer()
    if not callback.message:
        return

    # Demonstrate constructing Bot API 9.x/10.x InputChecklist
    checklist = InputChecklist(
        title="GuestMode Launch Checklist",
        tasks=[
            InputChecklistTask(id=1, text="BOT_TOKEN ni .env ga qo'yish"),
            InputChecklistTask(id=2, text="Guest Mode limitlarini sozlash"),
            InputChecklistTask(id=3, text="Botni ishga tushirish"),
        ],
        others_can_mark_tasks_as_done=True,
    )
    tasks_preview = "\n".join(f"☐ {t.text}" for t in checklist.tasks)
    await callback.message.answer(
        f"☑️ <b>{html.quote(checklist.title)}</b>\n\n"
        f"{tasks_preview}\n\n"
        "<i>Eslatma: Haqiqiy <code>bot.send_checklist(...)</code> metodi Telegram Bot API'da "
        "<code>business_connection_id</code> (Telegram Business) ulangan chatlarda ishlaydi. "
        "Kodda tayyor <code>InputChecklist</code> strukturasi misol qilib ko'rsatilgan.</i>"
    )


@router.callback_query(FeatureCD.filter(F.demo == "botinfo"))
async def cb_demo_botinfo(callback: CallbackQuery, bot: Bot) -> None:
    await callback.answer()
    if callback.message:
        await safe_edit_text(
            callback.message,
            await _format_bot_info(bot),
            reply_markup=get_features_inline_keyboard(),
        )
