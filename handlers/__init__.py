from __future__ import annotations

from aiogram import Router

from .errors import router as errors_router
from .groups import groups_router
from .users import (
    admin_router,
    features_router,
    guest_queries_router,
    guest_router,
    inline_router,
    start_router,
)


def get_root_router() -> Router:
    """Assemble and return the root application router in priority order."""
    root = Router(name="root")
    root.include_routers(
        admin_router,
        guest_queries_router,
        guest_router,
        features_router,
        start_router,
        inline_router,
        groups_router,
        errors_router,
    )
    return root
