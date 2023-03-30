# Version 2.0.8 release

import asyncio
import configparser
import logging
from aiogram import Bot, Dispatcher

import bot_common
import bot_authorization
import bot_exploit
import bot_update_shifts
import bot_keys
import bot_newsletter
import bot_subscription
import bot_settings
from tools import config_data


async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=config_data.get_bot(configparser.ConfigParser())["bot_token"])
    dp = Dispatcher()

    dp.include_router(bot_common.router)
    dp.include_router(bot_authorization.router)
    dp.include_router(bot_exploit.router)
    dp.include_router(bot_update_shifts.router)
    dp.include_router(bot_keys.router)
    dp.include_router(bot_newsletter.router)
    dp.include_router(bot_subscription.router)
    dp.include_router(bot_settings.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


asyncio.run(main())
