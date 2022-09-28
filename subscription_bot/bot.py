# Version 2.0.0 release

import asyncio
import logging
# import mysql.connector as mysql
from aiogram import Bot, Dispatcher

import bot_subscription
# import server_db

TG_BOT_API_TOKEN = "5510496973:AAHc2M_09Zk3K5MppSawIrgDg33DQWlqbuE"


async def main():
    # server_db.initialization(mysql.connect(host="92.118.150.6", user="root", password="1745375"))
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=TG_BOT_API_TOKEN)
    dp = Dispatcher()
    dp.include_router(bot_subscription.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


asyncio.run(main())
