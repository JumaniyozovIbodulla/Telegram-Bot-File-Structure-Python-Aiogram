from asyncio import run
from logging import basicConfig, INFO
from sys import stdout

import handlers, utils 
from data.config import BOT_TOKEN
from data.loader import dp, bot
from utils.misc.helpers import start_bot, stop_bot



async def main() -> None:
    dp.startup.register(start_bot)
    dp.shutdown.register(stop_bot)

    await dp.start_polling(bot)

if __name__ == "__main__":
    basicConfig(level=INFO, stream=stdout)
    run(main())