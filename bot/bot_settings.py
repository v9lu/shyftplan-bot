# Version 1.0.0 release

import configparser
import mysql.connector as mysql
from aiogram import Router, types
from aiogram.exceptions import TelegramBadRequest
from datetime import datetime

from bot_keyboards import create_settings_keyboard
from tools import config_data
from tools import db

router = Router()


@router.callback_query()
async def change_config(call: types.CallbackQuery) -> None:
    db_data = config_data.get_db(configparser.ConfigParser())
    db_connect = mysql.connect(user="root",
                               host=db_data["ip"],
                               port=db_data["port"],
                               password=db_data["password"])
    user_data = db.users_get_user(conn=db_connect, user_id=call.from_user.id)
    sp_user_data = db.sp_users_get_user(conn=db_connect, sp_uid=user_data["sp_uid"])
    sp_user_subscription = sp_user_data["subscription"]
    if sp_user_data["subscription"] and sp_user_data["expire"]:
        if datetime.now() < sp_user_data["expire"]:
            if call.data == "prog_status" or call.data == "prog_open_shifts" or call.data == "prog_shift_offers" or \
               call.data == "bike_status":
                db.sp_users_configs_update_user(conn=db_connect, sp_uid=user_data["sp_uid"],
                                                **{call.data: not bool(sp_user_data[call.data])})
                updated_sp_user_data = db.sp_users_get_user(conn=db_connect, sp_uid=user_data["sp_uid"])
                keyboard = await create_settings_keyboard(sp_user_data=updated_sp_user_data)
                try:
                    await call.message.edit_text("🚦Settings:", reply_markup=keyboard)
                except TelegramBadRequest:
                    pass
                await call.answer()
            elif sp_user_subscription == 'premium' or sp_user_subscription == "friend" or sp_user_subscription == "admin":
                if call.data == "prog_news" or call.data == "scooter_status" or call.data == "car_status":
                    db.sp_users_configs_update_user(conn=db_connect, sp_uid=user_data["sp_uid"],
                                                    **{call.data: not bool(sp_user_data[call.data])})
                else:
                    if sp_user_data["prog_sleep"] == 5.0:
                        db.sp_users_configs_update_user(conn=db_connect, sp_uid=user_data["sp_uid"],
                                                        **{call.data: 1.0})
                    elif sp_user_data["prog_sleep"] == 1.0:
                        db.sp_users_configs_update_user(conn=db_connect, sp_uid=user_data["sp_uid"],
                                                        **{call.data: 0.3})
                    elif sp_user_data["prog_sleep"] == 0.3:
                        db.sp_users_configs_update_user(conn=db_connect, sp_uid=user_data["sp_uid"],
                                                        **{call.data: 5.0})
                updated_sp_user_data = db.sp_users_get_user(conn=db_connect, sp_uid=user_data["sp_uid"])
                keyboard = await create_settings_keyboard(sp_user_data=updated_sp_user_data)
                try:
                    await call.message.edit_text("🚦Settings:", reply_markup=keyboard)
                except TelegramBadRequest:
                    pass
                await call.answer()
            else:
                await call.answer(text="💎 Only for premium subscription!")
        else:
            await call.answer(text="❌ You don't have a subscription!")
    else:
        await call.answer(text="❌ You don't have a subscription!")
    db_connect.close()
