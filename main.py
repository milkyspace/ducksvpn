import json
import string
import subprocess
import sqlite3
import time
import aiosqlite
import buttons
import dbworker
import emoji as e
import asyncio
import threading
import requests
import logging
import os
from datetime import datetime
from telebot import TeleBot
from pyqiwip2p import QiwiP2P
from pyqiwip2p import AioQiwiP2P
from telebot import asyncio_filters
from telebot.async_telebot import AsyncTeleBot
from telebot import types
from telebot.asyncio_storage import StateMemoryStorage
from telebot.asyncio_handler_backends import State, StatesGroup
from buttons import main_buttons
from dbworker import User
from dotenv import load_dotenv, dotenv_values

load_dotenv()

CONFIG = {
    "admin_tg_id": [int(os.getenv("ADMIN_TG_ID_1")), int(os.getenv("ADMIN_TG_ID_2"))],
    "one_month_cost": float(os.getenv("ONE_MONTH_COST")),
    "trial_period": os.getenv("TRIAL_PERIOD"),
    "perc_1": float(os.getenv("PERC_1")),
    "perc_3": float(os.getenv("PERC_3")),
    "perc_6": float(os.getenv("PERC_6")),
    "perc_12": float(os.getenv("PERC_12")),
    "UTC_time": int(os.getenv("UTC_TIME")),
    "tg_token": os.getenv("TG_TOKEN"),
    "tg_shop_token": os.getenv("TG_SHOP_TOKEN"),
    "base_url": os.getenv("BASE_URL"),
    "password_to_amnezia": os.getenv("PASSWORD_TO_AMNEZIA"),
    "count_free_from_referrer": int(os.getenv("COUNT_FREE_FROM_REFERRER")),
    "bot_name": os.getenv("BOT_NAME"),
}
dbworker.CONFIG = CONFIG
buttons.CONFIG = CONFIG

with open("texts.json", encoding="utf-8") as file_handler:
    text_mess = json.load(file_handler)
    texts_for_bot = text_mess

DBCONNECT = "data.sqlite"
BOTAPIKEY = CONFIG["tg_token"]
BASE_URL = CONFIG["base_url"]
PASSWORD = CONFIG["password_to_amnezia"]

bot = AsyncTeleBot(CONFIG["tg_token"], state_storage=StateMemoryStorage())

class MyStates(StatesGroup):
    findUserViaId = State()
    prepareUserForSendMessage = State()
    sendMessageToUser = State()
    sendMessageToAllInactiveUser = State()
    editUser = State()
    editUserResetTime = State()

    UserAddTimeDays = State()
    UserAddTimeHours = State()
    UserAddTimeMinutes = State()
    UserAddTimeApprove = State()

    AdminNewUser = State()

async def getTrialButtons():
    trialButtons = types.InlineKeyboardMarkup(row_width = 1)
    trialButtons.add(
        types.InlineKeyboardButton(e.emojize(":mobile_phone: iOS (iPhone, iPad)"), callback_data="Init:iPhone"),
        types.InlineKeyboardButton(e.emojize(":mobile_phone: Android"), callback_data="Init:Android"),
        types.InlineKeyboardButton(e.emojize(":laptop: ПК (Windows, MacOS)"), callback_data="Init:PC")
    )
    return trialButtons

async def sendPayMessage(chatId):
    Butt_payment = types.InlineKeyboardMarkup()

    if chatId in CONFIG["admin_tg_id"]:
        Butt_payment.add(
                types.InlineKeyboardButton(e.emojize(f"Проверка оплаты: {int(getCostBySale(100))} руб."),
                                           callback_data="BuyMonth:100"))
    Butt_payment.add(
        types.InlineKeyboardButton(e.emojize(f"1 месяц: {int(getCostBySale(1))} руб."),
                                   callback_data="BuyMonth:1"))
    Butt_payment.add(
        types.InlineKeyboardButton(e.emojize(f"3 месяца: {int(getCostBySale(3))} руб. (-{getSale(3)}%)"),
                                   callback_data="BuyMonth:3"))
    Butt_payment.add(
        types.InlineKeyboardButton(e.emojize(f"6 месяцев: {int(getCostBySale(6))} руб. (-{getSale(6)}%)"),
                                   callback_data="BuyMonth:6"))
    Butt_payment.add(
        types.InlineKeyboardButton(e.emojize(f"1 год: {int(getCostBySale(12))} руб. (-{getSale(12)}%)"),
                                   callback_data="BuyMonth:12"))
    await bot.send_message(chatId,
                           "<b>Оплатить подписку можно с помощью банковской карты</b>\n\nОплата производится официально через сервис ЮКасса\nМы не сохраняем, не передаем и не имеем доступа к данным карт, используемых для оплаты\n\nВыберите период, на который хотите приобрести подписку:",
                           reply_markup=Butt_payment, parse_mode="HTML")

async def sendConfig(chatId):
    user_dat = await User.GetInfo(chatId)
    if user_dat.trial_subscription == False:
        clients = requests.get(f"{BASE_URL}/wireguard/client", headers={"password": f"{PASSWORD}"})
        trialButtons = await getTrialButtons()
        await bot.send_message(chat_id=chatId, text=f"Пожалуйста, выберите тип устройства, для которого нужна инструкция для подключения:", parse_mode="HTML", reply_markup=trialButtons)
    else:
        await bot.send_message(chat_id=chatId, text="Для этого необходимо оплатить подписку", reply_markup=await main_buttons(user_dat))
        await sendPayMessage(chatId)

