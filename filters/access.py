from __future__ import annotations

from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject

from data.config import Settings
from utils.db.database import UserRecord


class IsAdminFilter(BaseFilter):
    """Matches only configured admins or users with role='admin'."""

    async def __call__(
        self,
        event: TelegramObject,
        is_admin: bool = False,
        settings: Settings | None = None,
    ) -> bool:
        if is_admin:
            return True
        from_user = getattr(event, "from_user", None)
        if settings is not None and from_user is not None:
            return from_user.id in settings.admins
        return False


class IsGuestFilter(BaseFilter):
    """Matches users currently in Guest Mode."""

    async def __call__(
        self,
        event: TelegramObject,
        db_user: UserRecord | None = None,
    ) -> bool:
        return db_user is not None and db_user.is_guest


class IsRegisteredFilter(BaseFilter):
    """Matches registered users (role='user' or 'admin')."""

    async def __call__(
        self,
        event: TelegramObject,
        db_user: UserRecord | None = None,
    ) -> bool:
        return db_user is not None and db_user.is_registered
