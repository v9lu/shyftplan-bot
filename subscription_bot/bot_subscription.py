# Version 2.1.0 release

import configparser
import mysql.connector as mysql
import random
import string
from aiogram import F, Router, types
from aiogram.filters import Command, Text, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import LabeledPrice, ReplyKeyboardRemove

import bot_keyboards
import config_data
import db

admins = {1630691291}
STRIPE_TOKEN = "284685063:TEST:OWI2MzFmMjMzMDhh"  # TEST
router = Router()


@router.message(Command(commands=["start"]))
async def bot_start(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    if message.from_user.id in admins:
        keyboard = await bot_keyboards.create_menu_keyboard(True)

    else:
        keyboard = await bot_keyboards.create_menu_keyboard(False)
    await message.answer("💳 Plans:\n\n"
                         "💎 Premium 30 day's\n"
                         "🔹 Standard 30 day's\n"
                         "🆓 Trial 7 day's [FREE]", reply_markup=keyboard)


@router.message(Text(text="🔑 Create key"), F.from_user.id.in_(admins))
async def create_key_btn(message: types.Message, state: FSMContext) -> None:
    keyboard = await bot_keyboards.create_menu_keyboard(True)
    await message.answer("🔑 Key generator:\n"
                         "1. Type [standard/premium].\n"
                         "2. Days [15]\n\n"
                         "Usage: /key <b>standard</b> <b>30</b>", reply_markup=keyboard, parse_mode="HTML")


@router.message(Text(text="🚫 Deactivate key"), F.from_user.id.in_(admins))
async def deactivate_key_btn(message: types.Message, state: FSMContext) -> None:
    keyboard = await bot_keyboards.create_menu_keyboard(True)
    await message.answer("🚫 Key deactivator:\n\n"
                         "Usage: /deactivate <b>key</b>", reply_markup=keyboard, parse_mode="HTML")


@router.message(Command(commands=["key"]), F.from_user.id.in_(admins))
async def keygen(message: types.Message, command: CommandObject, state: FSMContext) -> None:
    if command.args:
        parameters = command.args.split()
        if len(parameters) == 2:
            key_type = parameters[0]
            if key_type == "standard" or key_type == "premium":
                try:
                    key_days = int(parameters[1])
                    database_data = config_data.get_db(configparser.ConfigParser())
                    letters = string.ascii_lowercase + string.digits
                    key = ''.join(random.choice(letters) for i in range(16))
                    db.add_key(mysql.connect(user="root",
                                             host=database_data["ip"],
                                             password=database_data["password"],
                                             database="keys_db"),
                               key, key_type, key_days)
                    if key_type == "premium":
                        await message.reply(f"🔑 <b>Key</b>: <code>{key}</code>\n"
                                            f"     ├─ 💎 <b>Type: <code>Premium</code>\n"
                                            f"     └─ 📅 <b>Days: <code>{key_days}</code>", parse_mode="HTML")
                    elif key_type == "standard":
                        await message.reply(f"🔑 <b>Key</b>: <code>{key}</code>\n"
                                            f"     ├─ 🔹 <b>Type</b>: <code>Standard</code>\n"
                                            f"     └─ 📅 <b>Days</b>: <code>{key_days}</code>", parse_mode="HTML")
                except ValueError:
                    pass


@router.message(Command(commands=["deactivate"]), F.from_user.id.in_(admins))
async def key_deactivator(message: types.Message, command: CommandObject, state: FSMContext) -> None:
    if command.args:
        parameters = command.args.split()
        if len(parameters) == 1:
            database_data = config_data.get_db(configparser.ConfigParser())
            key = parameters[0]
            db.remove_key(mysql.connect(user="root",
                                        host=database_data["ip"],
                                        password=database_data["password"],
                                        database="keys_db"),
                          key)
            await message.reply("✅ Key was successfully removed!")


@router.message(Text(text="💎 30 day's premium"))
async def sub_30_prem(message: types.Message, state: FSMContext) -> None:
    await message.answer_invoice(title="📅 30 day subscription (premium)",
                                 description="⚠️ In order to prevent JUSH account blocking, I'm not recommend to "
                                             "inform someone about purchase of a subscription.",
                                 payload=f"{message.from_user.id}:sub_premium:30d",
                                 provider_token=STRIPE_TOKEN,
                                 currency="PLN",
                                 prices=[LabeledPrice(label="💎 Premium 30 day's", amount=30000)],
                                 max_tip_amount=10000,
                                 suggested_tip_amounts=[500, 1000, 2000],
                                 photo_url="https://i.imgur.com/aNKX0gH.jpeg",
                                 need_name=True)


@router.message(Text(text="🔹 30 day's standard"))
async def sub_30(message: types.Message, state: FSMContext) -> None:
    await message.answer_invoice(title="📅 30 day subscription (standard)",
                                 description="⚠️ In order to prevent JUSH account blocking, I'm not recommend to "
                                             "inform someone about purchase of a subscription.",
                                 payload=f"{message.from_user.id}:sub_standard:30d",
                                 provider_token=STRIPE_TOKEN,
                                 currency="PLN",
                                 prices=[LabeledPrice(label="🔹 Standard 30 day's", amount=10000)],
                                 max_tip_amount=10000,
                                 suggested_tip_amounts=[500, 1000, 2000],
                                 photo_url="https://i.imgur.com/aNKX0gH.jpeg",
                                 need_name=True)


@router.pre_checkout_query()
async def pre_checkout(callback: types.PreCheckoutQuery):
    await callback.answer(True)