async def sendConfigAndInstructions(chatId, device='iPhone'):
    user_dat = await User.GetInfo(chatId)
    clients = requests.get(f"{BASE_URL}/wireguard/client", headers={"password": f"{PASSWORD}"})
    for client in clients.json():
        if str(user_dat.tgid) == client.get('name', 0):
            response = requests.get(f"{BASE_URL}/wireguard/client/{client.get('id', 0)}/configuration", headers={"Content-Type": "application/json", "password": f"{PASSWORD}"})
            content_disposition = response.headers["Content-Disposition"]
            filename = f"data/{content_disposition.split('filename=')[1]}"
            with open(filename, "wb") as code:
                code.write(response.content)
            configFull = open(filename, 'rb')

            instructionIPhone = f"<b>Подключение VPN DUCKS на iOS</b>\n\r\n\r1. Установите приложение <a href='https://apps.apple.com/ru/app/amneziavpn/id1600529900'>AmneziaVPN для iOS из AppStore</a>\n\r2. Откройте прикрепленный выше файл конфигурации vpnducks_{str(user_dat.tgid)}.conf\n\r3. Нажмите на иконку поделиться в левом нижнем углу\n\r4. Найдите AmneziaVPN среди предложенных приложений и кликните по нему\n\r5. Откроется приложение AmneziaVPN и спросит о добавлении конфигурации, согласитесь на добавление конфигурации\n\r6. Нажмите на большую круглую кнопку подключиться на главном экране приложения. Готово\n\r\n\r<a href='https://t.me/vpnducks_video/4'>Видео-инструкция</a>\n\r\n\rЧто-то не получилось? Напишите нам @vpnducks_support"
            instructionAndroid = f"<b>Подключение VPN DUCKS на Android</b>\n\r\n\r1. Установите приложение <a href='https://play.google.com/store/apps/details?id=org.amnezia.vpn'>AmneziaVPN для Android из Google Play</a>\n\r2. Откройте прикрепленный выше файл конфигурации vpnducks_{str(user_dat.tgid)}.conf с помощью приложения AmneziaVPN\n\r3. Откроется приложение AmneziaVPN, нажмите на кнопку подключиться\n\r4. Нажмите на большую круглую кнопку подключиться на главном экране приложения и разрешите смартфону установить VPN соединение. Готово\n\r\n\rЧто-то не получилось? Напишите нам @vpnducks_support"
            instructionPC = f"<b>Подключение VPN DUCKS на PC (Windows, MacOS)</b>\n\r\n\r1. Установите приложение AmneziaVPN на <a href='https://github.com/amnezia-vpn/amnezia-client/releases/download/4.7.0.0/AmneziaVPN_4.7.0.0_x64.exe'>для Windows</a> или <a href='https://github.com/amnezia-vpn/amnezia-client/releases/download/4.7.0.0/AmneziaVPN_4.7.0.0.dmg'>для MacOS</a>\n\r2. Установите скачанную программу\n\r3.Откройте прикрепленный выше файл конфигурации vpnducks_{str(user_dat.tgid)}.conf в программе AmneziaVPN\n\r4. Нажмите на кнопку подключиться\n\r5. Нажмите на большую круглую кнопку подключиться на главном экране программы и разрешите установить VPN соединение. Готово\n\r\n\rЧто-то не получилось? Напишите нам @vpnducks_support"
            if(device == "iPhone"):
                await bot.send_document(chat_id=user_dat.tgid, caption=e.emojize(instructionIPhone), parse_mode="HTML", reply_markup=await main_buttons(user_dat, True), document=configFull, visible_file_name=f"vpnducks_{str(user_dat.tgid)}.conf")
            if(device == "Android"):
                await bot.send_document(chat_id=user_dat.tgid, caption=e.emojize(instructionAndroid), parse_mode="HTML", reply_markup=await main_buttons(user_dat, True), document=configFull, visible_file_name=f"vpnducks_{str(user_dat.tgid)}.conf")
            if(device == "PC"):
                await bot.send_document(chat_id=user_dat.tgid, caption=e.emojize(instructionPC), parse_mode="HTML", reply_markup=await main_buttons(user_dat, True), document=configFull, visible_file_name=f"vpnducks_{str(user_dat.tgid)}.conf")

async def addTrialForReferrerByUserId(userId):
    user_dat = await User.GetInfo(userId)
    try:
        referrer_id = int(user_dat.referrer_id)
    except TypeError:
        referrer_id = 0
    if referrer_id != 0:
        user_dat_referrer = await User.GetInfo(user_dat.referrer_id)
        addTrialTime = 30 * CONFIG['count_free_from_referrer'] * 60 * 60 * 24
        db = await aiosqlite.connect(DBCONNECT)
        db.row_factory = sqlite3.Row
        subscription = int(user_dat_referrer.subscription) + int(addTrialTime)
        await db.execute(f"Update userss set subscription=subscription+{addTrialTime}, banned=false, trial_continue=false, notion_oneday=false where tgid={referrer_id}")
        await db.commit()
        await bot.send_message(user_dat.referrer_id, f"<b>Поздравляем!</b>\nПользователь, пришедший по вашей ссылке, оплатил подписку, вам добавлен <b>+1 месяц</b> бесплатного доступа", reply_markup=await main_buttons(user_dat_referrer, True), parse_mode="HTML")

@bot.message_handler(commands=['start'])
async def start(message: types.Message):
    if message.chat.type == "private":
        await bot.delete_state(message.from_user.id)
        user_dat = await User.GetInfo(message.chat.id)

        if user_dat.registered:
            await sendConfig(message.chat.id)
            await bot.send_message(message.chat.id, e.emojize("Инструкция по установке :index_pointing_up:"), parse_mode="HTML",
                                   reply_markup=await main_buttons(user_dat))
        else:
            try:
                username = "@" + str(message.from_user.username)
            except:
                username = str(message.from_user.id)
            # Определяем referrer_id
            arg_referrer_id = message.text[7:]
            referrer_id = None if arg_referrer_id is None else arg_referrer_id
            await user_dat.Adduser(username, message.from_user.full_name, referrer_id)
            # Обработка реферера
            if referrer_id and referrer_id != user_dat.tgid:
                # Пользователь пришел по реферальной ссылке, обрабатываем это
                referrerUser = await User.GetInfo(referrer_id)
                await bot.send_message(referrer_id,
                                       f"По вашей ссылке пришел новый пользователь\nВы получите +1 месяц бесплатного доступа, если он оплатит подписку",
                                       reply_markup=await main_buttons(referrerUser))

            # Приветствуем нового пользователя (реферала)
            user_dat = await User.GetInfo(message.chat.id)
#             await bot.send_message(message.chat.id, e.emojize(texts_for_bot["hello_message"]), parse_mode="HTML", reply_markup=await main_buttons(user_dat))
#             await sendConfig(message.chat.id)

            trialText = e.emojize(f"Привет, {user_dat.fullname}!\n\r\n\r" \
                                  f"🎁 <b>Дарим вам 7 дней бесплатного доступа!</b>\n\r\n\r" \
                                  f"Пожалуйста, выберите тип телефона или планшета, для которого нужна инструкция для подключения:\n\r")

            trialButtons = await getTrialButtons()
            await bot.send_message(message.chat.id, trialText, parse_mode="HTML", reply_markup=trialButtons)

