# Version 2.3.2 release

import configparser
import mysql.connector as mysql
import random
import string
from aiogram import Router, types
from aiogram.filters import Text
from aiogram.fsm.context import FSMContext
from aiogram.types import LabeledPrice

from bot_keyboards import create_menu_keyboard
from tools import config_data
from tools import db

STRIPE_TOKEN = config_data.get_bot(configparser.ConfigParser())["pay_token"]
router = Router()


@router.message(Text(text="💎 30 day's premium"))
async def premium_30(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer_invoice(title="📅 30 day subscription (premium)",
                                 description="⚠️ In order to prevent JUSH account blocking, I'm not recommend to "
                                             "inform someone about purchase of a subscription.",
                                 payload=f"premium:30",
                                 provider_token=STRIPE_TOKEN,
                                 currency="PLN",
                                 prices=[LabeledPrice(label="💎 Premium 30 day's", amount=30000)],
                                 max_tip_amount=10000,
                                 suggested_tip_amounts=[500, 1000, 2000],
                                 photo_url="https://i.imgur.com/aNKX0gH.jpeg",
                                 need_name=True)


@router.message(Text(text="🔹 30 day's standard"))
async def standard_30(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer_invoice(title="📅 30 day subscription (standard)",
                                 description="⚠️ In order to prevent JUSH account blocking, I'm not recommend to "
                                             "inform someone about purchase of a subscription.",
                                 payload=f"standard:30",
                                 provider_token=STRIPE_TOKEN,
                                 currency="PLN",
                                 prices=[LabeledPrice(label="🔹 Standard 30 day's", amount=10000)],
                                 max_tip_amount=10000,
                                 suggested_tip_amounts=[500, 1000, 2000],
                                 photo_url="https://i.imgur.com/aNKX0gH.jpeg",
                                 need_name=True)


@router.message(Text(text="🆓 7 day's trial"))
async def trial_7(message: types.Message, state: FSMContext):
    await state.clear()
    db_data = config_data.get_db(configparser.ConfigParser())
    db_connect = mysql.connect(user="root",
                               host=db_data["ip"],
                               port=db_data["port"],
                               password=db_data["password"])
    user_data = db.users_get_user(conn=db_connect, user_id=message.from_user.id)
    if user_data["sp_uid"]:
        sp_user_data = db.sp_users_get_user(conn=db_connect, sp_uid=user_data["sp_uid"])
        keyboard = await create_menu_keyboard(sp_user_data=sp_user_data)
        if not sp_user_data["used_trial_btn"]:
            db.sp_users_subscriptions_update_user(conn=db_connect, sp_uid=user_data["sp_uid"], used_trial_btn=True)
            letters = string.ascii_lowercase + string.digits
            key = ''.join(random.choice(letters) for i in range(16))
            db.keys_add_key(conn=db_connect, key=key, key_type="trial", key_days=7)
            await message.reply(f"🔑 <b>Key</b>: <code>{key}</code>\n"
                                "     ├─ 🆓 <b>Type</b>: <code>Trial</code>\n"
                                "     └─ 📅 <b>Days</b>: <code>7</code>",
                                parse_mode="HTML", reply_markup=keyboard)
        else:
            await message.answer("🚫 You have already got the trial key!", reply_markup=keyboard)
    else:
        keyboard = await create_menu_keyboard()
        await message.answer("🚫 You aren't authorized! For a login, use a special button or /auth command",
                             reply_markup=keyboard)
    db_connect.close()


@router.pre_checkout_query()
async def pre_checkout(callback: types.PreCheckoutQuery):
    await callback.answer(True)


@router.message()
async def successful_payment(message: types.Message, state: FSMContext):
    await state.clear()
    db_data = config_data.get_db(configparser.ConfigParser())
    db_connect = mysql.connect(user="root",
                               host=db_data["ip"],
                               port=db_data["port"],
                               password=db_data["password"])
    invoice_payload = message.successful_payment.invoice_payload.split(":")
    key_type = invoice_payload[0]
    key_days = int(invoice_payload[1])
    if key_type == "standard" or key_type == "premium":
        letters = string.ascii_lowercase + string.digits
        key = ''.join(random.choice(letters) for i in range(16))
        db.keys_add_key(conn=db_connect, key=key, key_type=key_type, key_days=key_days)
        user_data = db.users_get_user(conn=db_connect, user_id=message.from_user.id)
        if user_data["sp_uid"]:
            sp_user_data = db.sp_users_get_user(conn=db_connect, sp_uid=user_data["sp_uid"])
            keyboard = await create_menu_keyboard(sp_user_data=sp_user_data)
        else:
            keyboard = create_menu_keyboard()
        if key_type == "premium":
            await message.reply(f"🔑 <b>Key</b>: <code>{key}</code>\n"
                                f"     ├─ 💎 <b>Type</b>: <code>Premium</code>\n"
                                f"     └─ 📅 <b>Days</b>: <code>{key_days}</code>",
                                parse_mode="HTML", reply_markup=keyboard)
        elif key_type == "standard":
            await message.reply(f"🔑 <b>Key</b>: <code>{key}</code>\n"
                                f"     ├─ 🔹 <b>Type</b>: <code>Standard</code>\n"
                                f"     └─ 📅 <b>Days</b>: <code>{key_days}</code>",
                                parse_mode="HTML", reply_markup=keyboard)
    db_connect.close()
