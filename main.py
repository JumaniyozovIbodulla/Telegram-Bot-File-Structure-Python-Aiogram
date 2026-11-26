from __future__ import annotations

import asyncio
import logging
import sys

from aiogram.fsm.scene import SceneRegistry

from data.config import get_settings
from data.loader import create_bot, create_dispatcher
from handlers import get_root_router
from middlewares import ThrottlingMiddleware, UserContextMiddleware
from states import RegistrationScene
from utils.db.database import Database
from utils.misc.helpers import on_shutdown, on_startup


async def main() -> None:
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        stream=sys.stdout,
    )

    db = Database(db_path=settings.db_path)
    bot = create_bot(settings)
    dp = create_dispatcher()

    # Register middlewares (UserContext first so Throttling knows is_guest / is_admin)
    user_ctx_mw = UserContextMiddleware(db=db, settings=settings)
    throttle_mw = ThrottlingMiddleware(settings=settings)
    dp.message.middleware(user_ctx_mw)
    dp.callback_query.middleware(user_ctx_mw)
    dp.message.middleware(throttle_mw)
    dp.callback_query.middleware(throttle_mw)

    # Register routers & FSM Scenes
    dp.include_router(get_root_router())
    scene_registry = SceneRegistry(dp)
    scene_registry.register(RegistrationScene)

    # Lifecycle hooks
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
            db=db,
            settings=settings,
        )
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped by user.")