@bot.message_handler(state=MyStates.editUser, content_types=["text"])
async def Work_with_Message(m: types.Message):
    async with bot.retrieve_data(m.from_user.id) as data:
        tgid = data['usertgid']
    user_dat = await User.GetInfo(tgid)
    if e.demojize(m.text) == "Назад :right_arrow_curving_left:":
        await bot.reset_data(m.from_user.id)
        await bot.delete_state(m.from_user.id)
        await bot.send_message(m.from_user.id, "Вернул вас назад!", reply_markup=await buttons.admin_buttons())
        return
    if e.demojize(m.text) == "Добавить время":
        await bot.set_state(m.from_user.id, MyStates.UserAddTimeDays)
        Butt_skip = types.ReplyKeyboardMarkup(resize_keyboard=True)
        Butt_skip.add(types.KeyboardButton(e.emojize(f"Пропустить :next_track_button:")))
        await bot.send_message(m.from_user.id, "Введите сколько дней хотите добавить:", reply_markup=Butt_skip)
        return
    if e.demojize(m.text) == "Обнулить время":
        await bot.set_state(m.from_user.id, MyStates.editUserResetTime)
        Butt_skip = types.ReplyKeyboardMarkup(resize_keyboard=True)
        Butt_skip.add(types.KeyboardButton(e.emojize(f"Да")))
        Butt_skip.add(types.KeyboardButton(e.emojize(f"Нет")))
        await bot.send_message(m.from_user.id, "Вы уверены что хотите сбросить время для этого пользователя ?",
                               reply_markup=Butt_skip)
        return

@bot.message_handler(state=MyStates.editUserResetTime, content_types=["text"])
async def Work_with_Message(m: types.Message):
    async with bot.retrieve_data(m.from_user.id) as data:
        tgid = data['usertgid']

    if e.demojize(m.text) == "Да":
        db = await aiosqlite.connect(DBCONNECT)
        db.row_factory = sqlite3.Row
        await db.execute(f"Update userss set subscription = ?, banned=false, notion_oneday=true where tgid=?",
                         (str(int(time.time())), tgid))
        await db.commit()
        await bot.send_message(m.from_user.id, "Время сброшено!")

    async with bot.retrieve_data(m.from_user.id) as data:
        usertgid = data['usertgid']
    user_dat = await User.GetInfo(usertgid)
    readymes = f"Пользователь: <b>{str(user_dat.fullname)}</b> ({str(user_dat.username)})\nTG-id: <code>{str(user_dat.tgid)}</code>\n\n"

    if int(user_dat.subscription) > int(time.time()):
        readymes += f"Подписка: до <b>{datetime.utcfromtimestamp(int(user_dat.subscription) + CONFIG['UTC_time'] * 3600).strftime('%d.%m.%Y %H:%M')}</b> :check_mark_button:"
    else:
        readymes += f"Подписка: закончилась <b>{datetime.utcfromtimestamp(int(user_dat.subscription) + CONFIG['UTC_time'] * 3600).strftime('%d.%m.%Y %H:%M')}</b> :cross_mark:"
    await bot.set_state(m.from_user.id, MyStates.editUser)

    await bot.send_message(m.from_user.id, e.emojize(readymes),
                           reply_markup=await buttons.admin_buttons_edit_user(user_dat), parse_mode="HTML")

@bot.message_handler(state=MyStates.UserAddTimeDays, content_types=["text"])
async def Work_with_Message(m: types.Message):
    if e.demojize(m.text) == "Пропустить :next_track_button:":
        days = 0
    else:
        try:
            days = int(m.text)
        except:
            await bot.send_message(m.from_user.id, "Должно быть число!\nПопробуйте еще раз.")
            return
        if days < 0:
            await bot.send_message(m.from_user.id, "Не должно быть отрицательным числом!\nПопробуйте еще раз.")
            return

    async with bot.retrieve_data(m.from_user.id) as data:
        data['days'] = days
    await bot.set_state(m.from_user.id, MyStates.UserAddTimeHours)
    Butt_skip = types.ReplyKeyboardMarkup(resize_keyboard=True)
    Butt_skip.add(types.KeyboardButton(e.emojize(f"Пропустить :next_track_button:")))
    await bot.send_message(m.from_user.id, "Введите сколько часов хотите добавить:", reply_markup=Butt_skip)

@bot.message_handler(state=MyStates.UserAddTimeHours, content_types=["text"])
async def Work_with_Message(m: types.Message):
    if e.demojize(m.text) == "Пропустить :next_track_button:":
        hours = 0
    else:
        try:
            hours = int(m.text)
        except:
            await bot.send_message(m.from_user.id, "Должно быть число!\nПопробуйте еще раз.")
            return
        if hours < 0:
            await bot.send_message(m.from_user.id, "Не должно быть отрицательным числом!\nПопробуйте еще раз.")
            return

    async with bot.retrieve_data(m.from_user.id) as data:
        data['hours'] = hours
    await bot.set_state(m.from_user.id, MyStates.UserAddTimeMinutes)
    Butt_skip = types.ReplyKeyboardMarkup(resize_keyboard=True)
    Butt_skip.add(types.KeyboardButton(e.emojize(f"Пропустить :next_track_button:")))
    await bot.send_message(m.from_user.id, "Введите сколько минут хотите добавить:", reply_markup=Butt_skip)

