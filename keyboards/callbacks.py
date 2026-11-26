from __future__ import annotations

from aiogram.filters.callback_data import CallbackData


class MenuCD(CallbackData, prefix="menu"):
    """Navigation callback data for main menu sections."""

    section: str


class GuestCD(CallbackData, prefix="guest"):
    """Actions related to Guest Mode."""

    action: str


class FeatureCD(CallbackData, prefix="feat"):
    """Actions for aiogram 3.34 / Bot API 10.5 feature demos."""

    demo: str


class AdminCD(CallbackData, prefix="admin"):
    """Admin panel actions."""

    action: str


class InlineCD(CallbackData, prefix="inl"):
    """Callback actions for inline-sent messages (uses inline_message_id)."""

    action: str

