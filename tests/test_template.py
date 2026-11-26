from __future__ import annotations

import pytest
from aiogram.enums import ParseMode
from aiogram.fsm.scene import SceneRegistry

from data.config import Settings
from data.loader import create_bot, create_dispatcher
from handlers import get_root_router
from keyboards.callbacks import AdminCD, FeatureCD, GuestCD, MenuCD
from states import RegistrationScene
from utils.db.database import Database


def test_settings_parses_admins_and_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
    monkeypatch.setenv("ADMINS", "111, 222,333")
    cfg = Settings(_env_file=None)
    assert cfg.admins == [111, 222, 333]
    assert cfg.guest_mode_default is True
    assert cfg.db_path == "data/bot.db"


def test_settings_allows_empty_admins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
    monkeypatch.delenv("ADMINS", raising=False)
    cfg = Settings(_env_file=None)
    assert cfg.admins == []


def test_bot_and_dispatcher_factory(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
    cfg = Settings(_env_file=None)
    bot = create_bot(cfg)
    dp = create_dispatcher()
    dp.include_router(get_root_router())
    registry = SceneRegistry(dp)
    registry.register(RegistrationScene)

    assert bot.default.parse_mode == ParseMode.HTML
    assert "root" in {r.name for r in dp.sub_routers}


def test_callback_data_roundtrip() -> None:
    for cd in (
        MenuCD(section="guest"),
        GuestCD(action="upgrade"),
        FeatureCD(demo="draft"),
        AdminCD(action="toggle_guest"),
    ):
        packed = cd.pack()
        unpacked = type(cd).unpack(packed)
        assert unpacked == cd


@pytest.mark.asyncio
async def test_database_guest_mode_lifecycle() -> None:
    db = Database(":memory:")
    await db.connect()
    try:
        user = await db.get_or_create_user(
            user_id=42,
            username="guest_user",
            full_name="Guest User",
            is_admin=False,
        )
        assert user.is_guest is True
        assert user.role == "guest"

        count = await db.increment_guest_requests(42)
        assert count == 1

        await db.set_user_role(42, "user")
        updated = await db.get_or_create_user(42, "guest_user", "Guest User")
        assert updated.is_registered is True
        assert updated.is_guest is False

        assert await db.is_guest_mode_enabled(default=True) is True
        await db.set_guest_mode_enabled(False)
        assert await db.is_guest_mode_enabled(default=True) is False

        stats = await db.get_stats()
        assert stats.total_users == 1
        assert stats.registered_users == 1
        assert stats.guest_users == 0
    finally:
        await db.close()