@bot.message_handler(state=MyStates.UserAddTimeMinutes, content_types=["text"])
async def Work_with_Message(m: types.Message):
    if e.demojize(m.text) == "Пропустить :next_track_button:":
        minutes = 0
    else:
        try:
            minutes = int(m.text)
        except:
            await bot.send_message(m.from_user.id, "Должно быть число!\nПопробуйте еще раз.")
            return
        if minutes < 0:
            await bot.send_message(m.from_user.id, "Не должно быть отрицательным числом!\nПопробуйте еще раз.")
            return

    async with bot.retrieve_data(m.from_user.id) as data:
        data['minutes'] = minutes
        hours = data['hours']
        days = data['days']
        tgid = data['usertgid']

    await bot.set_state(m.from_user.id, MyStates.UserAddTimeApprove)
    Butt_skip = types.ReplyKeyboardMarkup(resize_keyboard=True)
    Butt_skip.add(types.KeyboardButton(e.emojize(f"Да")))
    Butt_skip.add(types.KeyboardButton(e.emojize(f"Нет")))
    await bot.send_message(m.from_user.id,
                           f"Пользователю {str(tgid)} добавится:\n\nДни: {str(days)}\nЧасы: {str(hours)}\nМинуты: {str(minutes)}\n\nВсе верно ?",
                           reply_markup=Butt_skip)

@bot.message_handler(state=MyStates.UserAddTimeApprove, content_types=["text"])
async def Work_with_Message(m: types.Message):
    all_time = 0
    if e.demojize(m.text) == "Да":
        async with bot.retrieve_data(m.from_user.id) as data:
            minutes = data['minutes']
            hours = data['hours']
            days = data['days']
            tgid = data['usertgid']
        all_time += minutes * 60
        all_time += hours * 60 * 60
        all_time += days * 60 * 60 * 24
        await AddTimeToUser(tgid, all_time)
        await bot.send_message(m.from_user.id, e.emojize("Время добавлено пользователю!"), parse_mode="HTML")

    async with bot.retrieve_data(m.from_user.id) as data:
        usertgid = data['usertgid']
    user_dat = await User.GetInfo(usertgid)
    readymes = f"Пользователь: <b>{str(user_dat.fullname)}</b> ({str(user_dat.username)})\nTG-id: <code>{str(user_dat.tgid)}</code>\n\n"

    if int(user_dat.subscription) > int(time.time()):
        readymes += f"Подписка: до <b>{datetime.utcfromtimestamp(int(user_dat.subscription) + CONFIG['UTC_time'] * 3600).strftime('%d.%m.%Y %H:%M')}</b> :check_mark_button:"
    else:
        readymes += f"Подписка: закончилась <b>{datetime.utcfromtimestamp(int(user_dat.subscription) + CONFIG['UTC_time'] * 3600).strftime('%d.%m.%Y %H:%M')}</b> :cross_mark:"
    await bot.set_state(m.from_user.id, MyStates.editUser)

    await bot.send_message(m.from_user.id, e.emojize(readymes),
                           reply_markup=await buttons.admin_buttons_edit_user(user_dat), parse_mode="HTML")

@bot.message_handler(state=MyStates.findUserViaId, content_types=["text"])
async def Work_with_Message(m: types.Message):
    await bot.delete_state(m.from_user.id)
    try:
        user_id = int(m.text)
    except:
        await bot.send_message(m.from_user.id, "Неверный Id!", reply_markup=await buttons.admin_buttons())
        return
    user_dat = await User.GetInfo(user_id)
    if not user_dat.registered:
        await bot.send_message(m.from_user.id, "Такого пользователя не существует!",
                               reply_markup=await buttons.admin_buttons())
        return

    readymes = f"Пользователь: <b>{str(user_dat.fullname)}</b> ({str(user_dat.username)})\nTG-id: <code>{str(user_dat.tgid)}</code>\n\n"

    if int(user_dat.subscription) > int(time.time()):
        readymes += f"Подписка: до <b>{datetime.utcfromtimestamp(int(user_dat.subscription) + CONFIG['UTC_time'] * 3600).strftime('%d.%m.%Y %H:%M')}</b> :check_mark_button:"
    else:
        readymes += f"Подписка: закончилась <b>{datetime.utcfromtimestamp(int(user_dat.subscription) + CONFIG['UTC_time'] * 3600).strftime('%d.%m.%Y %H:%M')}</b> :cross_mark:"
    await bot.set_state(m.from_user.id, MyStates.editUser)
    async with bot.retrieve_data(m.from_user.id) as data:
        data['usertgid'] = user_dat.tgid
    await bot.send_message(m.from_user.id, e.emojize(readymes),
                           reply_markup=await buttons.admin_buttons_edit_user(user_dat), parse_mode="HTML")

