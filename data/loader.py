from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage, SimpleEventIsolation

from data.config import Settings, get_settings


def create_bot(settings: Settings | None = None) -> Bot:
    """Create and configure the Bot instance using DefaultBotProperties."""
    cfg = settings or get_settings()
    return Bot(
        token=cfg.bot_token.get_secret_value(),
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            link_preview_is_disabled=True,
        ),
    )


def create_dispatcher() -> Dispatcher:
    """Create the Dispatcher with MemoryStorage and event isolation for FSM/Scenes."""
    return Dispatcher(
        storage=MemoryStorage(),
        events_isolation=SimpleEventIsolation(),
    )
