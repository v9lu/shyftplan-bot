# Version 2.0.0 release

import configparser
from aiogram import F, Router, types
from aiogram.filters import Command, Text
from aiogram.fsm.context import FSMContext

import telegram_data
from bot_keyboards import *

owner_data = telegram_data.get(configparser.ConfigParser())
admins = {1630691291}
admins.add(owner_data["account_id"])

router = Router()


@router.message(Command(commands=["start"]), F.from_user.id.in_(admins))
@router.message(Text(text="🎛 Menu"), F.from_user.id.in_(admins))
async def bot_start(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    keyboard = await create_menu_keyboard()
    await message.answer("⭕ Here will be cool statistic soon, but not yet", reply_markup=keyboard)


@router.message(Text(text="♻️ Update shifts"), F.from_user.id.in_(admins))
async def update_shifts(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    keyboard = await create_update_shifts_keyboard()
    await message.answer("⏳ Select an action",
                         reply_markup=keyboard)


@router.callback_query()
async def change_config(call: types.CallbackQuery) -> None:
    config = configparser.ConfigParser()
    config.read("settings.ini")
    if call.data != 'speed':
        reversed_bool = not config.getboolean("PROGRAM_CONFIG", call.data)
        config.set("PROGRAM_CONFIG", call.data, str(reversed_bool))
    else:
        sleeptime_original = config.get("PROGRAM_CONFIG", "sleeptime")
        if sleeptime_original == "5":
            sleeptime_new = "1"
        else:
            sleeptime_new = "5"
        config.set("PROGRAM_CONFIG", "sleeptime", sleeptime_new)

    with open("settings.ini", 'w') as configfile:
        config.write(configfile)

    keyboard = await create_settings_keyboard(config)
    await call.message.edit_text("🚦Settings:", reply_markup=keyboard)
    await call.answer()