@bot.message_handler(state=MyStates.prepareUserForSendMessage, content_types=["text"])
async def Work_with_Message(m: types.Message):
    await bot.delete_state(m.from_user.id)
    try:
        user_id = int(m.text)
    except:
        await bot.send_message(m.from_user.id, "Неверный Id!", reply_markup=await buttons.admin_buttons())
        return
    user_dat = await User.GetInfo(user_id)
    if not user_dat.registered:
        await bot.send_message(m.from_user.id, "Такого пользователя не существует!",
                               reply_markup=await buttons.admin_buttons())
        return

    readymes = f"Пользователь: <b>{str(user_dat.fullname)}</b> ({str(user_dat.username)})\nTG-id: <code>{str(user_dat.tgid)}</code>\n\n"

    if int(user_dat.subscription) > int(time.time()):
        readymes += f"Подписка: до <b>{datetime.utcfromtimestamp(int(user_dat.subscription) + CONFIG['UTC_time'] * 3600).strftime('%d.%m.%Y %H:%M')}</b> :check_mark_button:"
    else:
        readymes += f"Подписка: закончилась <b>{datetime.utcfromtimestamp(int(user_dat.subscription) + CONFIG['UTC_time'] * 3600).strftime('%d.%m.%Y %H:%M')}</b> :cross_mark:"
    await bot.set_state(m.from_user.id, MyStates.sendMessageToUser)
    async with bot.retrieve_data(m.from_user.id) as data:
        data['usertgid'] = user_dat.tgid
    await bot.send_message(m.from_user.id, e.emojize(readymes), parse_mode="HTML")
    await bot.send_message(m.from_user.id, "Введите сообщение:", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(state=MyStates.sendMessageToUser, content_types=["text"])
async def Work_with_Message(m: types.Message):
    async with bot.retrieve_data(m.from_user.id) as data:
            tgid = data['usertgid']
    await bot.send_message(tgid, e.emojize(m.text), parse_mode="HTML")
    await bot.delete_state(m.from_user.id)
    await bot.send_message(m.from_user.id, "Сообщение отправлено", reply_markup=await buttons.admin_buttons())

@bot.message_handler(state=MyStates.sendMessageToAllInactiveUser, content_types=["text"])
async def Work_with_Message(m: types.Message):
    if e.demojize(m.text) == "Назад :right_arrow_curving_left:":
        await bot.delete_state(m.from_user.id)
        await bot.send_message(m.from_user.id, "Вернул вас назад!", reply_markup=await buttons.admin_buttons())
        return

    user_dat = await User.GetInfo(m.from_user.id)
    allusers = await user_dat.GetAllUsersWithoutSub()

    readymass = []
    readymes = ""
    for i in allusers:
        await bot.send_message(i['tgid'], e.emojize(m.text), parse_mode="HTML")
        if len(readymes) + len(f"{i['fullname']} ({i['username']}|<code>{str(i['tgid'])}</code>)\n") > 4090:
            readymass.append(readymes)
            readymes = ""
        readymes += f"{i['fullname']} ({i['username']}|<code>{str(i['tgid'])}</code>)\n"

    readymass.append(readymes)
    for i in readymass:
        await bot.send_message(m.from_user.id, e.emojize(i), reply_markup=await buttons.admin_buttons(),
                               parse_mode="HTML")

    await bot.delete_state(m.from_user.id)
    await bot.send_message(m.from_user.id, "Сообщения отправлены", reply_markup=await buttons.admin_buttons())
    return

@bot.message_handler(state=MyStates.AdminNewUser, content_types=["text"])
async def Work_with_Message(m: types.Message):
    if e.demojize(m.text) == "Назад :right_arrow_curving_left:":
        await bot.delete_state(m.from_user.id)
        await bot.send_message(m.from_user.id, "Вернул вас назад!", reply_markup=await buttons.admin_buttons())
        return

    if set(m.text) <= set(string.ascii_letters + string.digits):
        db = await aiosqlite.connect(DBCONNECT)
        await db.execute(f"INSERT INTO static_profiles (name) values (?)", (m.text,))
        await db.commit()

        client = {'name': str(m.text)}

        requests.post(f"{BASE_URL}/wireguard/client", data=json.dumps({"name": str(m.text)}), headers={"Content-Type": "application/json", "password": f"{PASSWORD}"})

        await bot.delete_state(m.from_user.id)
        await bot.send_message(m.from_user.id,
                               "Пользователь добавлен!", reply_markup=await buttons.admin_buttons_static_users())
    else:
        await bot.send_message(m.from_user.id,
                               "Можно использовать только латинские символы и арабские цифры!\nПопробуйте заново.")
        return

@bot.message_handler(state="*", content_types=["text"])
async def Work_with_Message(m: types.Message):
    user_dat = await User.GetInfo(m.chat.id)

    if user_dat.registered == False:
        try:
            username = "@" + str(m.from_user.username)
        except:

            username = str(m.from_user.id)

        # Определяем referrer_id
        arg_referrer_id = m.text[7:]
        referrer_id = arg_referrer_id if arg_referrer_id != user_dat.tgid else 0

        await user_dat.Adduser(username, m.from_user.full_name, )
        await bot.send_message(m.chat.id,
                               texts_for_bot["hello_message"],
                               parse_mode="HTML", reply_markup=await main_buttons(user_dat))
        return
    await user_dat.CheckNewNickname(m)

    if e.demojize(m.text) == "Почему стоит выбрать нас? :smiling_face_with_sunglasses:":
        await bot.send_message(m.chat.id, e.emojize(texts_for_bot["hello_message"]), parse_mode="HTML",
                                       reply_markup=await main_buttons(user_dat))
        return

    if m.from_user.id in CONFIG["admin_tg_id"]:
        if e.demojize(m.text) == "Админ-панель :smiling_face_with_sunglasses:":
            await bot.send_message(m.from_user.id, "Админ панель", reply_markup=await buttons.admin_buttons())
            return
        if e.demojize(m.text) == "Главное меню :right_arrow_curving_left:":
            await bot.send_message(m.from_user.id, e.emojize("Админ-панель :smiling_face_with_sunglasses:"),
                                   reply_markup=await main_buttons(user_dat))
            return
        if e.demojize(m.text) == "Вывести пользователей :bust_in_silhouette:":
            await bot.send_message(m.from_user.id, e.emojize("Выберите каких пользователей хотите вывести."),
                                   reply_markup=await buttons.admin_buttons_output_users())
            return

        if e.demojize(m.text) == "Назад :right_arrow_curving_left:":
            await bot.send_message(m.from_user.id, "Админ панель", reply_markup=await buttons.admin_buttons())
            return

        if e.demojize(m.text) == "Всех пользователей":
            allusers = await user_dat.GetAllUsers()
            readymass = []
            readymes = ""
            for i in allusers:
                if int(i['subscription']) > int(time.time()):
                    if len(readymes) + len(f"{i['fullname']} ({i['username']}|{str(i['tgid'])}) :check_mark_button:\n") > 4090:
                        readymass.append(readymes)
                        readymes = ""
                    readymes += f"{i['fullname']} ({i['username']}|{str(i['tgid'])}) :check_mark_button:\n"
                else:
                    if len(readymes) + len(f"{i['fullname']} ({i['username']}|{str(i['tgid'])})\n") > 4090:
                        readymass.append(readymes)
                        readymes = ""
                    readymes += f"{i['fullname']} ({i['username']}|{str(i['tgid'])})\n"
            readymass.append(readymes)
            for i in readymass:
                await bot.send_message(m.from_user.id, e.emojize(i), reply_markup=await buttons.admin_buttons())
            return

        if e.demojize(m.text) == "Пользователей с подпиской":
            allusers = await user_dat.GetAllUsersWithSub()
            readymass = []
            readymes = ""
            if len(allusers) == 0:
                await bot.send_message(m.from_user.id, e.emojize("Нет пользователей с подпиской!"),
                                       reply_markup=await buttons.admin_buttons(), parse_mode="HTML")
                return
            for i in allusers:
                if int(i['subscription']) > int(time.time()):
                    if len(readymes) + len(
                            f"{i['fullname']} ({i['username']}|{str(i['tgid'])}) - {datetime.utcfromtimestamp(int(i['subscription']) + CONFIG['UTC_time'] * 3600).strftime('%d.%m.%Y %H:%M')}\n") > 4090:
                        readymass.append(readymes)
                        readymes = ""
                    readymes += f"{i['fullname']} ({i['username']}|{str(i['tgid'])}) - {datetime.utcfromtimestamp(int(i['subscription']) + CONFIG['UTC_time'] * 3600).strftime('%d.%m.%Y %H:%M')}\n"
            readymass.append(readymes)
            for i in readymass:
                await bot.send_message(m.from_user.id, e.emojize(i))
            return

        if e.demojize(m.text) == "Редактировать пользователя по id":
            await bot.send_message(m.from_user.id, "Введите Telegram Id пользователя:",
                                   reply_markup=types.ReplyKeyboardRemove())
            await bot.set_state(m.from_user.id, MyStates.findUserViaId)
            return

        if e.demojize(m.text) == "Отправить пользователю сообщение :pencil:":
            await bot.send_message(m.from_user.id, "Введите Telegram Id пользователя:",
                                   reply_markup=types.ReplyKeyboardRemove())
            await bot.set_state(m.from_user.id, MyStates.prepareUserForSendMessage)
            return

        if e.demojize(m.text) == "Отправить сообщение всем неактивным пользователям :pencil:":
            await bot.set_state(m.from_user.id, MyStates.sendMessageToAllInactiveUser)
            await bot.send_message(m.from_user.id, "Введите сообщение:", reply_markup=await buttons.admin_buttons_back())
            return

        if e.demojize(m.text) == "Добавить пользователя :plus:":
            await bot.send_message(m.from_user.id,
                                   "Введите имя для нового пользователя!\nМожно использовать только латинские символы и арабские цифры.",
                                   reply_markup=await buttons.admin_buttons_back())
            await bot.set_state(m.from_user.id, MyStates.AdminNewUser)
            return

    if e.demojize(m.text) == "Продлить подписку :money_bag:":
        payment_info = await user_dat.PaymentInfo()
        if True:
            await sendPayMessage(m.chat.id)
        return

    if e.demojize(m.text) == "Как подключить :gear:":
        await sendConfig(m.chat.id)
        return

    if e.demojize(m.text) == "Пригласить :woman_and_man_holding_hands:":
        countReferal = await user_dat.countReferrerByUser()
        refLink = f"https://t.me/{CONFIG['bot_name']}?start=" + str(user_dat.tgid)

        msg = e.emojize(f"<b>Реферальная программа</b>\n\r\n\r" \
              f":fire: Получите подписку, пригласив друзей по реферальной ссылке. Они получат неделю VPN бесплатно, а если после этого оформят подписку, мы подарим вам за каждого по месяцу подписки на DUCKS VPN!\n\r\n\r" \
              f":money_bag: А если вы блогер или владелец крупного сообщества, присоединяйтесь к нашей партнерской программе и зарабатывайте, рассказывая о DUCKS VPN! Напишите нам @vpnducks_support\n\r" \
              f"\n\rВаша пригласительная ссылка (кликните по ней, чтобы скопировать): \n\r<code>{refLink}</code>"
              f"\n\r\n\rПользователей, пришедших по вашей ссылке: {str(countReferal)}")

        await bot.send_message(chat_id=m.chat.id, text=msg, parse_mode='HTML')
        return

    if e.demojize(m.text) == "Помощь :heart_hands:":
        msg = e.emojize(f"Как мы можем вам помочь?")
        helpButtons = types.InlineKeyboardMarkup(row_width = 1)
        helpButtons.add(
            types.InlineKeyboardButton(e.emojize(":credit_card: Обновить информацию о подписке"), callback_data="Help:update"),
            types.InlineKeyboardButton(e.emojize(":heart_hands: Поддержка"), callback_data="Help:support"),
        )
        await bot.send_message(chat_id=m.chat.id, text=msg, parse_mode="HTML", reply_markup=helpButtons)
        return

    else:
        if "Подписка закончилась:" in m.text:
            await sendPayMessage(m.chat.id)
            return
        if "Подписка активна до:" in m.text:
            return
        for admin in CONFIG["admin_tg_id"]:
            await bot.send_message(admin, f"Новое сообщение от @{m.from_user.username} ({m.from_user.id}): {e.emojize(m.text)}")
        return

@bot.callback_query_handler(func=lambda c: 'Init:' in c.data)
async def Init(call: types.CallbackQuery):
    user_dat = await User.GetInfo(call.from_user.id)
    device = str(call.data).split(":")[1]
    await sendConfigAndInstructions(user_dat.tgid, device)
    await bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: 'Help:' in c.data)
