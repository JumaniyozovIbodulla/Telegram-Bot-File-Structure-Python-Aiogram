from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from keyboards.callbacks import AdminCD, FeatureCD, GuestCD, MenuCD


def get_start_inline_keyboard(is_guest: bool = True, is_admin: bool = False) -> InlineKeyboardMarkup:
    """Main inline menu shown on /start and /menu."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🎭 Guest Mode", callback_data=MenuCD(section="guest"))
    builder.button(text="🚀 Bot API 10.5 Features", callback_data=MenuCD(section="features"))
    builder.button(text="👤 Profil", callback_data=MenuCD(section="profile"))
    if is_guest:
        builder.button(text="✅ Ro'yxatdan o'tish", callback_data=GuestCD(action="upgrade"))
    if is_admin:
        builder.button(text="🛠 Admin Panel", callback_data=MenuCD(section="admin"))
    builder.adjust(2)
    return builder.as_markup()


def get_guest_inline_keyboard(is_guest: bool) -> InlineKeyboardMarkup:
    """Inline controls for Guest Mode."""
    builder = InlineKeyboardBuilder()
    if is_guest:
        builder.button(
            text="✅ To'liq rejimga o'tish (Register)",
            callback_data=GuestCD(action="upgrade"),
        )
    else:
        builder.button(
            text="🎭 Guest Mode'ga qaytish (Demo)",
            callback_data=GuestCD(action="downgrade"),
        )
    builder.button(text="📊 Kunlik limitni ko'rish", callback_data=GuestCD(action="status"))
    builder.button(text="⬅️ Bosh menyu", callback_data=MenuCD(section="home"))
    builder.adjust(1)
    return builder.as_markup()


def get_features_inline_keyboard() -> InlineKeyboardMarkup:
    """Interactive showcase of aiogram 3.34.0 & Telegram Bot API 10.5 features."""
    builder = InlineKeyboardBuilder()
    builder.button(text="⚡️ Draft Streaming (API 10.x)", callback_data=FeatureCD(demo="draft"))
    builder.button(text="🎉 Message Effect + Reaction", callback_data=FeatureCD(demo="effect"))
    builder.button(text="⏳ ChatActionSender (typing)", callback_data=FeatureCD(demo="typing"))
    builder.button(text="📖 Expandable Quote & Spoiler", callback_data=FeatureCD(demo="formatting"))
    builder.button(text="☑️ Checklist API (Business)", callback_data=FeatureCD(demo="checklist"))
    builder.button(text="🤖 BotFullInfo (API 10.5)", callback_data=FeatureCD(demo="botinfo"))
    builder.button(text="⬅️ Bosh menyu", callback_data=MenuCD(section="home"))
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()


def get_admin_inline_keyboard(guest_mode_enabled: bool) -> InlineKeyboardMarkup:
    """Admin panel controls."""
    builder = InlineKeyboardBuilder()
    toggle_label = "🔴 Guest Mode'ni o'chirish" if guest_mode_enabled else "🟢 Guest Mode'ni yoqish"
    builder.button(text=toggle_label, callback_data=AdminCD(action="toggle_guest"))
    builder.button(text="📊 Statistika", callback_data=AdminCD(action="stats"))
    builder.button(text="⚙️ Bot API 10.5 Settings", callback_data=AdminCD(action="bot_settings"))
    builder.button(text="⬅️ Bosh menyu", callback_data=MenuCD(section="home"))
    builder.adjust(1)
    return builder.as_markup()
