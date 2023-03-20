# Version 1.1.0 release

import configparser
import mysql.connector as mysql
from aiogram import Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from datetime import datetime

from bot_keyboards import create_cutoff_times_keyboard, create_settings_keyboard
from tools import config_data
from tools import db

router = Router()


class SelectCutoff(StatesGroup):
    waiting_for_cutoff = State()


@router.callback_query(SelectCutoff.waiting_for_cutoff)
async def change_cutoff(call: types.CallbackQuery, state: FSMContext) -> None:
    if "set_cutoff" in call.data:
        call_data_elements = call.data.split("_")
        db_data = config_data.get_db(configparser.ConfigParser())
        db_connect = mysql.connect(user="root",
                                   host=db_data["ip"],
                                   port=db_data["port"],
                                   password=db_data["password"])
        user_data = db.users_get_user(conn=db_connect, user_id=call.from_user.id)
        db.sp_users_configs_update_user(conn=db_connect, sp_uid=user_data["sp_uid"],
                                        prog_cutoff_time=call_data_elements[-1])
        sp_user_data = db.sp_users_get_user(conn=db_connect, sp_uid=user_data["sp_uid"])
        keyboard = await create_settings_keyboard(sp_user_data=sp_user_data)
        try:
            await call.message.edit_text("🚦Settings:", reply_markup=keyboard)
        except TelegramBadRequest:
            pass
        db_connect.close()
    await state.clear()


@router.callback_query()
async def change_config(call: types.CallbackQuery, state: FSMContext) -> None:
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
            if call.data in ["prog_status", "prog_open_shifts", "prog_shift_offers", "bike_status", "prog_cutoff_time"]:
                if call.data == "prog_cutoff_time":
                    keyboard = await create_cutoff_times_keyboard(sp_user_data=sp_user_data)
                    try:
                        await call.message.edit_text("🔥 <b>Select cut-off time</b>\n"
                                                     "<i>What is a cut-off time? Let's imagine it's 2:30 PM now, "
                                                     "cut-off time is 1 hour and you have an auto-booking for some "
                                                     "shift that start's at 3:00 PM. In this case shift will be "
                                                     "ignored.\n"
                                                     "In simple words if shift starts in less than your "
                                                     "cut-off time - bot won't take it.</i>",
                                                     reply_markup=keyboard, parse_mode="HTML")
                        await state.set_state(SelectCutoff.waiting_for_cutoff)
                    except TelegramBadRequest:
                        pass
                else:
                    db.sp_users_configs_update_user(conn=db_connect, sp_uid=user_data["sp_uid"],
                                                    **{call.data: not bool(sp_user_data[call.data])})
                    updated_sp_user_data = db.sp_users_get_user(conn=db_connect, sp_uid=user_data["sp_uid"])
                    keyboard = await create_settings_keyboard(sp_user_data=updated_sp_user_data)
                    try:
                        await call.message.edit_text("🚦Settings:", reply_markup=keyboard)
                    except TelegramBadRequest:
                        pass
                await call.answer()
            elif sp_user_subscription in ["admin", "friend", "premium"]:
                if call.data in ["prog_news", "scooter_status", "car_status"]:
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