async def Init(call: types.CallbackQuery):
    user_dat = await User.GetInfo(call.from_user.id)
    command = str(call.data).split(":")[1]
    if command == 'update':
        await bot.send_message(user_dat.tgid, e.emojize('Информация о подписке обновлена'), parse_mode="HTML", reply_markup=await main_buttons(user_dat, True))
    else:
        await bot.send_message(user_dat.tgid, e.emojize('Напишите нам @vpnducks_support'), parse_mode="HTML", reply_markup=await main_buttons(user_dat, True))

    await bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: 'Referrer' in c.data)
async def Referrer(call: types.CallbackQuery):
    user_dat = await User.GetInfo(call.from_user.id)
    countReferal = await user_dat.countReferrerByUser()
    refLink = "https://t.me/FreeVpnDownloadBot?start=" + str(user_dat.tgid)

    msg = e.emojize(f"<b>Реферальная программа</b>\n\r\n\r" \
          f":fire: Получите подписку, пригласив друзей по реферальной ссылке. Они получат неделю VPN бесплатно, а если после этого оформят подписку, мы подарим вам за каждого по месяцу подписки на DUCKS VPN!\n\r\n\r" \
          f":money_bag: А если вы блогер или владелец крупного сообщества, присоединяйтесь к нашей партнерской программе и зарабатывайте, рассказывая о DUCKS VPN! Напишите нам @vpnducks_support\n\r" \
          f"\n\rВаша пригласительная ссылка (кликните по ней, чтобы скопировать): \n\r<code>{refLink}</code>"
          f"\n\r\n\rПользователей, пришедших по вашей ссылке: {str(countReferal)}")

    await bot.send_message(chat_id=call.message.chat.id, text=msg, parse_mode='HTML')

