from __future__ import annotations

import logging

from aiogram import Router
from aiogram.types import ErrorEvent

logger = logging.getLogger(__name__)

router = Router(name="global_errors")


@router.errors()
async def global_error_handler(event: ErrorEvent) -> bool:
    """Catch unhandled handler exceptions cleanly so polling never crashes."""
    logger.exception(
        "Unhandled exception while processing update %s: %s",
        event.update.update_id,
        event.exception,
        exc_info=event.exception,
    )
    return True
