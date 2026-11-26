from __future__ import annotations

from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_main_reply_keyboard(is_guest: bool = True, is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Build a clean, role-aware ReplyKeyboard."""
    builder = ReplyKeyboardBuilder()
    builder.button(text="👤 Profil")
    builder.button(text="🚀 Bot API Features")
    if is_guest:
        builder.button(text="🎭 Guest Mode")
        builder.button(text="✅ Ro'yxatdan o'tish")
    else:
        builder.button(text="🎭 Guest rejimga o'tish")
    if is_admin:
        builder.button(text="🛠 Admin Panel")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True, input_field_placeholder="Bo'limni tanlang...")
