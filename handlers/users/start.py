from __future__ import annotations

from aiogram import Bot, F, Router, html
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message, ReactionTypeEmoji

from data.config import Settings
from keyboards.callbacks import MenuCD
from keyboards.default import get_main_reply_keyboard
from keyboards.inline import get_start_inline_keyboard
from services import build_responder_context, get_responder
from utils.db.database import UserRecord
from utils.misc.helpers import safe_edit_text

router = Router(name="users_start")
router.message.filter(F.chat.type == ChatType.PRIVATE)


def _build_welcome_text(user_full_name: str, db_user: UserRecord) -> str:
    role_badge = {
        "guest": "🎭 Guest Mode (Mehmon)",
        "user": "✅ Registered User",
        "admin": "🛠 Admin",
    }.get(db_user.role, db_user.role)

    return (
        f"Assalomu alaykum, {html.bold(user_full_name)}!\n\n"
        f"Bu — <b>aiogram 3.34.0</b> (Bot API 10.5) asosida qurilgan "
        f"zamonaviy <b>GuestMode</b> shabloni.\n\n"
        f"📌 <b>Sizning holatingiz:</b> {role_badge}\n"
        f"Quyidagi tugmalar orqali funksiyalarni sinab ko'ring:"
    )


def _build_profile_text(db_user: UserRecord, settings: Settings) -> str:
    username = f"@{db_user.username}" if db_user.username else "yo'q"
    limit_line = (
        f"📊 <b>Guest kunlik so'rovlar:</b> {db_user.guest_requests_today} / {settings.guest_daily_limit}\n"
        if db_user.is_guest
        else "♾ <b>So'rov limiti:</b> Cheksiz\n"
    )
    return (
        f"👤 <b>Shaxsiy profil</b>\n\n"
        f"🆔 <b>ID:</b> {html.code(str(db_user.user_id))}\n"
        f"👤 <b>Ism:</b> {html.quote(db_user.full_name)}\n"
        f"🔗 <b>Username:</b> {username}\n"
        f"🏷 <b>Rol:</b> {html.code(db_user.role)}\n"
        f"{limit_line}"
        f"📅 <b>Ro'yxatdan o'tgan sana:</b> {db_user.created_at[:10]}"
    )


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    bot: Bot,
    db_user: UserRecord,
    is_guest: bool,
    is_admin: bool,
) -> None:
    try:
        await bot.set_message_reaction(
            chat_id=message.chat.id,
            message_id=message.message_id,
            reaction=[ReactionTypeEmoji(emoji="👍")],
        )
    except TelegramAPIError:
        pass

    name = message.from_user.full_name if message.from_user else db_user.full_name
    await message.answer(
        _build_welcome_text(name, db_user),
        reply_markup=get_main_reply_keyboard(is_guest=is_guest, is_admin=is_admin),
    )
    await message.answer(
        "🧭 <b>Tezkor navigatsiya:</b>",
        reply_markup=get_start_inline_keyboard(is_guest=is_guest, is_admin=is_admin),
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message, is_guest: bool, is_admin: bool) -> None:
    await message.answer(
        "🧭 <b>Bosh menyu:</b>",
        reply_markup=get_start_inline_keyboard(is_guest=is_guest, is_admin=is_admin),
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "📖 <b>Yordam va komandalar</b>\n\n"
        "• /start — Botni ishga tushirish\n"
        "• /guest — Guest Mode holati va limitlar\n"
        "• /register — Scenes Wizard orqali ro'yxatdan o'tish\n"
        "• /profile — Shaxsiy profil ma'lumotlari\n"
        "• /features — aiogram 3.34.0 & Bot API 10.5 imkoniyatlari\n"
        "• /botinfo — BotFullInfo ma'lumotlari\n"
        "• /admin — Admin panel (faqat adminlar uchun)"
    )


@router.message(Command("profile"))
@router.message(F.text == "👤 Profil")
async def cmd_profile(message: Message, db_user: UserRecord, settings: Settings) -> None:
    await message.answer(_build_profile_text(db_user, settings))


@router.callback_query(MenuCD.filter(F.section == "home"))
async def cb_menu_home(
    callback: CallbackQuery,
    db_user: UserRecord,
    is_guest: bool,
    is_admin: bool,
) -> None:
    await callback.answer()
    if callback.message:
        name = callback.from_user.full_name
        await safe_edit_text(
            callback.message,
            _build_welcome_text(name, db_user),
            reply_markup=get_start_inline_keyboard(is_guest=is_guest, is_admin=is_admin),
        )


@router.callback_query(MenuCD.filter(F.section == "profile"))
async def cb_menu_profile(
    callback: CallbackQuery,
    db_user: UserRecord,
    settings: Settings,
    is_guest: bool,
    is_admin: bool,
) -> None:
    await callback.answer()
    if callback.message:
        await safe_edit_text(
            callback.message,
            _build_profile_text(db_user, settings),
            reply_markup=get_start_inline_keyboard(is_guest=is_guest, is_admin=is_admin),
        )


@router.message(F.text & ~F.text.startswith("/"))
async def handle_private_question(
    message: Message,
    db_user: UserRecord,
    settings: Settings,
) -> None:
    """Default fallback responder for free-form text questions in private chat."""
    name = message.from_user.full_name if message.from_user else db_user.full_name
    ctx = build_responder_context(
        user_id=db_user.user_id,
        user_name=name,
        db_user=db_user,
        settings=settings,
        source="private",
    )
    reply_text = await get_responder().generate(message.text or "", ctx)
    await message.answer(f"🤖 {html.quote(reply_text)}")