@bot.callback_query_handler(func=lambda c: 'BuyMonth:' in c.data)
async def Buy_month(call: types.CallbackQuery):
    user_dat = await User.GetInfo(call.from_user.id)
    payment_info = await user_dat.PaymentInfo()

    Month_count = int(str(call.data).split(":")[1])
    await bot.delete_message(call.message.chat.id, call.message.id)

    bill = await bot.send_invoice(call.message.chat.id, f"Оплата VPN", f"VPN на {str(Month_count)} мес.", call.data,
                                    currency="RUB",prices=[
                types.LabeledPrice(f"VPN на {str(Month_count)} мес.", getCostBySale(Month_count) * 100)],
                                    provider_token=CONFIG["tg_shop_token"])

    await bot.answer_callback_query(call.id)

async def AddTimeToUser(tgid, timetoadd):
    userdat = await User.GetInfo(tgid)
    db = await aiosqlite.connect(DBCONNECT)
    db.row_factory = sqlite3.Row
    if int(userdat.subscription) < int(time.time()):
        passdat = int(time.time()) + timetoadd
        await db.execute(f"Update userss set subscription = ?, banned=false, notion_oneday=false where tgid=?",
                         (str(int(time.time()) + timetoadd), userdat.tgid))

        requests.post(f"{BASE_URL}/wireguard/client", data=json.dumps({"name": str(userdat.tgid)}), headers={"Content-Type": "application/json", "password": f"{PASSWORD}"})

        await bot.send_message(userdat.tgid, e.emojize('<b>Ваш конфигурационный файл был обновлен</b>\n\nНеобходимо импортировать новый файл в приложение AmneziaVpn.\nНажмите на кнопку <b>Как подключить :gear:</b> и следуйте инструкции для вашего устройства\n\nНе забудьте удалить предыдущее соединение в Amnezia Vpn\n\r\n\rЧто-то не получилось? Напишите нам @vpnducks_support'), parse_mode="HTML", reply_markup=await main_buttons(userdat, True))
    else:
        passdat = int(userdat.subscription) + timetoadd
        await db.execute(f"Update userss set subscription = ?, notion_oneday=false where tgid=?",
                         (str(int(userdat.subscription) + timetoadd), userdat.tgid))
        await bot.send_message(userdat.tgid, e.emojize(
                    'Информация о подписке обновлена'), parse_mode="HTML", reply_markup=await main_buttons(userdat, True))
    await db.commit()

@bot.callback_query_handler(func=lambda c: 'DELETE:' in c.data or 'DELETYES:' in c.data or 'DELETNO:' in c.data)
async def DeleteUserYesOrNo(call: types.CallbackQuery):
    idstatic = str(call.data).split(":")[1]
    db = await aiosqlite.connect(DBCONNECT)
    c = await db.execute(f"select * from static_profiles where id=?", (int(idstatic),))
    staticuser = await c.fetchone()
    await c.close()
    await db.close()
    if staticuser[0] != int(idstatic):
        await bot.answer_callback_query(call.id, "Пользователь уже удален!")
        return

    if "DELETE:" in call.data:
        Butt_delete_account = types.InlineKeyboardMarkup()
        Butt_delete_account.add(
            types.InlineKeyboardButton(e.emojize("Удалить!"), callback_data=f'DELETYES:{str(staticuser[0])}'),
            types.InlineKeyboardButton(e.emojize("Нет"), callback_data=f'DELETNO:{str(staticuser[0])}'))
        await bot.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=Butt_delete_account)
        await bot.answer_callback_query(call.id)
        return
    if "DELETYES:" in call.data:
        db = await aiosqlite.connect(DBCONNECT)
        await db.execute(f"delete from static_profiles where id=?", (int(idstatic),))
        await db.commit()
        await bot.delete_message(call.message.chat.id, call.message.id)

        response = requests.get(f"{BASE_URL}/wireguard/client", headers={"password": "199612"})
        for val in response.json():
            if str(staticuser[1]) == val.get('name', 0):
                response = requests.delete(f"{BASE_URL}/wireguard/client/{val.get('id', 0)}", headers={"password": f"{PASSWORD}"})

        await bot.answer_callback_query(call.id, "Пользователь удален!")
        return
    if "DELETNO:" in call.data:
        Butt_delete_account = types.InlineKeyboardMarkup()
        Butt_delete_account.add(types.InlineKeyboardButton(e.emojize("Удалить пользователя :cross_mark:"),
                                                           callback_data=f'DELETE:{str(idstatic)}'))
        await bot.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=Butt_delete_account)
        await bot.answer_callback_query(call.id)
        return

@bot.pre_checkout_query_handler(func=lambda query: True)
async def checkout(pre_checkout_query):
    # (pre_checkout_query)
    month = int(str(pre_checkout_query.invoice_payload).split(":")[1])
    if(month == 1):
            count = CONFIG['perc_1']
    if(month == 3):
            count = CONFIG['perc_3']
    if(month == 6):
            count = CONFIG['perc_6']
    if(month == 12):
            count = CONFIG['perc_12']

    if getCostBySale(month) * 100 != pre_checkout_query.total_amount:
        await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=False,
                                            error_message="Нельзя купить по старой цене!")
        await bot.send_message(pre_checkout_query.from_user.id,
                               "<b>Цена изменилась! Нельзя приобрести по старой цене!</b>", parse_mode="HTML")
    else:
        await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True,
                                            error_message="Оплата не прошла, попробуйте еще раз!")

def getCostBySale(month):
    cost = month * CONFIG['one_month_cost']
    oneMonthCost = float(CONFIG['one_month_cost'])
    perc3 = float(CONFIG['perc_3'])
    perc6 = float(CONFIG['perc_6'])
    perc12 = float(CONFIG['perc_12'])

    if month == 3:
        cost = oneMonthCost * perc3
    elif month == 6:
        cost = oneMonthCost * perc6
    elif month == 12:
        cost = oneMonthCost * perc12
    elif month == 100:
        cost = 60

    return int(cost)

