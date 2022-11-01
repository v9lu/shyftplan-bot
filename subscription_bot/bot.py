# Version 2.0.1 release

import asyncio
import configparser
import logging
from aiogram import Bot, Dispatcher

import bot_subscription
import config_data


async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=config_data.get_bot_token(configparser.ConfigParser()))
    dp = Dispatcher()
    dp.include_router(bot_subscription.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


asyncio.run(main())
