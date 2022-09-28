# Version 2.0.0 release

import asyncio
import configparser
import logging
from aiogram import Bot, Dispatcher

import bot_common
import bot_authorization
import bot_update_shifts
import telegram_data

owner_data = telegram_data.get(configparser.ConfigParser())
TG_BOT_API_TOKEN = owner_data["bot_token"]


async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=TG_BOT_API_TOKEN)
    dp = Dispatcher()

    dp.include_router(bot_common.router)
    dp.include_router(bot_authorization.router)
    dp.include_router(bot_update_shifts.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


asyncio.run(main())