def getSale(month):
    cost = month * CONFIG['one_month_cost']
    oneMonthCost = float(CONFIG['one_month_cost'])
    perc3 = float(CONFIG['perc_3'])
    perc6 = float(CONFIG['perc_6'])
    perc12 = float(CONFIG['perc_12'])

    if month == 3:
        sale = 100 - round((oneMonthCost * perc3 * 100) / cost)
    elif month == 6:
        sale = 100 - round((oneMonthCost * perc6 * 100) / cost)
    elif month == 12:
        sale = 100 - round((oneMonthCost * perc12 * 100) / cost)
    else:
        sale = 0
    return sale

@bot.message_handler(content_types=['successful_payment'])
async def got_payment(m):
    payment: types.SuccessfulPayment = m.successful_payment
    month = int(str(payment.invoice_payload).split(":")[1])

    user_dat = await User.GetInfo(m.from_user.id)
    await bot.send_message(m.from_user.id, e.emojize(texts_for_bot["success_pay_message"]), reply_markup=await buttons.main_buttons(user_dat, True), parse_mode="HTML")

    addTimeSubscribe = month * 30 * 24 * 60 * 60
    await AddTimeToUser(m.from_user.id, addTimeSubscribe)

    payment_id = str(payment.provider_payment_charge_id)
    # save info about user
    await user_dat.NewPay(
        payment_id,
        getCostBySale(month),
        addTimeSubscribe,
        m.from_user.id)

    await addTrialForReferrerByUserId(m.from_user.id)

    await bot.send_message(m.from_user.id, f"Информация о подписке обновлена", reply_markup=await buttons.main_buttons(user_dat, True), parse_mode="HTML")

    for admin in CONFIG["admin_tg_id"]:
        await bot.send_message(admin, f"Новая оплата подписки от @{m.from_user.username} ( {m.from_user.id} ) на <b>{month}</b> мес. : {getCostBySale(month)} руб.", parse_mode="HTML")

bot.add_custom_filter(asyncio_filters.StateFilter(bot))

def checkTime():
    while True:
        try:
            time.sleep(15)
            db = sqlite3.connect(DBCONNECT)
            db.row_factory = sqlite3.Row
            c = db.execute(f"SELECT * FROM userss")
            log = c.fetchall()
            c.close()
            db.close()
            for i in log:
                time_now = int(time.time())
                remained_time = int(i['subscription']) - time_now
                if remained_time <= 0 and i['banned'] == False:
                    db = sqlite3.connect(DBCONNECT)
                    db.execute(f"UPDATE userss SET banned=true where tgid=?", (i['tgid'],))
                    db.commit()

                    response = requests.get(f"{BASE_URL}/wireguard/client", headers={"password": PASSWORD})
                    for val in response.json():
                        if str(i['tgid']) == val.get('name', 0):
                            response = requests.delete(f"{BASE_URL}/wireguard/client/{val.get('id', 0)}", headers={"password": f"{PASSWORD}"})

                    dateto = datetime.utcfromtimestamp(int(i['subscription']) + CONFIG['UTC_time'] * 3600).strftime(
                        '%d.%m.%Y %H:%M')
                    Butt_main = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    Butt_main.add(types.KeyboardButton(e.emojize(f":red_circle: Подписка закончилась: {dateto} МСК")))
                    Butt_main.add(types.KeyboardButton(e.emojize(f"Продлить подписку :money_bag:")),types.KeyboardButton(e.emojize(f"Как подключить :gear:")))
                    Butt_main.add(types.KeyboardButton(e.emojize(f"Почему стоит выбрать нас? :smiling_face_with_sunglasses:")), types.KeyboardButton(e.emojize(f"Пригласить :woman_and_man_holding_hands:")), types.KeyboardButton(e.emojize(f"Помощь :heart_hands:")))
                    if i['tgid'] in CONFIG["admin_tg_id"]:
                        Butt_main.add(types.KeyboardButton(e.emojize(f"Админ-панель :smiling_face_with_sunglasses:")))

                    BotChecking = TeleBot(BOTAPIKEY)
                    BotChecking.send_message(i['tgid'],
                                             texts_for_bot["ended_sub_message"],
                                             reply_markup=Butt_main, parse_mode="HTML")

                if remained_time <= 7200 and i['notion_oneday'] == False:
                    db = sqlite3.connect(DBCONNECT)
                    db.execute(f"UPDATE userss SET notion_oneday=true where tgid=?", (i['tgid'],))
                    db.commit()

                    Butt_reffer = types.InlineKeyboardMarkup()
                    Butt_reffer.add(
                        types.InlineKeyboardButton(
                            e.emojize(f"Бесплатно +{CONFIG['count_free_from_referrer']} месяц за нового друга, оплатившего подписку"),
                            callback_data="Referrer"))
                    BotChecking = TeleBot(BOTAPIKEY)
                    BotChecking.send_message(i['tgid'], texts_for_bot["alert_to_renew_sub"], reply_markup=Butt_reffer, parse_mode="HTML")

                # Дарим бесплатную подписку на 2 дня, если он висит 3 дня как неактивный и не ушел
                if remained_time <= 259200 and i['trial_continue'] == 0:
                    BotChecking = TeleBot(BOTAPIKEY)
                    timetoadd = 2 * 60 * 60 * 24
                    db = sqlite3.connect(DBCONNECT)
                    db.execute(f"UPDATE userss SET trial_continue=1 where tgid=?", (i['tgid'],))
                    db.execute(
                        f"Update userss set subscription = ?, banned=false, notion_oneday=false where tgid=?",
                        (str(int(time.time()) + timetoadd), i['tgid']))
                    db.commit()
                    db.close()

                    requests.post(f"{BASE_URL}/wireguard/client", data=json.dumps({"name": str(i['tgid'])}), headers={"Content-Type": "application/json", "password": f"{PASSWORD}"})

                    Butt_main = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    Butt_main.add(types.KeyboardButton(e.emojize(f"Продлить подписку :money_bag:")),
                                  types.KeyboardButton(e.emojize(f"Как подключить :gear:")))
                    BotChecking.send_message(i['tgid'],
                                             e.emojize(texts_for_bot["alert_to_extend_sub"]),
                                             reply_markup=Butt_main, parse_mode="HTML")

        except Exception as err:
            print(err)
            pass

if __name__ == '__main__':
    threadcheckTime = threading.Thread(target=checkTime, name="checkTime1")
    threadcheckTime.start()

    asyncio.run(bot.polling(non_stop=True, interval=0, request_timeout=60, timeout=60))
