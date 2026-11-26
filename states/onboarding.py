from __future__ import annotations

from aiogram import F
from aiogram.fsm.scene import Scene, on
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.db.database import Database


class FeedbackStates(StatesGroup):
    """Standard FSM StatesGroup example for collecting user feedback."""

    waiting_for_text = State()


class RegistrationScene(Scene, state="registration"):
    """
    Modern aiogram 3.x Scenes Wizard for upgrading a Guest Mode user
    into a full Registered User.
    """

    @on.message.enter()
    async def on_enter(self, message: Message) -> None:
        builder = InlineKeyboardBuilder()
        builder.button(text="❌ Bekor qilish", callback_data="scene:cancel")
        await message.answer(
            "📝 <b>Ro'yxatdan o'tish (Scenes Wizard)</b>\n\n"
            "To'liq foydalanuvchi rejimiga o'tish uchun ismingizni kiriting "
            "(yoki /cancel yozing):",
            reply_markup=builder.as_markup(),
        )

    @on.callback_query.enter()
    async def on_enter_callback(self, callback: CallbackQuery) -> None:
        await callback.answer()
        if callback.message:
            builder = InlineKeyboardBuilder()
            builder.button(text="❌ Bekor qilish", callback_data="scene:cancel")
            await callback.message.answer(
                "📝 <b>Ro'yxatdan o'tish (Scenes Wizard)</b>\n\n"
                "To'liq foydalanuvchi rejimiga o'tish uchun ismingizni kiriting:",
                reply_markup=builder.as_markup(),
            )

    @on.callback_query(F.data == "scene:cancel")
    async def on_cancel_callback(self, callback: CallbackQuery) -> None:
        await callback.answer("Bekor qilindi")
        if callback.message:
            await callback.message.edit_text("❌ Ro'yxatdan o'tish bekor qilindi. Siz hali ham Guest Mode'dasiz.")
        await self.wizard.exit()

    @on.message(F.text == "/cancel")
    async def on_cancel_message(self, message: Message) -> None:
        await message.answer("❌ Ro'yxatdan o'tish bekor qilindi.")
        await self.wizard.exit()

    @on.message(F.text)
    async def process_name(self, message: Message, db: Database) -> None:
        name = (message.text or "").strip()
        if len(name) < 2:
            await message.answer("⚠️ Ism kamida 2 ta belgidan iborat bo'lishi kerak. Qaytadan kiriting:")
            return

        if message.from_user is not None:
            await db.set_user_role(message.from_user.id, "user")

        await message.answer(
            f"🎉 Tabriklaymiz, <b>{name}</b>!\n"
            "Siz endi <b>To'liq foydalanuvchi</b> rejimidasiz. "
            "Cheklovlar olib tashlandi va barcha funksiyalar ochildi."
        )
        await self.wizard.exit()
