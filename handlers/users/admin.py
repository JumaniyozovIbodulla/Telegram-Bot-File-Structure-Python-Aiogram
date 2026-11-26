from __future__ import annotations

from aiogram import Bot, F, Router, html
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from filters.access import IsAdminFilter
from keyboards.callbacks import AdminCD, MenuCD
from keyboards.inline import get_admin_inline_keyboard
from utils.db.database import Database
from utils.misc.bot_settings import apply_bot_settings

router = Router(name="users_admin")
router.message.filter(F.chat.type == ChatType.PRIVATE, IsAdminFilter())
router.callback_query.filter(IsAdminFilter())


async def _admin_panel_text(db: Database, guest_mode_enabled: bool) -> str:
    stats = await db.get_stats()
    status = "🟢 Yoqilgan" if guest_mode_enabled else "🔴 O'chirilgan"
    return (
        "🛠 <b>Admin Panel</b>\n\n"
        f"• <b>Global Guest Mode:</b> {status}\n"
        f"• <b>Jami foydalanuvchilar:</b> {stats.total_users}\n"
        f"• <b>Guest Mode'dagilar:</b> {stats.guest_users}\n"
        f"• <b>Ro'yxatdan o'tganlar:</b> {stats.registered_users}\n"
        f"• <b>Bloklanganlar:</b> {stats.banned_users}"
    )


@router.message(Command("admin"))
@router.message(F.text == "🛠 Admin Panel")
async def cmd_admin(
    message: Message,
    db: Database,
    guest_mode_enabled: bool,
) -> None:
    await message.answer(
        await _admin_panel_text(db, guest_mode_enabled),
        reply_markup=get_admin_inline_keyboard(guest_mode_enabled),
    )


@router.callback_query(MenuCD.filter(F.section == "admin"))
async def cb_admin_menu(
    callback: CallbackQuery,
    db: Database,
    guest_mode_enabled: bool,
) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.edit_text(
            await _admin_panel_text(db, guest_mode_enabled),
            reply_markup=get_admin_inline_keyboard(guest_mode_enabled),
        )


@router.callback_query(AdminCD.filter(F.action == "toggle_guest"))
async def cb_toggle_guest(
    callback: CallbackQuery,
    db: Database,
    guest_mode_enabled: bool,
) -> None:
    new_state = not guest_mode_enabled
    await db.set_guest_mode_enabled(new_state)
    await callback.answer(
        "Guest Mode yoqildi!" if new_state else "Guest Mode o'chirildi!",
        show_alert=True,
    )
    if callback.message:
        await callback.message.edit_text(
            await _admin_panel_text(db, new_state),
            reply_markup=get_admin_inline_keyboard(new_state),
        )


@router.callback_query(AdminCD.filter(F.action == "stats"))
async def cb_admin_stats(
    callback: CallbackQuery,
    db: Database,
    guest_mode_enabled: bool,
) -> None:
    await callback.answer("Yangilandi")
    if callback.message:
        await callback.message.edit_text(
            await _admin_panel_text(db, guest_mode_enabled),
            reply_markup=get_admin_inline_keyboard(guest_mode_enabled),
        )


@router.callback_query(AdminCD.filter(F.action == "bot_settings"))
async def cb_admin_bot_settings(callback: CallbackQuery, bot: Bot) -> None:
    ok, err = await apply_bot_settings(
        bot,
        supports_guest_queries=True,
    )
    if ok:
        await callback.answer("✅ set_my_settings muvaffaqiyatli qo'llandi!", show_alert=True)
    else:
        await callback.answer(
            f"⚠️ set_my_settings javobi: {err}",
            show_alert=True,
        )
        if callback.message:
            await callback.message.answer(
                f"ℹ️ <code>bot.set_my_settings(supports_guest_queries=True)</code> natijasi:\n"
                f"<code>{html.quote(err or 'Unknown error')}</code>"
            )
