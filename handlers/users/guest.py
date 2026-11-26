from __future__ import annotations

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.fsm.scene import ScenesManager
from aiogram.types import CallbackQuery, Message

from data.config import Settings
from keyboards.callbacks import GuestCD, MenuCD
from keyboards.default import get_main_reply_keyboard
from keyboards.inline import get_guest_inline_keyboard
from states.onboarding import RegistrationScene
from utils.db.database import Database, UserRecord

router = Router(name="users_guest")
router.message.filter(F.chat.type == ChatType.PRIVATE)


def _guest_status_text(db_user: UserRecord, settings: Settings, guest_mode_enabled: bool) -> str:
    global_status = "🟢 Yoqilgan" if guest_mode_enabled else "🔴 O'chirilgan"
    if db_user.is_guest:
        remaining = max(0, settings.guest_daily_limit - db_user.guest_requests_today)
        return (
            "🎭 <b>Guest Mode (Mehmon rejimi)</b>\n\n"
            f"• <b>Sizning holatingiz:</b> Mehmon (Guest)\n"
            f"• <b>Global Guest Mode:</b> {global_status}\n"
            f"• <b>Bugungi so'rovlar:</b> {db_user.guest_requests_today} / {settings.guest_daily_limit} "
            f"(qoldi: {remaining})\n"
            f"• <b>Rate-limit:</b> {settings.rate_limit_guest}s\n\n"
            "<i>To'liq imkoniyatlarni ochish uchun ro'yxatdan o'ting.</i>"
        )
    return (
        "🎭 <b>Guest Mode</b>\n\n"
        f"• <b>Sizning holatingiz:</b> To'liq foydalanuvchi ({db_user.role})\n"
        f"• <b>Global Guest Mode:</b> {global_status}\n"
        f"• <b>Rate-limit:</b> {settings.rate_limit_user}s (yoki admin uchun cheksiz)\n\n"
        "Demo sifatida vaqtincha Guest Mode'ga qaytishingiz mumkin."
    )


@router.message(Command("guest"))
@router.message(F.text.in_({"🎭 Guest Mode", "🎭 Guest rejimga o'tish"}))
async def cmd_guest(
    message: Message,
    db_user: UserRecord,
    settings: Settings,
    guest_mode_enabled: bool,
) -> None:
    await message.answer(
        _guest_status_text(db_user, settings, guest_mode_enabled),
        reply_markup=get_guest_inline_keyboard(is_guest=db_user.is_guest),
    )


@router.message(Command("register"))
@router.message(F.text == "✅ Ro'yxatdan o'tish")
async def cmd_register(message: Message, scenes: ScenesManager) -> None:
    await scenes.enter(RegistrationScene)


@router.callback_query(MenuCD.filter(F.section == "guest"))
async def cb_guest_menu(
    callback: CallbackQuery,
    db_user: UserRecord,
    settings: Settings,
    guest_mode_enabled: bool,
) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.edit_text(
            _guest_status_text(db_user, settings, guest_mode_enabled),
            reply_markup=get_guest_inline_keyboard(is_guest=db_user.is_guest),
        )


@router.callback_query(GuestCD.filter(F.action == "upgrade"))
async def cb_guest_upgrade(callback: CallbackQuery, scenes: ScenesManager) -> None:
    await scenes.enter(RegistrationScene)


@router.callback_query(GuestCD.filter(F.action == "downgrade"))
async def cb_guest_downgrade(
    callback: CallbackQuery,
    db: Database,
    db_user: UserRecord,
    settings: Settings,
    guest_mode_enabled: bool,
    is_admin: bool,
) -> None:
    if is_admin:
        await callback.answer("Admin roli Guest Mode'ga tushirilmaydi.", show_alert=True)
        return

    await db.set_user_role(db_user.user_id, "guest")
    db_user.role = "guest"
    await callback.answer("Guest Mode yoqildi!")
    if callback.message:
        await callback.message.edit_text(
            _guest_status_text(db_user, settings, guest_mode_enabled),
            reply_markup=get_guest_inline_keyboard(is_guest=True),
        )
        await callback.message.answer(
            "🎭 Menyu Guest Mode uchun yangilandi.",
            reply_markup=get_main_reply_keyboard(is_guest=True, is_admin=False),
        )


@router.callback_query(GuestCD.filter(F.action == "status"))
async def cb_guest_status(
    callback: CallbackQuery,
    db_user: UserRecord,
    settings: Settings,
) -> None:
    if db_user.is_guest:
        text = f"Guest so'rovlar: {db_user.guest_requests_today}/{settings.guest_daily_limit}"
    else:
        text = f"Sizning rolingiz: {db_user.role} (limit yo'q)"
    await callback.answer(text, show_alert=True)
