import json
import time
from time import sleep

import buttons
import dbworker
import pay
import smrequests
import queueusers
import emoji as e
import emoji
import threading
import os
import traceback
import asyncio
import pymysql
import pymysql.cursors
import subprocess
import random
import string
from datetime import datetime
from telebot.apihelper import ApiTelegramException
from datetime import datetime
from telebot import TeleBot
from telebot import asyncio_filters
from telebot.async_telebot import AsyncTeleBot
from telebot import types
from telebot.asyncio_storage import StateMemoryStorage
from telebot.asyncio_handler_backends import State, StatesGroup
from buttons import main_buttons

from smrequests import getConnectionLinks, getAmneziaConnectionFile, switchUserActivity, addUser
from queueusers import addUserQueue, switchUserActivityQueue
from dbworker import User
from pay import Pay

from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    "admin_tg_id": [int(os.getenv("ADMIN_TG_ID_1")), int(os.getenv("ADMIN_TG_ID_2")), int(os.getenv("ADMIN_TG_ID_3"))],
    "one_month_cost": float(os.getenv("ONE_MONTH_COST")),
    "trial_period": os.getenv("TRIAL_PERIOD"),
    "perc_1": float(os.getenv("PERC_1")),
    "perc_3": float(os.getenv("PERC_3")),
    "perc_6": float(os.getenv("PERC_6")),
    "perc_12": float(os.getenv("PERC_12")),
    "UTC_time": int(os.getenv("UTC_TIME")),
    "tg_token": os.getenv("TG_TOKEN"),
    "tg_shop_token": os.getenv("TG_SHOP_TOKEN"),
    "count_free_from_referrer": int(os.getenv("COUNT_FREE_FROM_REFERRER")),
    "bot_name": os.getenv("BOT_NAME"),
    "db_host": os.getenv("DB_HOST"),
    "db_name": os.getenv("DB_NAME"),
    "db_user": os.getenv("DB_USER"),
    "db_password": os.getenv("DB_PASSWORD"),
    "server_manager_url": os.getenv("SERVER_MANAGER_URL"),
    "server_manager_email": os.getenv("SERVER_MANAGER_EMAIL"),
    "server_manager_password": os.getenv("SERVER_MANAGER_PASSWORD"),
    "server_manager_api_token": os.getenv("SERVER_MANAGER_API_TOKEN"),
    "payment_system_code": os.getenv("PAYMENT_SYSTEM_CODE"),
    "support_link": os.getenv("SUPPORT_LINK"),
    "support_username": os.getenv("SUPPORT_USERNAME"),
    "backup_dir": os.getenv("BACKUP_DIR"),
}

dbworker.CONFIG = CONFIG
buttons.CONFIG = CONFIG
smrequests.CONFIG = CONFIG

with open("texts.json", encoding="utf-8") as file_handler:
    text_mess = json.load(file_handler)
    texts_for_bot = text_mess

DBCONNECT = "data.sqlite"
BOTAPIKEY = CONFIG["tg_token"]

bot = AsyncTeleBot(CONFIG["tg_token"], state_storage=StateMemoryStorage())

DBHOST = CONFIG["db_host"]
DBUSER = CONFIG["db_user"]
DBPASSWORD = CONFIG["db_password"]
DBNAME = CONFIG["db_name"]

PAYMENT_SYSTEM_CODE = CONFIG["payment_system_code"]
SUPPORT_LINK = CONFIG["support_link"]
SUPPORT_USERNAME = CONFIG["support_username"]

BotCheck = TeleBot(BOTAPIKEY)


class MyStates(StatesGroup):
    findUserViaId = State()
    prepareUserForSendMessage = State()
    sendMessageToUser = State()
    sendMessageToAllUser = State()
    sendMessageToAmneziaUser = State()
    sendMessageToAllInactiveUser = State()
    sendMessageToLast50User = State()
    findUsersByName = State()
    switchActiveUserManual = State()
    updateAllUsers = State()
    update10Users = State()
    editUser = State()
    editUserResetTime = State()

    UserAddTimeDays = State()
    UserAddTimeHours = State()
    UserAddTimeMinutes = State()
    UserAddTimeApprove = State()

    AdminNewUser = State()

    EnterGiftSecret = State()


async def getTrialButtons():
    trialButtons = types.InlineKeyboardMarkup(row_width=1)
    trialButtons.add(
        types.InlineKeyboardButton(e.emojize(":mobile_phone: iOS (iPhone, iPad)"), callback_data="Init:iPhone"),
        types.InlineKeyboardButton(e.emojize(":mobile_phone: Android"), callback_data="Init:Android"),
        types.InlineKeyboardButton(e.emojize(":laptop: Windows"), callback_data="Init:Windows"),
        types.InlineKeyboardButton(e.emojize(":laptop: MacOS"), callback_data="Init:MacOS")
    )
    return trialButtons


async def sendPayMessage(chatId, additionalParam=''):
    print('sendPayMessage start')

    Butt_payment = types.InlineKeyboardMarkup()

    if additionalParam != '':
        additionalParam = ':' + additionalParam

    if chatId in CONFIG["admin_tg_id"]:
        Butt_payment.add(
            types.InlineKeyboardButton(e.emojize(f"Проверка оплаты: {int(getCostBySale(100))} руб."),
                                       callback_data="BuyMonth:100" + additionalParam))
    Butt_payment.add(
        types.InlineKeyboardButton(e.emojize(f"1 месяц: {int(getCostBySale(1))} руб."),
                                   callback_data="BuyMonth:1" + additionalParam))
    Butt_payment.add(
        types.InlineKeyboardButton(e.emojize(f"3 месяца: {int(getCostBySale(3))} руб. (-{getSale(3)}%)"),
                                   callback_data="BuyMonth:3" + additionalParam))
    Butt_payment.add(
        types.InlineKeyboardButton(e.emojize(f"6 месяцев: {int(getCostBySale(6))} руб. (-{getSale(6)}%)"),
                                   callback_data="BuyMonth:6" + additionalParam))
    Butt_payment.add(
        types.InlineKeyboardButton(e.emojize(f"1 год: {int(getCostBySale(12))} руб. (-{getSale(12)}%)"),
                                   callback_data="BuyMonth:12" + additionalParam))

    print('sendPayMessage send_message')

    await bot.send_message(chatId,
                           "<b>Оплатить подписку можно банковской картой</b>\n\nОплата производится официально через сервис ЮКасса\nМы не сохраняем, не передаем и не имеем доступа к данным карт, используемых для оплаты\n\n<a href='https://telegra.ph/Publichnaya-oferta-11-03-5'>Условия использования</a>\n\nВыберите период, на который хотите приобрести подписку:",
                           disable_web_page_preview=True, reply_markup=Butt_payment, parse_mode="HTML")
    print('sendPayMessage stop')


async def sendConfig(chatId):
    print('sendConfig get user_dat start')
    user_dat = await User.GetInfo(chatId)
    print('sendConfig get user_dat stop')
    if user_dat.trial_subscription == False:
        print('sendConfig send_message')
        await bot.send_message(chat_id=chatId,
                               text=f"Пожалуйста, выберите тип устройства, для которого нужна инструкция для подключения:",
                               parse_mode="HTML", reply_markup=await getTrialButtons())
    else:
        await bot.send_message(chat_id=chatId, text="Для этого необходимо оплатить подписку",
                               reply_markup=await main_buttons(user_dat))
        await sendPayMessage(chatId)


async def sendConfigAndInstructions(chatId, device='iPhone', type='xui'):
    user_dat = await User.GetInfo(chatId)
    tgId = str(user_dat.tgid)

    if type == 'xui':

        conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
        dbCur = conn.cursor(pymysql.cursors.DictCursor)
        dbCur.execute(f"select * from users_keys where tgid = %s and type = %s order by id desc limit 1",
                      (tgId, device))
        userKeyLog = dbCur.fetchone()
        dbCur.close()
        conn.close()

        if userKeyLog is not None and userKeyLog['user_key']:
            connectionLinks = {
                'success': True,
                'data': {
                    'link': userKeyLog['user_key']
                },
            }
        else:
            connectionLinks = await getConnectionLinks(tgId, device)
            if connectionLinks['success'] != True:
                connectionLinks = await getConnectionLinks(tgId, device)

        if connectionLinks['success']:
            data = connectionLinks['data']
            link = data['link']

            if userKeyLog is None and link:
                conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
                dbCur = conn.cursor(pymysql.cursors.DictCursor)
                dbCur.execute(f"insert into users_keys (tgid,type,user_key) values (%s,%s,%s)",
                              (tgId, device, link))
                conn.commit()
                dbCur.close()
                conn.close()

            additionalText = (
                "\r\n\r\n<b>Важно!</b>" \
                "\r\n<b>При первом подключении</b> ваш ключ может дойти на все серверы с задержкой <b>до 10 минут</b>." \
                "\r\nПожалуйста, подождите <b>10 минут</b> и переподключитесь (выключите и включите впн в приложении)")

            instructionIPhone = f"<b>Подключение VPN DUCKS на iOS</b>\n\r\n\r1. Установите приложение <a href=\"https://apps.apple.com/ru/app/streisand/id6450534064\">Streisand из AppStore</a> (если это приложение вам не подойдет, <a href=\"https://apps.apple.com/ru/app/v2raytun/id6476628951\">установите v2RayTun</a>)\n\r" \
                                f"2. Скопируйте ссылку (начинающуюся с vless://), прикрепленную ниже и вставьте в приложение Streisand, нажмите кнопку ➕ вверху, и затем \"Добавить из буфера\"\n\r" \
                                f"3. Дайте разрешения приложению Streisand на вставку файла\n\r" \
                                f"4. Включите VPN, нажав синюю кнопку и дайте разрешение на добавление конфигурации.\n\r\n\r" \
                                f"<b>Важная настройка!</b>\n\r" \
                                f"Откройте Настройки в нижнем правом углу приложения, затем выберете \"Туннель\": \"Постоянный тунель\" переведите в активное состояние и \"IP Settings\" поменяйте на IPv4. Готово 🎉\n\r\n\r" \
                                f"<a href=\"https://t.me/vpnducks_video/8\">Видео-инструкция</a>\n\r\n\r" \
                                f"Что-то не получилось или vpn работает не стабильно? Напишите {SUPPORT_USERNAME}, мы оперативно поможем 🙌🏻"
            instructionAndroid = f"<b>Подключение VPN DUCKS на Android</b>\n\r\n\r1. Установите приложение <a href='https://play.google.com/store/apps/details/v2rayNG?id=com.v2ray.ang'>v2rayNG из Google Play</a>. Если у вас нет Google Play, напишите {SUPPORT_USERNAME} и мы отправим файл для установки приложения\n\r2. Скопируйте ссылку (начинающуюся с vless://), прикрепленную ниже, перейдите в установленное в первом пункте приложение v2rayNG, внутри приложения нажмите кнопку ➕, находящуюся вверху справа, затем \"Импорт из буфера обмена\"\n\r3. Нажмите на кнопку ▶️ внизу справа и выдайте приложению требуемые разрешения. Готово! 🎉\n\r\n\r<a href=\"https://t.me/vpnducks_video/7\">Видео-инструкция</a>\n\r\n\rЧто-то не получилось или vpn работает не стабильно? Напишите {SUPPORT_USERNAME}, мы оперативно поможем 🙌🏻"
            instructionWindows = f"<b>Подключение VPN DUCKS на Windows</b>\n\r\n\r1. Скопируйте ссылку (начинающуюся с vless://), прикрепленную ниже\n\r2. Следуйте инструкции https://telegra.ph/Instrukciya-po-ustanovke-Ducks-VPN-na-Windows-10-22\n\r\n\rЧто-то не получилось или vpn работает не стабильно? Напишите {SUPPORT_USERNAME}, мы оперативно поможем 🙌🏻"
            instructionMacOS = f"<b>Подключение VPN DUCKS на MacOS</b>\n\r\n\r1. Установите <a href='https://apps.apple.com/ru/app/foxray/id6448898396'>FoXray</a>\n\r2. Скопируйте ссылку (начинающуюся с vless://), прикрепленную ниже, перейдите в установленное в первом пункте приложение, внутри приложения импортируйте строку\n\r\n\rГотово! 🎉\n\r\n\rЧто-то не получилось или vpn работает не стабильно? Напишите {SUPPORT_USERNAME}, мы оперативно поможем 🙌🏻"
            if (device == "iPhone"):
                await bot.send_message(chat_id=user_dat.tgid, text=e.emojize(instructionIPhone), parse_mode="HTML",
                                       disable_web_page_preview=True,
                                       reply_markup=await main_buttons(user_dat, True))
            if (device == "Android"):
                await bot.send_message(chat_id=user_dat.tgid, text=e.emojize(instructionAndroid), parse_mode="HTML",
                                       disable_web_page_preview=True,
                                       reply_markup=await main_buttons(user_dat, True))
            if (device == "Windows"):
                await bot.send_message(chat_id=user_dat.tgid, text=e.emojize(instructionWindows), parse_mode="HTML",
                                       disable_web_page_preview=True,
                                       reply_markup=await main_buttons(user_dat, True))
            if (device == "MacOS"):
                await bot.send_message(chat_id=user_dat.tgid, text=e.emojize(instructionMacOS), parse_mode="HTML",
                                       disable_web_page_preview=True,
                                       reply_markup=await main_buttons(user_dat, True))

            await bot.send_message(chat_id=user_dat.tgid, text=f"<blockquote>{link}</blockquote>", parse_mode="HTML",
                                   reply_markup=await main_buttons(user_dat, True))

            if userKeyLog is None:
                await bot.send_message(chat_id=user_dat.tgid, text=e.emojize(additionalText), parse_mode="HTML",
                                       reply_markup=await main_buttons(user_dat, True))
        else:
            await bot.send_message(user_dat.tgid,
                                   emoji.emojize(
                                       f"Пожалуйста, попробуйте еще раз :smiling_face_with_smiling_eyes:\n\rЗа помощью обратитесь к {SUPPORT_USERNAME}"),
                                   reply_markup=await main_buttons(user_dat, True), parse_mode="HTML")
    elif type == 'amnezia':
        try:
            fileResponse = await getAmneziaConnectionFile(tgId)
            if fileResponse['success']:
                data = fileResponse['data']
                configFull = data['file']

                instructionIPhone = f"<b>Подключение VPN DUCKS на iOS</b>\n\r\n\r1. Установите приложение <a href='https://apps.apple.com/us/app/amneziavpn/id1600529900'>Amnezia VPN для iOS из AppStore</a>. Приложение удалено из российского AppStore. Для того, чтобы скачать приложение, регион AppStore необходимо сменить <a href=\"https://journal.tinkoff.ru/apple-region/\">по инструкции</a> на другую страну\n\r2. Откройте прикрепленный выше файл конфигурации vpnducks_{str(user_dat.tgid)}.conf\n\r3. Нажмите на иконку поделиться в левом нижнем углу\n\r4. Найдите AmneziaWG среди предложенных приложений и кликните по нему\n\r5. Откроется приложение AmneziaWG и спросит о добавлении конфигурации, согласитесь на добавление конфигурации\n\r6. Нажмите на кнопку подключиться на главном экране приложения. Готово\n\r\n\rЧто-то не получилось? Напишите нам {SUPPORT_USERNAME}"
                instructionAndroid = f"<b>Подключение VPN DUCKS на Android</b>\n\r\n\r1. Установите приложение <a href='https://play.google.com/store/apps/details?id=org.amnezia.vpn'>AmneziaVPN для Android из Google Play</a>\n\r2. Откройте прикрепленный выше файл конфигурации vpnducks_{str(user_dat.tgid)}.conf с помощью приложения AmneziaVPN\n\r3. Откроется приложение AmneziaVPN, нажмите на кнопку подключиться\n\r4. Нажмите на большую круглую кнопку подключиться на главном экране приложения и разрешите смартфону установить VPN соединение. Готово\n\r\n\rЧто-то не получилось? Напишите нам {SUPPORT_USERNAME}"
                instructionWindows = f"<b>Подключение VPN DUCKS на Windows</b>\n\r\n\r1. Установите <a href='https://github.com/amnezia-vpn/amnezia-client/releases/download/4.7.0.0/AmneziaVPN_4.7.0.0_x64.exe'>AmneziaVPN</a>\n\r2. Установите скачанную программу\n\r3.Откройте прикрепленный выше файл конфигурации vpnducks_{str(user_dat.tgid)}.conf в программе AmneziaVPN\n\r4. Нажмите на кнопку подключиться\n\r5. Нажмите на большую круглую кнопку подключиться на главном экране программы и разрешите установить VPN соединение. Готово\n\r\n\rЧто-то не получилось? Напишите нам {SUPPORT_USERNAME}"
                instructionMacOS = f"<b>Подключение VPN DUCKS на MacOS</b>\n\r\n\r1. Установите <a href='https://github.com/amnezia-vpn/amnezia-client/releases/download/4.7.0.0/AmneziaVPN_4.7.0.0.dmg'>AmneziaVPN</a>\n\r2. Установите скачанную программу\n\r3.Откройте прикрепленный выше файл конфигурации vpnducks_{str(user_dat.tgid)}.conf в программе AmneziaVPN\n\r4. Нажмите на кнопку подключиться\n\r5. Нажмите на большую круглую кнопку подключиться на главном экране программы и разрешите установить VPN соединение. Готово\n\r\n\rЧто-то не получилось? Напишите нам {SUPPORT_USERNAME}"
                if (device == "iPhone"):
                    await bot.send_document(chat_id=user_dat.tgid, caption=e.emojize(instructionIPhone),
                                            parse_mode="HTML",
                                            reply_markup=await main_buttons(user_dat, True), document=configFull,
                                            visible_file_name=f"vpnducks_{str(user_dat.tgid)}.conf")
                if (device == "Android"):
                    await bot.send_document(chat_id=user_dat.tgid, caption=e.emojize(instructionAndroid),
                                            parse_mode="HTML",
                                            reply_markup=await main_buttons(user_dat, True), document=configFull,
                                            visible_file_name=f"vpnducks_{str(user_dat.tgid)}.conf")
                if (device == "Windows"):
                    await bot.send_document(chat_id=user_dat.tgid, caption=e.emojize(instructionWindows),
                                            parse_mode="HTML",
                                            reply_markup=await main_buttons(user_dat, True), document=configFull,
                                            visible_file_name=f"vpnducks_{str(user_dat.tgid)}.conf")
                if (device == "MacOS"):
                    await bot.send_document(chat_id=user_dat.tgid, caption=e.emojize(instructionMacOS),
                                            parse_mode="HTML",
                                            reply_markup=await main_buttons(user_dat, True), document=configFull,
                                            visible_file_name=f"vpnducks_{str(user_dat.tgid)}.conf")
            else:
                await bot.send_message(user_dat.tgid,
                                       emoji.emojize(
                                           f"Пожалуйста, попробуйте еще раз :smiling_face_with_smiling_eyes:\n\rЗа помощью обратитесь к {SUPPORT_USERNAME}"),
                                       reply_markup=await main_buttons(user_dat, True), parse_mode="HTML")
        except:
            await bot.send_message(user_dat.tgid,
                                   "Выдать ключ не получилось :(\r\n\r\nСмените протокол. Нажмите на Помощь -> Сменить протокол",
                                   reply_markup=await buttons.admin_buttons())


async def addTrialForReferrerByUserId(userId):
    userDat = await User.GetInfo(userId)
    try:
        if userDat.referrer_id and userDat.referrer_id > 0:
            referrer_id = int(userDat.referrer_id)
        else:
            referrer_id = 0
    except TypeError:
        referrer_id = 0

    if referrer_id != 0:
        userDatReferrer = await User.GetInfo(userDat.referrer_id)
        addTrialTime = 30 * CONFIG['count_free_from_referrer'] * 60 * 60 * 24

        conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
        dbCur = conn.cursor(pymysql.cursors.DictCursor)
        dbCur.execute(
            f"Update userss set subscription=subscription+{addTrialTime}, banned=false where tgid={referrer_id}")
        conn.commit()
        dbCur.close()
        conn.close()

        userName = userDat.fullname
        if userDat.username:
            userName = f"{userName} ({userDat.username})"
        await bot.send_message(userDat.referrer_id,
                               f"<b>Поздравляем!</b>\nПользователь {userName}, пришедший по вашей ссылке, оплатил подписку, вам добавлен <b>+1 месяц</b> бесплатного доступа",
                               reply_markup=await main_buttons(userDatReferrer, True), parse_mode="HTML")

        for admin in CONFIG["admin_tg_id"]:
            await bot.send_message(admin,
                                   f"Оплативший пользователь пришел от {userDat.username} ( {userDat.referrer_id} )",
                                   parse_mode="HTML")


async def AddTimeToUser(tgid, timetoadd):
    userdat = await User.GetInfo(tgid)

    if int(userdat.subscription) < int(time.time()):
        conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
        dbCur = conn.cursor(pymysql.cursors.DictCursor)
        dbCur.execute(f"Update userss set subscription = %s, banned=false where tgid=%s",
                      (str(int(time.time()) + timetoadd), userdat.tgid))
        dbCur.execute(f"DELETE FROM notions where tgid=%s", (userdat.tgid))
        conn.commit()
        dbCur.close()
        conn.close()

        await switchUserActivity(str(userdat.tgid), True)
        await switchUserActivityQueue(str(userdat.tgid), True)

        await bot.send_message(userdat.tgid, e.emojize(
            f'<b>Информация о подписке обновлена</b>\n\nНеобходимо отключить и заново включить соединение с vpn в приложении.\n\r\n\rЧто-то не получилось? Напишите нам {SUPPORT_USERNAME}'),
                               parse_mode="HTML", reply_markup=await main_buttons(userdat, True))
    else:
        conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
        dbCur = conn.cursor(pymysql.cursors.DictCursor)
        dbCur.execute(f"Update userss set subscription = %s where tgid=%s",
                      (str(int(userdat.subscription) + timetoadd), userdat.tgid))
        conn.commit()
        dbCur.close()
        conn.close()

        await switchUserActivity(str(userdat.tgid), True)
        await switchUserActivityQueue(str(userdat.tgid), True)
        await bot.send_message(userdat.tgid, e.emojize(
            'Информация о подписке обновлена'), parse_mode="HTML", reply_markup=await main_buttons(userdat, True))


def addTrialForReferrerByUserIdSync(userId):
    userDat = asyncio.run(User.GetInfo(userId))
    try:
        referrer_id = userDat.referrer_id if userDat.referrer_id else 0
    except TypeError:
        referrer_id = 0

    if referrer_id and referrer_id != 0:
        userDatReferrer = asyncio.run(User.GetInfo(userDat.referrer_id))
        if userDatReferrer.subscription != None:
            addTrialTime = 30 * CONFIG['count_free_from_referrer'] * 60 * 60 * 24
            AddTimeToUserSync(referrer_id, addTrialTime)
            BotCheck.send_message(userDat.referrer_id,
                                  f"<b>Поздравляем!</b>\nПользователь, пришедший по вашей ссылке, оплатил подписку, вам добавлен <b>+1 месяц</b> бесплатного доступа",
                                  reply_markup=asyncio.run(main_buttons(userDatReferrer, True)), parse_mode="HTML")

            for admin in CONFIG["admin_tg_id"]:
                BotCheck.send_message(admin,
                                      f"Оплативший пользователь {userDat.username} ({userDat.tgid}) пришел от {userDatReferrer.username} ( {userDatReferrer.tgid} )",
                                      parse_mode="HTML")


def AddTimeToUserSync(tgid, timetoadd):
    userdat = asyncio.run(User.GetInfo(tgid))
    if userdat.subscription == None:
        return
    if int(userdat.subscription) < int(time.time()):
        conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
        dbCur = conn.cursor(pymysql.cursors.DictCursor)
        dbCur.execute(f"Update userss set subscription = %s, banned=false where tgid=%s",
                      (str(int(time.time()) + timetoadd), userdat.tgid))
        dbCur.execute(f"DELETE FROM notions where tgid=%s", (userdat.tgid))
        conn.commit()
        dbCur.close()
        conn.close()

        asyncio.run(switchUserActivity(str(userdat.tgid), True))
        asyncio.run(switchUserActivityQueue(str(userdat.tgid), True))

        BotCheck.send_message(userdat.tgid, e.emojize(
            f'<b>Информация о подписке обновлена</b>\n\nНеобходимо отключить и заново включить соединение с vpn в приложении.\n\r\n\rЧто-то не получилось? Напишите нам {SUPPORT_USERNAME}'),
                              parse_mode="HTML", reply_markup=asyncio.run(main_buttons(userdat, True)))
    else:
        conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
        dbCur = conn.cursor(pymysql.cursors.DictCursor)
        dbCur.execute(f"Update userss set subscription = %s where tgid=%s",
                      (str(int(userdat.subscription) + timetoadd), userdat.tgid))
        conn.commit()
        dbCur.close()
        conn.close()

        asyncio.run(switchUserActivity(str(userdat.tgid), True))
        asyncio.run(switchUserActivityQueue(str(userdat.tgid), True))
        BotCheck.send_message(userdat.tgid, e.emojize(
            'Информация о подписке обновлена'), parse_mode="HTML",
                              reply_markup=asyncio.run(main_buttons(userdat, True)))


async def AddTimeToUserAsync(tgid, timetoadd):
    userdat = await User.GetInfo(tgid)
    if userdat.subscription == None:
        return
    if int(userdat.subscription) < int(time.time()):
        conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
        dbCur = conn.cursor(pymysql.cursors.DictCursor)
        dbCur.execute(f"Update userss set subscription = %s, banned=false where tgid=%s",
                      (str(int(time.time()) + timetoadd), userdat.tgid))
        dbCur.execute(f"DELETE FROM notions where tgid=%s", (userdat.tgid))
        conn.commit()
        dbCur.close()
        conn.close()

        await switchUserActivity(str(userdat.tgid), True)
        await switchUserActivityQueue(str(userdat.tgid), True)

        await bot.send_message(userdat.tgid, e.emojize(
            f'<b>Информация о подписке обновлена</b>\n\nНеобходимо отключить и заново включить соединение с vpn в приложении.\n\r\n\rЧто-то не получилось? Напишите нам {SUPPORT_USERNAME}'),
                               parse_mode="HTML", reply_markup=await main_buttons(userdat, True))
    else:
        conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
        dbCur = conn.cursor(pymysql.cursors.DictCursor)
        dbCur.execute(f"Update userss set subscription = %s where tgid=%s",
                      (str(int(userdat.subscription) + timetoadd), userdat.tgid))
        conn.commit()
        dbCur.close()
        conn.close()

        await switchUserActivity(str(userdat.tgid), True)
        await switchUserActivityQueue(str(userdat.tgid), True)
        await bot.send_message(userdat.tgid, e.emojize(
            'Информация о подписке обновлена'), parse_mode="HTML",
                               reply_markup=await main_buttons(userdat, True))


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


def randomword(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


def paymentSuccess(paymentId):
    conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
    dbCur = conn.cursor(pymysql.cursors.DictCursor)
    dbCur.execute(f"UPDATE payments SET status='success' WHERE bill_id = %s", (paymentId,))
    conn.commit()
    dbCur.execute(f"SELECT * FROM payments where bill_id=%s", (paymentId,))
    log = dbCur.fetchone()
    dbCur.close()
    conn.close()

    tgid = log['tgid']
    amount = log['amount']
    addTimeSubscribe = log['time_to_add']
    additional = log['additional']
    paymentsCount = 0

    try:
        # находим прошлые оплаты
        conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
        dbCur = conn.cursor(pymysql.cursors.DictCursor)
        dbCur.execute(f"select COUNT(*) as count from payments where tgid=%s and status='success'", (tgid,))
        paymentsConn = dbCur.fetchone()
        paymentsCount = paymentsConn['count']
        dbCur.close()
        conn.close()
    except Exception as err:
        print('***--- FOUND PAYMENTS ERROR ---***')
        print(err)
        print(traceback.format_exc())
        pass

    user_dat = asyncio.run(User.GetInfo(tgid))

    if additional == 'gift':
        secret = randomword(10)
        giftId = asyncio.run(user_dat.newGift(paymentId, secret))
        BotCheck.send_message(tgid, e.emojize(texts_for_bot["success_pay_gift_message"]), parse_mode="HTML")

        giftLink = f"https://t.me/{CONFIG['bot_name']}?start=" + 'gift' + str(giftId)
        msg = e.emojize(f"<b>Ссылка на подарок и секретный код активации</b>\n\r\n\r" \
                        f":wrapped_gift: Скопируйте ссылку на подарок и отправьте её получателю.\n\r" \
                        f"Когда обладатель подарка перейдет по ссылке, ему <b>нужно будет нажать кнопку \"Запустить\"</b>, после этого мы поздравим его и продлим его подписку VPN Ducks!\n\r\n\r" \
                        f"Подарочная ссылка (кликните по ней, чтобы скопировать): \n\r\n\r<b><code>{giftLink}</code></b>\n\r\n\r" \
                        f"Обязательно передайте получателю подарка секретный код для активации подарка (кликните по нему, чтобы скопировать):\n\r\n\r" \
                        f"<b><code>{secret}</code></b>"
                        )
        BotCheck.send_message(tgid, msg, reply_markup=asyncio.run(buttons.main_buttons(user_dat, True)),
                              parse_mode="HTML")

        month = addTimeSubscribe / (30 * 24 * 60 * 60)
        for admin in CONFIG["admin_tg_id"]:
            BotCheck.send_message(admin,
                                  f"Новая оплата ПОДАРКА от {user_dat.username} ( {user_dat.tgid} ) на <b>{month}</b> мес. : {amount} руб.",
                                  parse_mode="HTML")
        return

    try:
        dateto = datetime.utcfromtimestamp(
            int(user_dat.subscription) + int(addTimeSubscribe) + CONFIG["UTC_time"] * 3600).strftime(
            '%d.%m.%Y %H:%M')
        BotCheck.send_message(tgid,
                              e.emojize(texts_for_bot["success_pay_message"]),
                              reply_markup=asyncio.run(buttons.main_buttons(user_dat, True)), parse_mode="HTML")
    except Exception as err:
        print('***--- PAY MESSAGE 1 ERROR ---***')
        print(err)
        print(traceback.format_exc())
        pass

    try:
        AddTimeToUserSync(tgid, addTimeSubscribe)
    except Exception as err:
        print('***--- ADD TIME ERROR ---***')
        print(err)
        print(traceback.format_exc())
        pass

    try:
        Butt_reffer = types.InlineKeyboardMarkup()
        Butt_reffer.add(
            types.InlineKeyboardButton(
                e.emojize(f"Пригласить друга :wrapped_gift:"),
                callback_data="Referrer"))
        BotCheck.send_message(tgid, e.emojize(texts_for_bot["success_pay_message_2"]),
                              reply_markup=Butt_reffer, parse_mode="HTML")
    except Exception as err:
        print('***--- PAY MESSAGE 2 ERROR ---***')
        print(err)
        print(traceback.format_exc())
        pass

    month = addTimeSubscribe / (30 * 24 * 60 * 60)
    for admin in CONFIG["admin_tg_id"]:
        BotCheck.send_message(admin,
                              f"Новая оплата подписки от {user_dat.username} ( {user_dat.tgid} ) на <b>{month}</b> мес. : {amount} руб.",
                              parse_mode="HTML")

    try:
        if paymentsCount <= 1:
            addTrialForReferrerByUserIdSync(tgid)
    except Exception as err:
        print('***--- ADD TRIAL TO REFERRER AFTER PAY ERROR ---***')
        print(err)
        print(traceback.format_exc())
        pass


async def startSendRegistered(tgId):
    user_dat = await User.GetInfo(tgId)
    await sendConfig(tgId)
    await bot.send_message(tgId, e.emojize("Инструкция по установке :index_pointing_up:"),
                           parse_mode="HTML",
                           reply_markup=await main_buttons(user_dat))


async def startSendNotRegistered(tgId, userName, fullName, messageText=''):
    user_dat = await User.GetInfo(tgId)

    try:
        username = "@" + str(userName)
    except:
        username = str(tgId)

    if (username == "@None"):
        username = str(tgId)

    # Определяем referrer_id
    arg_referrer_id = messageText[7:]
    referrer_id = None if arg_referrer_id is None else arg_referrer_id
    if not referrer_id:
        referrer_id = 0

    await user_dat.Adduser(tgId, username, fullName, referrer_id)

    # Обработка реферера
    if referrer_id and referrer_id != user_dat.tgid:
        # Пользователь пришел по реферальной ссылке, обрабатываем это
        referrerUser = await User.GetInfo(referrer_id)

        comingUserInfo = fullName
        if str(userName) != 'None':
            comingUserInfo = comingUserInfo + ' ( ' + username + ' )'

        await bot.send_message(referrer_id,
                               f"По вашей ссылке пришел новый пользователь: {comingUserInfo}\nВы получите +1 месяц бесплатного доступа, если он оплатит подписку",
                               reply_markup=await main_buttons(referrerUser))

        for admin in CONFIG["admin_tg_id"]:
            await bot.send_message(admin,
                                   f"По ссылке от пользователя {referrerUser.username} ( {referrer_id} ) пришел новый пользователь: {comingUserInfo}")

    user_dat = await User.GetInfo(tgId)
    trialText = e.emojize(f"Привет, {user_dat.fullname}!\n\r\n\r" \
                          f"🎁 <b>Дарим вам 7 дней бесплатного доступа!</b>\n\r\n\r" \
                          f"Пожалуйста, выберите тип телефона или планшета, для которого нужна инструкция для подключения:\n\r")

    trialButtons = await getTrialButtons()

    await bot.send_message(tgId, trialText, parse_mode="HTML", reply_markup=trialButtons)

    await addUser(tgId, username)
    await addUserQueue(tgId, username)


@bot.message_handler(commands=['start'])
async def start(message: types.Message):
    if message.chat.type == "private":
        await bot.delete_state(message.from_user.id)
        user_dat = await User.GetInfo(message.chat.id)

        print('gift start')
        print(message.text)
        try:
            if message.text.find('gift') >= 0:
                print('gift send')
                await bot.set_state(message.chat.id, MyStates.EnterGiftSecret)

                async with bot.retrieve_data(message.from_user.id) as data:
                    data['giftid'] = message.text.replace('/start gift', '')

                await bot.send_message(message.chat.id, e.emojize(f'Для вас подготовлен подарок! :wrapped_gift:'),
                                       parse_mode="HTML",
                                       reply_markup=await main_buttons(user_dat))
                buttSkip = types.ReplyKeyboardMarkup(resize_keyboard=True)
                buttSkip.add(types.KeyboardButton(e.emojize(f"Отменить :right_arrow_curving_left:")))
                await bot.send_message(message.chat.id, "Введите секретный код подарка:", reply_markup=buttSkip)
                return
            print('gift stop')
        except Exception as err:
            print('***--- GIFT ERROR ---***')
            print(err)
            print(traceback.format_exc())
            pass
        if user_dat.registered:
            await startSendRegistered(message.chat.id)
        else:
            await startSendNotRegistered(message.chat.id, message.from_user.username, message.from_user.full_name,
                                         message.text)


@bot.message_handler(state=MyStates.EnterGiftSecret, content_types=["text"])
async def Work_with_Message(m: types.Message):
    userDat = await User.GetInfo(m.from_user.id)
    if e.demojize(m.text) == "Отменить :right_arrow_curving_left:":
        await bot.reset_data(m.from_user.id)
        await bot.delete_state(m.from_user.id)
        await bot.send_message(m.from_user.id, "Вернули вас назад!", reply_markup=await main_buttons(userDat, True))
        if not userDat.registered:
            await startSendNotRegistered(m.chat.id, m.from_user.username, m.from_user.full_name, '/start')
        return

    giftId = 0
    async with bot.retrieve_data(m.from_user.id) as data:
        giftId = data['giftid']

    secretCode = m.text
    print('secretCode: ' + secretCode)

    conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
    dbCur = conn.cursor(pymysql.cursors.DictCursor)
    dbCur.execute(f"select * from gifts where id = %s and secret = %s and status='new' order by id desc limit 1",
                  (giftId, secretCode))
    giftLog = dbCur.fetchone()
    dbCur.close()
    conn.close()

    if giftLog is not None:
        conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
        dbCur = conn.cursor(pymysql.cursors.DictCursor)
        dbCur.execute(f"select * from payments where bill_id = %s and additional='gift' order by id desc limit 1",
                      (giftLog['payment_id']))
        paymentLog = dbCur.fetchone()
        dbCur.close()
        conn.close()
        if paymentLog is not None:
            if not userDat.registered:
                await startSendNotRegistered(m.chat.id, m.from_user.username, m.from_user.full_name, '/start')
            addTimeSubscribe = paymentLog['time_to_add']
            await AddTimeToUserAsync(m.chat.id, addTimeSubscribe)

            monthСount = int(addTimeSubscribe / (30 * 24 * 60 * 60))
            print(addTimeSubscribe)
            print(monthСount)
            if monthСount == 1:
                monthText = '1 месяц'
            elif monthСount == 12:
                monthText = '1 год'
            else:
                monthText = str(monthСount) + ' месяцев'

            await bot.send_message(m.from_user.id, e.emojize(f'<b>Поздравляем!</b>\r\n\r\n'
                                                             f'Подарок на {monthText} подписки на VPN DUCKS активирован :wrapped_gift:'),
                                   parse_mode="HTML",
                                   reply_markup=await main_buttons(userDat, True))

            Butt_reffer = types.InlineKeyboardMarkup()
            Butt_reffer.add(
                types.InlineKeyboardButton(
                    e.emojize(f"Пригласить друга :wrapped_gift:"),
                    callback_data="Referrer"))
            BotCheck.send_message(m.from_user.id, e.emojize(texts_for_bot["success_pay_message_2"]),
                                  reply_markup=Butt_reffer, parse_mode="HTML")

            conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
            dbCur = conn.cursor(pymysql.cursors.DictCursor)
            dbCur.execute(f"update gifts set status='success', recipient_tgid=%s where id = %s",
                          (m.chat.id, giftId))
            conn.commit()
            dbCur.close()
            conn.close()

        else:
            await bot.send_message(m.from_user.id, f'Подарок не найден :(',
                                   parse_mode="HTML",
                                   reply_markup=await main_buttons(userDat, True))

            if not userDat.registered:
                await startSendNotRegistered(m.chat.id, m.from_user.username, m.from_user.full_name, '/start')
    else:
        await bot.send_message(m.from_user.id, f'Подарок не найден :(',
                               parse_mode="HTML",
                               reply_markup=await main_buttons(userDat, True))
        if not userDat.registered:
            await startSendNotRegistered(m.chat.id, m.from_user.username, m.from_user.full_name, '/start')

    await bot.reset_data(m.from_user.id)
    await bot.delete_state(m.from_user.id)


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
        await bot.send_message(m.from_user.id, "Вы уверены что хотите сбросить время для этого пользователя?",
                               reply_markup=Butt_skip)
        return


@bot.message_handler(state=MyStates.editUserResetTime, content_types=["text"])
async def Work_with_Message(m: types.Message):
    async with bot.retrieve_data(m.from_user.id) as data:
        tgid = data['usertgid']

    if e.demojize(m.text) == "Да":
        conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
        dbCur = conn.cursor(pymysql.cursors.DictCursor)
        dbCur.execute(f"Update userss set subscription = %s, banned=false where tgid=%s",
                      (str(int(time.time())), tgid))
        conn.commit()
        dbCur.close()
        conn.close()

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
                           f"Пользователю {str(tgid)} добавится:\n\nДни: {str(days)}\nЧасы: {str(hours)}\nМинуты: {str(minutes)}\n\nВсе верно?",
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

        userDat = await User.GetInfo(tgid)
        await bot.send_message(chat_id=tgid,
                               text=f"Поздравляем!\n\nМы дарим к вашей подписке: {days} дней {hours} часов {minutes} минут",
                               reply_markup=await main_buttons(userDat))
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


@bot.message_handler(state=MyStates.sendMessageToAllUser, content_types=["text"])
async def Work_with_Message(m: types.Message):
    if e.demojize(m.text) == "Назад :right_arrow_curving_left:":
        await bot.delete_state(m.from_user.id)
        await bot.send_message(m.from_user.id, "Вернул вас назад!", reply_markup=await buttons.admin_buttons())
        return

    user_dat = await User.GetInfo(m.from_user.id)
    allusers = await user_dat.GetAllUsers()

    for i in allusers:
        if i['banned'] == False:
            try:
                await bot.send_message(i['tgid'], e.emojize(m.text), parse_mode="HTML")
            except ApiTelegramException as exception:
                print("sendMessageToAllUser")
                print(exception.description)
                pass

    await bot.delete_state(m.from_user.id)
    await bot.send_message(m.from_user.id, "Сообщения отправлены", reply_markup=await buttons.admin_buttons())
    return


@bot.message_handler(state=MyStates.sendMessageToAmneziaUser, content_types=["text"])
async def Work_with_Message(m: types.Message):
    if e.demojize(m.text) == "Назад :right_arrow_curving_left:":
        await bot.delete_state(m.from_user.id)
        await bot.send_message(m.from_user.id, "Вернул вас назад!", reply_markup=await buttons.admin_buttons())
        return

    user_dat = await User.GetInfo(m.from_user.id)
    allusers = await user_dat.GetAllUsers()

    for i in allusers:
        if i['banned'] == False and i['type'] == 'amnezia':
            try:
                await bot.send_message(i['tgid'], e.emojize(m.text), parse_mode="HTML")
            except ApiTelegramException as exception:
                print("sendMessageToAmneziaUser")
                print(exception.description)
                pass

    await bot.delete_state(m.from_user.id)
    await bot.send_message(m.from_user.id, "Сообщения отправлены", reply_markup=await buttons.admin_buttons())
    return


@bot.message_handler(state=MyStates.sendMessageToAllInactiveUser, content_types=["text"])
async def Work_with_Message(m: types.Message):
    if e.demojize(m.text) == "Назад :right_arrow_curving_left:":
        await bot.delete_state(m.from_user.id)
        await bot.send_message(m.from_user.id, "Вернул вас назад!", reply_markup=await buttons.admin_buttons())
        return

    user_dat = await User.GetInfo(m.from_user.id)
    allusers = await user_dat.GetAllUsersWithoutSub()

    for i in allusers:
        try:
            userDat = await User.GetInfo(i['tgid'])
            await bot.send_message(i['tgid'], e.emojize(m.text), parse_mode="HTML",
                                   reply_markup=await main_buttons(userDat, True))
        except ApiTelegramException as exception:
            print("sendMessageToAllInactiveUser")
            print(exception.description)
            pass
        except Exception as err:
            print(err)
            print(traceback.format_exc())
            pass

    await bot.delete_state(m.from_user.id)
    await bot.send_message(m.from_user.id, "Сообщения отправлены", reply_markup=await buttons.admin_buttons())
    return


@bot.message_handler(state=MyStates.sendMessageToLast50User, content_types=["text"])
async def Work_with_Message(m: types.Message):
    if e.demojize(m.text) == "Назад :right_arrow_curving_left:":
        await bot.delete_state(m.from_user.id)
        await bot.send_message(m.from_user.id, "Вернул вас назад!", reply_markup=await buttons.admin_buttons())
        return

    conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
    dbCur = conn.cursor(pymysql.cursors.DictCursor)
    dbCur.execute(f"SELECT * FROM userss order by id desc limit 50")
    log = dbCur.fetchall()
    dbCur.close()
    conn.close()

    for i in log:
        try:
            supportButtons = types.InlineKeyboardMarkup(row_width=1)
            supportButtons.add(
                types.InlineKeyboardButton(emoji.emojize(":woman_technologist: Чат с поддержкой"),
                                           url=SUPPORT_LINK),
            )

            await bot.send_message(i['tgid'], e.emojize(m.text), parse_mode="HTML",
                                   reply_markup=supportButtons)

        except Exception as err:
            print("sendMessageToLast50Users")
            print(err)
            print(traceback.format_exc())
            pass

    await bot.delete_state(m.from_user.id)
    await bot.send_message(m.from_user.id, "Сообщения отправлены", reply_markup=await buttons.admin_buttons())
    return


@bot.message_handler(state=MyStates.findUsersByName, content_types=["text"])
async def Work_with_Message(m: types.Message):
    if e.demojize(m.text) == "Назад :right_arrow_curving_left:":
        await bot.delete_state(m.from_user.id)
        await bot.send_message(m.from_user.id, "Вернул вас назад!", reply_markup=await buttons.admin_buttons())
        return

    user_dat = await User.GetInfo(m.from_user.id)
    allusers = await user_dat.GetAllUsers()
    for i in allusers:
        if i['username'] == m.text or i['username'] == '@' + m.text:
            try:
                await bot.send_message(m.from_user.id, "Пользователь найден:",
                                       reply_markup=await buttons.admin_buttons())
                await bot.send_message(m.from_user.id, f"{i['tgid']}", parse_mode="HTML")
                await bot.send_message(m.from_user.id, f"{i['username']}", parse_mode="HTML")
                await bot.send_message(m.from_user.id, f"Полное имя: {i['fullname']}", parse_mode="HTML")
                await bot.send_message(m.from_user.id,
                                       f"Подписка до: {datetime.utcfromtimestamp(int(i['subscription']) + CONFIG['UTC_time'] * 3600).strftime('%d.%m.%Y %H:%M')}",
                                       parse_mode="HTML")
                await bot.delete_state(m.from_user.id)
                return
            except ApiTelegramException as exception:
                print("sendMessageToAllInactiveUser")
                print(exception.description)
                pass

    await bot.send_message(m.from_user.id, "Пользователь не найден",
                           reply_markup=await buttons.admin_buttons())
    await bot.delete_state(m.from_user.id)
    return


@bot.message_handler(state=MyStates.switchActiveUserManual, content_types=["text"])
async def Work_with_Message(m: types.Message):
    if e.demojize(m.text) == "Назад :right_arrow_curving_left:":
        await bot.delete_state(m.from_user.id)
        await bot.send_message(m.from_user.id, "Вернул вас назад!", reply_markup=await buttons.admin_buttons())
        return

    user_dat = await User.GetInfo(m.from_user.id)
    allusers = await user_dat.GetAllUsers()
    for i in allusers:
        if i['username'] == m.text or i['username'] == '@' + m.text or i['tgid'] == m.text:
            try:
                await bot.send_message(m.from_user.id, "Пользователь найден:",
                                       reply_markup=await buttons.admin_buttons())
                await bot.send_message(m.from_user.id, f"{i['tgid']}", parse_mode="HTML")
                await bot.send_message(m.from_user.id, f"{i['username']}", parse_mode="HTML")
                await bot.send_message(m.from_user.id, f"Полное имя: {i['fullname']}", parse_mode="HTML")
                await bot.send_message(m.from_user.id,
                                       f"Подписка до: {datetime.utcfromtimestamp(int(i['subscription']) + CONFIG['UTC_time'] * 3600).strftime('%d.%m.%Y %H:%M')}",
                                       parse_mode="HTML")
                if i['banned'] == False:
                    await switchUserActivity(str(i['tgid']), True)
                    await switchUserActivityQueue(str(i['tgid']), True)
                    await bot.send_message(m.from_user.id, f"Пользователь активирован", parse_mode="HTML")
                else:
                    await bot.send_message(m.from_user.id, f"У пользователя закончилась подписка", parse_mode="HTML")

                await bot.delete_state(m.from_user.id)
                return
            except TypeError:
                await bot.send_message(m.from_user.id, f"Произошла какая-то ошибка", parse_mode="HTML")
                pass

    await bot.send_message(m.from_user.id, "Пользователь не найден",
                           reply_markup=await buttons.admin_buttons())
    await bot.delete_state(m.from_user.id)
    return


@bot.message_handler(state=MyStates.updateAllUsers, content_types=["text"])
async def Work_with_Message(m: types.Message):
    if e.demojize(m.text) == "Назад :right_arrow_curving_left:":
        await bot.delete_state(m.from_user.id)
        await bot.send_message(m.from_user.id, "Вернул вас назад!", reply_markup=await buttons.admin_buttons())
        return

    conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
    dbCur = conn.cursor(pymysql.cursors.DictCursor)
    dbCur.execute(f"SELECT * FROM userss order by id desc limit 1500")
    log = dbCur.fetchall()
    dbCur.close()
    conn.close()

    try:
        k = 1
        for i in log:
            print(k)
            user = await User.GetInfo(i['tgid'])
            timenow = int(time.time())
            if int(user.subscription) < timenow:
                await switchUserActivity(str(i['tgid']), False)
                await switchUserActivityQueue(str(i['tgid']), False)
            if int(user.subscription) >= timenow:
                await switchUserActivity(str(i['tgid']), True)
                await switchUserActivityQueue(str(i['tgid']), True)
            if k % 100 == 0:
                await bot.send_message(m.from_user.id, f"{k} пользователей отправлены в очередь",
                                       reply_markup=await buttons.admin_buttons())
            k = k + 1

    except Exception as err:
        print('UPDATE ALL USERS ERROR')
        print(err)
        print(traceback.format_exc())
        pass

    await bot.send_message(m.from_user.id, "Обновления запущены в очередь",
                           reply_markup=await buttons.admin_buttons())
    await bot.delete_state(m.from_user.id)
    return


@bot.message_handler(state=MyStates.update10Users, content_types=["text"])
async def Work_with_Message(m: types.Message):
    if e.demojize(m.text) == "Назад :right_arrow_curving_left:":
        await bot.delete_state(m.from_user.id)
        await bot.send_message(m.from_user.id, "Вернул вас назад!", reply_markup=await buttons.admin_buttons())
        return

    conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
    dbCur = conn.cursor(pymysql.cursors.DictCursor)
    dbCur.execute(f"SELECT * FROM userss order by id desc limit 10")
    log = dbCur.fetchall()
    dbCur.close()
    conn.close()

    try:
        for i in log:
            user = await User.GetInfo(i['tgid'])
            timenow = int(time.time())
            if int(user.subscription) < timenow:
                await switchUserActivity(str(i['tgid']), False)
                await switchUserActivityQueue(str(i['tgid']), False)
            if int(user.subscription) >= timenow:
                await switchUserActivity(str(i['tgid']), True)
                await switchUserActivityQueue(str(i['tgid']), True)

    except Exception as err:
        print('UPDATE 10 USERS ERROR')
        print(err)
        print(traceback.format_exc())
        pass

    await bot.send_message(m.from_user.id, "Обновления запущены в очередь",
                           reply_markup=await buttons.admin_buttons())
    await bot.delete_state(m.from_user.id)
    return


@bot.message_handler(state="*", content_types=["text"])
async def Work_with_Message(m: types.Message):
    print('Work_with_Message start')
    user_dat = await User.GetInfo(m.chat.id)

    if user_dat.registered == False:
        try:
            username = "@" + str(m.from_user.username)
        except:
            username = str(m.from_user.id)

        # Определяем referrer_id
        arg_referrer_id = m.text[7:]
        referrer_id = arg_referrer_id if arg_referrer_id != user_dat.tgid else 0

        await user_dat.Adduser(m.chat.id, username, m.from_user.full_name, referrer_id)
        await addUser(m.chat.id, username)
        await addUserQueue(m.chat.id, username)

        await bot.send_message(m.chat.id,
                               texts_for_bot["hello_message"],
                               parse_mode="HTML", reply_markup=await main_buttons(user_dat))
        return
    print('user_dat.CheckNewNickname start')
    await user_dat.CheckNewNickname(m)
    print('user_dat.CheckNewNickname stop')

    if (e.demojize(m.text) == "Наши преимущества :gem_stone:"
            or e.demojize(m.text) == "Почему стоит выбрать нас? :smiling_face_with_sunglasses:"):
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
                    if len(readymes) + len(
                            f"{i['fullname']} ({i['username']}|{str(i['tgid'])}) :check_mark_button:\n") > 4090:
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

        if e.demojize(m.text) == "Отправить сообщение всем пользователям :pencil:":
            await bot.set_state(m.from_user.id, MyStates.sendMessageToAllUser)
            await bot.send_message(m.from_user.id, "Введите сообщение:",
                                   reply_markup=await buttons.admin_buttons_back())
            return

        if e.demojize(m.text) == "Отправить сообщение всем пользователям Amnezia :pencil:":
            await bot.set_state(m.from_user.id, MyStates.sendMessageToAmneziaUser)
            await bot.send_message(m.from_user.id, "Введите сообщение:",
                                   reply_markup=await buttons.admin_buttons_back())
            return

        if e.demojize(m.text) == "Отправить сообщение всем неактивным пользователям :pencil:":
            await bot.set_state(m.from_user.id, MyStates.sendMessageToAllInactiveUser)
            await bot.send_message(m.from_user.id, "Введите сообщение:",
                                   reply_markup=await buttons.admin_buttons_back())
            return

        if e.demojize(
                m.text) == "Отправить сообщение всем неактивным пользователям (с кнопкой Активировать подписку) :pencil:":
            user_dat = await User.GetInfo(m.from_user.id)
            allusers = await user_dat.GetAllUsersWithoutSub()

            for i in allusers:
                try:
                    activateButtons = types.InlineKeyboardMarkup(row_width=1)
                    activateButtons.add(
                        types.InlineKeyboardButton(emoji.emojize(f"Активировать подписку :dizzy:"),
                                                   callback_data="toActivatePromo:3daysToInactive"),
                        types.InlineKeyboardButton(emoji.emojize(":woman_technologist: Чат с поддержкой"),
                                                   url=SUPPORT_LINK)
                    )
                    await bot.send_message(i['tgid'], emoji.emojize(texts_for_bot["not_active_activate"]),
                                           parse_mode="HTML",
                                           reply_markup=activateButtons)

                except ApiTelegramException as exception:
                    if (exception.description == 'Forbidden: bot was blocked by the user'):
                        conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
                        dbCur = conn.cursor(pymysql.cursors.DictCursor)
                        dbCur.execute(f"Update userss set blocked=true where tgid=%s", (i['tgid']))
                        conn.commit()
                        dbCur.close()
                        conn.close()
                    pass
                except Exception as err:
                    print(err)
                    print(traceback.format_exc())
                    pass

            await bot.delete_state(m.from_user.id)
            await bot.send_message(m.from_user.id, "Сообщения отправлены", reply_markup=await buttons.admin_buttons())
            return

        if e.demojize(m.text) == "Отправить напоминание о службе поддержки :pencil:":
            user_dat = await User.GetInfo(m.from_user.id)
            allusers = await user_dat.GetAllUsers()

            for i in allusers:
                try:
                    supportButtons = types.InlineKeyboardMarkup(row_width=1)
                    supportButtons.add(
                        types.InlineKeyboardButton(emoji.emojize(":woman_technologist: Чат с поддержкой"),
                                                   url=SUPPORT_LINK),
                        types.InlineKeyboardButton(emoji.emojize(f"Пригласить друга :wrapped_gift:"),
                                                   callback_data="Referrer"),
                    )
                    await bot.send_message(i['tgid'], emoji.emojize(texts_for_bot["notify_about_support"]),
                                           parse_mode="HTML",
                                           reply_markup=supportButtons)
                except Exception as err:
                    print("sendMessageAboutSupportToAllUser")
                    print(err)
                    print(traceback.format_exc())
                    pass

            await bot.send_message(m.from_user.id, "Сообщения отправлены", reply_markup=await buttons.admin_buttons())
            await bot.send_message(m.from_user.id, f"{len(allusers)} пользователям",
                                   reply_markup=await buttons.admin_buttons())

            return

        if e.demojize(m.text) == "Отправить сообщение последним 50 пользователям :pencil:":
            await bot.set_state(m.from_user.id, MyStates.sendMessageToLast50User)
            await bot.send_message(m.from_user.id, "Введите сообщение:",
                                   reply_markup=await buttons.admin_buttons_back())
            return

        if e.demojize(m.text) == "Поиск пользователя по никнейму :magnifying_glass_tilted_left:":
            await bot.set_state(m.from_user.id, MyStates.findUsersByName)
            await bot.send_message(m.from_user.id, "Введите никнейм пользователя:",
                                   reply_markup=await buttons.admin_buttons_back())
            return

        if e.demojize(m.text) == "Перезагрузить базу :optical_disk:":
            subprocess.call('sudo systemctl restart mysql\n', shell=True)
            await bot.send_message(m.from_user.id, "База перезагружена",
                                   reply_markup=await buttons.admin_buttons_back())
            return

        if e.demojize(m.text) == "Активировать пользователя вручную :man:":
            await bot.set_state(m.from_user.id, MyStates.switchActiveUserManual)
            await bot.send_message(m.from_user.id, "Введите никнейм или id пользователя:",
                                   reply_markup=await buttons.admin_buttons_back())
            return

        if e.demojize(m.text) == "Обновить последних 10 пользователей :man:":
            await bot.set_state(m.from_user.id, MyStates.update10Users)
            await bot.send_message(m.from_user.id,
                                   "Вы уверены, что хотите обновить последних 10 пользователей? Введите `Да`",
                                   reply_markup=await buttons.admin_buttons_back())
            return

        if e.demojize(m.text) == "Обновить всех пользователей :man:":
            await bot.set_state(m.from_user.id, MyStates.updateAllUsers)
            await bot.send_message(m.from_user.id, "Вы уверены, что хотите обновить всех? Введите `Да`",
                                   reply_markup=await buttons.admin_buttons_back())
            return

        if e.demojize(m.text) == "Добавить пользователя :plus:":
            await bot.send_message(m.from_user.id,
                                   "Введите имя для нового пользователя!\nМожно использовать только латинские символы и арабские цифры.",
                                   reply_markup=await buttons.admin_buttons_back())
            await bot.set_state(m.from_user.id, MyStates.AdminNewUser)
            return

    if e.demojize(m.text) == "Продлить подписку :money_bag:":
        await sendPayMessage(m.chat.id)
        return

    if e.demojize(m.text) == "Как подключить :gear:":
        print('Как подключить :gear:')
        await sendConfig(m.chat.id)
        return

    if (e.demojize(m.text) == "Пригласить :wrapped_gift:"
            or e.demojize(m.text) == "Пригласить :woman_and_man_holding_hands:"):
        countReferal = await user_dat.countReferrerByUser()
        refLink = f"https://t.me/{CONFIG['bot_name']}?start=" + str(user_dat.tgid)

        msg = e.emojize(f"<b>Реферальная программа</b>\n\r\n\r" \
                        f":wrapped_gift: Получите бесплатную подписку, приглашая друзей по реферальной ссылке. Они получат неделю VPN бесплатно, а если после этого оформят подписку, мы подарим вам за каждого друга +1 месяц подписки на VPN Ducks!\n\r\n\r" \
                        f"Ваша пригласительная ссылка (кликните по ней, чтобы скопировать): \n\r\n\r<b><code>{refLink}</code></b>" \
                        f"\n\r\n\rПользователей, пришедших по вашей ссылке: {str(countReferal)}")

        await bot.send_message(chat_id=m.chat.id, text=msg, parse_mode='HTML')
        return

    if e.demojize(m.text) == "Помощь :heart_hands:":
        msg = e.emojize(f"Как мы можем вам помочь?")
        helpButtons = types.InlineKeyboardMarkup(row_width=1)
        helpButtons.add(
            types.InlineKeyboardButton(e.emojize("💫 Обновить информацию о подписке"),
                                       callback_data="Help:update"),
            types.InlineKeyboardButton(e.emojize(":woman_technologist: Чат с поддержкой"), url=SUPPORT_LINK),
            types.InlineKeyboardButton(e.emojize("❓ Часто задаваемые вопросы (FAQ)"),
                                       url="https://teletype.in/@vpnducks/faq"),
            types.InlineKeyboardButton(e.emojize("💳 Наши тарифы и стоимость"), callback_data="Help:PRICES"),
            types.InlineKeyboardButton(e.emojize(":video_camera: Не работает TikTok?"), callback_data="Help:TIKTOK"),
            types.InlineKeyboardButton(e.emojize(":wrapped_gift: Подарить подписку"), callback_data="Help:GIFT"),
        )
        if user_dat.type == 'amnezia':
            helpButtons.add(
                types.InlineKeyboardButton(e.emojize(":repeat_button: Сменить протокол"),
                                           callback_data="Help:change_type"),
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
            await bot.send_message(admin,
                                   f"Новое сообщение от @{m.from_user.username} ({m.from_user.id}): {e.emojize(m.text)}")
        await bot.send_message(m.from_user.id, f"Есть вопрос? Напишите нам {SUPPORT_USERNAME}",
                               reply_markup=await main_buttons(user_dat, True))

        return


@bot.callback_query_handler(func=lambda c: 'Init:' in c.data)
async def Init(call: types.CallbackQuery):
    user_dat = await User.GetInfo(call.from_user.id)
    device = str(call.data).split(":")[1]
    await sendConfigAndInstructions(user_dat.tgid, device, user_dat.type)
    await addUser(user_dat.tgid, user_dat.username)
    await addUserQueue(user_dat.tgid, user_dat.username)
    await bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: 'Help:' in c.data)
async def Init(call: types.CallbackQuery):
    user_dat = await User.GetInfo(call.from_user.id)
    command = str(call.data).split(":")[1]
    if command == 'update':
        await bot.send_message(user_dat.tgid, e.emojize('Информация о подписке обновлена'), parse_mode="HTML",
                               reply_markup=await main_buttons(user_dat, True))
    elif command == 'change_type':
        await bot.send_message(chat_id=user_dat.tgid, text=e.emojize(
            f"Запрос отправлен. Пожалуйста, дождитесь сообщения о смене протокола :winking_face:"), parse_mode="HTML")
        isTypeChanged = await user_dat.changeType()
        if isTypeChanged:
            userDatNew = await User.GetInfo(call.from_user.id)
            await addUser(userDatNew.tgid, userDatNew.username, userDatNew.type)
            await addUserQueue(userDatNew.tgid, userDatNew.username, userDatNew.type)
            await bot.send_message(userDatNew.tgid,
                                   e.emojize(
                                       'Протокол изменен.\nДля подключения нажмите на кнопку Как подключить :gear:'),
                                   parse_mode="HTML",
                                   reply_markup=await main_buttons(userDatNew, True))
    elif command == 'FAQ':
        await bot.send_message(chat_id=user_dat.tgid, text=e.emojize(
            texts_for_bot["faq"]
            + f"Если у вас остались вопросы, напишите в поддержку {SUPPORT_USERNAME}, мы всегда на связи и рады вам помочь 🙌🏻."),
                               parse_mode="HTML")
    elif command == 'PRICES':
        await bot.send_message(chat_id=user_dat.tgid, text=e.emojize(
            texts_for_bot["prices"]
            + f"Если у вас остались вопросы, напишите в поддержку {SUPPORT_USERNAME}, мы всегда на связи и рады вам помочь 🙌🏻."),
                               parse_mode="HTML")
    elif command == 'TIKTOK':
        await bot.send_message(chat_id=user_dat.tgid, text=e.emojize(
            f"Для корректной работы TikTok попробуйте, пожалуйста, переключиться на другие серверы."
            f"\n\rДля этого вам необходимо удалить ваш ключ из приложения и добавить новый, который мы вам отправим следующим сообщением ниже."
            f"\n\rЧто-то не получилось или этот способ не помог? Напишите {SUPPORT_USERNAME}, мы оперативно поможем 🙌🏻"),
                               parse_mode="HTML")

        await bot.send_message(chat_id=user_dat.tgid, text=e.emojize(
            f"Пожалуйста, подождите, ваш персональный ключ для TikTok генерируется :locked_with_key:"),
                               parse_mode="HTML")
        await sendConfigAndInstructions(user_dat.tgid, 'tiktok', 'xui')
    elif command == 'GIFT':
        await bot.send_message(chat_id=user_dat.tgid,
                               text=e.emojize(f"<b>Вы можете подарить подписку другому человеку</b>\r\n\r\n" \
                                              f"Для этого необходимо выбрать период подписки и произвести оплату\r\n" \
                                              f"После этого мы отправим вам ссылку и секретный код подарка, которые нужно будет передать получателю подарка\r\n\r\n" \
                                              f"После того, как получатель подарка перейдет по ссылке и введет секретный код, к его подписке добавится ваш подарок :wrapped_gift:"
                                              ),
                               parse_mode="HTML")
        await bot.send_message(chat_id=user_dat.tgid,
                               text=e.emojize(
                                   f"Выберите продолжительность подписки, которую хотите подарить :wrapped_gift:"),
                               parse_mode="HTML")
        await sendPayMessage(user_dat.tgid, 'gift')
    else:
        await bot.send_message(user_dat.tgid, e.emojize(f'Напишите нам {SUPPORT_USERNAME}'), parse_mode="HTML",
                               reply_markup=await main_buttons(user_dat, True))

    await bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: 'Referrer' in c.data)
async def Referrer(call: types.CallbackQuery):
    user_dat = await User.GetInfo(call.from_user.id)
    countReferal = await user_dat.countReferrerByUser()
    refLink = f"https://t.me/{CONFIG['bot_name']}?start=" + str(user_dat.tgid)

    msg = e.emojize(f"<b>Реферальная программа</b>\n\r\n\r" \
                    f":fire: Получите подписку, пригласив друзей по реферальной ссылке. Они получат неделю VPN бесплатно, а если после этого оформят подписку, мы подарим вам за каждого по месяцу подписки на VPN Ducks!\n\r\n\r" \
                    f":money_bag: А если вы блогер или владелец крупного сообщества, присоединяйтесь к нашей партнерской программе и зарабатывайте, рассказывая о VPN Ducks! Напишите нам {SUPPORT_USERNAME}\n\r" \
                    f"\n\rВаша пригласительная ссылка (кликните по ней, чтобы скопировать): \n\r\n\r<b><code>{refLink}</code></b>"
                    f"\n\r\n\rПользователей, пришедших по вашей ссылке: {str(countReferal)}")

    await bot.send_message(chat_id=call.message.chat.id, text=msg, parse_mode='HTML')


@bot.callback_query_handler(func=lambda c: 'toActivatePromo:' in c.data)
async def toActivatePromo(call: types.CallbackQuery):
    userDat = await User.GetInfo(call.from_user.id)

    await bot.send_message(chat_id=userDat.tgid, text="Подождите... Подписка активируется...",
                           reply_markup=await main_buttons(userDat))

    promo = str(call.data).split(":")[1]
    print(promo)

    conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
    dbCur = conn.cursor(pymysql.cursors.DictCursor)
    dbCur.execute(f"select * from promo where code = %s order by id desc limit 1",
                  (promo))
    promoLog = dbCur.fetchone()
    dbCur.close()
    conn.close()

    if promoLog is None:
        await bot.send_message(chat_id=userDat.tgid, text="Такой акции уже нет :)",
                               reply_markup=await main_buttons(userDat))
        await bot.delete_state(userDat.tgid)
        return

    daysToAdd = promoLog['days_to_add']

    conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
    dbCur = conn.cursor(pymysql.cursors.DictCursor)
    dbCur.execute(f"select * from promo_activations where code = %s and tgid = %s order by id desc limit 1",
                  (promo, userDat.tgid))
    promoActivationLog = dbCur.fetchone()
    dbCur.close()
    conn.close()

    if promoActivationLog is not None:
        await bot.send_message(chat_id=userDat.tgid, text="Вы уже участвовали в этой акции :)",
                               reply_markup=await main_buttons(userDat))
        await bot.delete_state(userDat.tgid)
        return

    await AddTimeToUserAsync(userDat.tgid, int(daysToAdd) * 24 * 60 * 60)

    conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
    dbCur = conn.cursor(pymysql.cursors.DictCursor)
    dbCur.execute(
        f"insert into promo_activations (tgid,code) values (%s,%s)",
        (userDat.tgid, promo))
    conn.commit()
    dbCur.close()
    conn.close()

    promoText = e.emojize(f"🎁 <b>Дарим вам {daysToAdd} дня бесплатного доступа!</b>\n\r\n\r" \
                          f"Пожалуйста, выберите тип телефона или планшета, для которого нужна инструкция для подключения:\n\r")
    trialButtons = await getTrialButtons()
    await bot.send_message(userDat.tgid, promoText, parse_mode="HTML", reply_markup=trialButtons)

    for admin in CONFIG["admin_tg_id"]:
        BotCheck.send_message(admin,
                              f"Пользователь {userDat.username} ({userDat.tgid}) активировал промо-акцию {promo}",
                              parse_mode="HTML")


@bot.callback_query_handler(func=lambda c: 'PayBlock' in c.data)
async def PayBlock(call: types.CallbackQuery):
    await sendPayMessage(call.message.chat.id)


@bot.callback_query_handler(func=lambda c: 'BuyMonth:' in c.data)
async def Buy_month(call: types.CallbackQuery):
    print('Buy_month start')
    user_dat = await User.GetInfo(call.from_user.id)
    payment_info = await user_dat.PaymentInfo()

    split = str(call.data).split(":")
    monthСount = int(split[1])

    additional = ''
    if len(split) > 2:
        additional = str(call.data).split(":")[2]

    print('additional ' + str(additional))
    try:
        await bot.delete_message(call.message.chat.id, call.message.id)
    except:
        pass

    # if call.message.chat.id in CONFIG["admin_tg_id"]:
    try:
        label = f"VPN на {str(monthСount)} мес. ({call.message.chat.id})"
        if additional == 'gift':
            label = f"VPN в подарок на {str(monthСount)} мес. ({call.message.chat.id})"

        price = getCostBySale(monthСount)
        pay = await Pay(PAYMENT_SYSTEM_CODE).createPay(
            tgid=call.message.chat.id,
            currency="RUB",
            label=label,
            price=price
        )
        payLink = pay['link']
        payId = pay['id']

        addTimeSubscribe = monthСount * 30 * 24 * 60 * 60

        payLinkButton = types.InlineKeyboardMarkup(row_width=1)
        payLinkButton.add(
            types.InlineKeyboardButton(emoji.emojize(":credit_card: Оплатить"), url=payLink)
        )

        if monthСount == 1:
            monthText = 'месяц'
        elif monthСount == 12:
            monthСount = 1
            monthText = 'год'
        else:
            monthText = 'месяцев'

        text = f"<b>Оплата подписки на {monthСount} {monthText}</b>\n\r\n\rДля оплаты откроется браузер.\n\rВы сможете оплатить подписку с помощью банковских карт, СБП и SberPay"
        if additional == 'gift':
            text = f"<b>Оплата подписки в подарок :wrapped_gift: на {monthСount} {monthText}</b>\n\r\n\rДля оплаты откроется браузер.\n\rВы сможете оплатить подарок с помощью банковских карт, СБП и SberPay"

        messageSend = await bot.send_message(chat_id=call.message.chat.id,
                                             text=emoji.emojize(text),
                                             parse_mode="HTML", reply_markup=payLinkButton)

        messageId = messageSend.message_id

        await user_dat.NewPay(
            payId,
            price,
            addTimeSubscribe,
            call.message.chat.id,
            Pay.STATUS_CREATED,
            messageId,
            additional
        )
    except Exception as e:
        print('payment error')
        print(e)
    # else:
    # price = getCostBySale(monthСount) * 100
    #
    # bill = await bot.send_invoice(call.message.chat.id, f"Оплата VPN", f"VPN на {str(monthСount)} мес.", call.data,
    #                               currency="RUB", prices=[
    #         types.LabeledPrice(f"VPN на {str(monthСount)} мес.", getCostBySale(monthСount) * 100)],
    #                               provider_token=CONFIG["tg_shop_token"])

    await bot.answer_callback_query(call.id)


@bot.pre_checkout_query_handler(func=lambda query: True)
async def checkout(pre_checkout_query):
    # (pre_checkout_query)
    month = int(str(pre_checkout_query.invoice_payload).split(":")[1])

    if getCostBySale(month) * 100 != pre_checkout_query.total_amount:
        await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=False,
                                            error_message="Нельзя купить по старой цене!")
        await bot.send_message(pre_checkout_query.from_user.id,
                               "<b>Цена изменилась! Нельзя приобрести по старой цене!</b>", parse_mode="HTML")
    else:
        await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True,
                                            error_message="Оплата не прошла, попробуйте еще раз!")


@bot.message_handler(content_types=['successful_payment'])
async def got_payment(m):
    payment: types.SuccessfulPayment = m.successful_payment
    month = int(str(payment.invoice_payload).split(":")[1])
    paymentsCount = 0

    try:
        # находим прошлые оплаты
        conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
        dbCur = conn.cursor(pymysql.cursors.DictCursor)
        dbCur.execute(f"select COUNT(*) as count from payments where tgid=%s", (m.from_user.id,))
        paymentsConn = dbCur.fetchone()
        paymentsCount = paymentsConn['count']
        dbCur.close()
        conn.close()
    except Exception as err:
        print('***--- FOUND PAYMENTS ERROR ---***')
        print(err)
        print(traceback.format_exc())
        pass

    addTimeSubscribe = month * 30 * 24 * 60 * 60

    try:
        await AddTimeToUser(m.from_user.id, addTimeSubscribe)
    except Exception as err:
        print('***--- ADD TIME ERROR ---***')
        print(err)
        print(traceback.format_exc())
        pass

    user_dat = await User.GetInfo(m.from_user.id)
    try:
        dateto = datetime.utcfromtimestamp(
            int(user_dat.subscription) + int(addTimeSubscribe) + CONFIG["UTC_time"] * 3600).strftime(
            '%d.%m.%Y %H:%M')
        await bot.send_message(m.from_user.id,
                               e.emojize(texts_for_bot["success_pay_message"]),
                               reply_markup=await buttons.main_buttons(user_dat, True), parse_mode="HTML")
    except Exception as err:
        print('***--- PAY MESSAGE 1 ERROR ---***')
        print(err)
        print(traceback.format_exc())
        pass

    try:
        Butt_reffer = types.InlineKeyboardMarkup()
        Butt_reffer.add(
            types.InlineKeyboardButton(
                e.emojize(f"Пригласить друга :wrapped_gift:"),
                callback_data="Referrer"))
        await bot.send_message(m.from_user.id, e.emojize(texts_for_bot["success_pay_message_2"]),
                               reply_markup=Butt_reffer, parse_mode="HTML")
    except Exception as err:
        print('***--- PAY MESSAGE 2 ERROR ---***')
        print(err)
        print(traceback.format_exc())
        pass

    try:
        payment_id = str(payment.provider_payment_charge_id)
        # save info about user
        await user_dat.NewPay(
            payment_id,
            getCostBySale(month),
            addTimeSubscribe,
            m.from_user.id)
    except Exception as err:
        print('***--- PAYMENT INFO DB ERROR ---***')
        print(err)
        print(traceback.format_exc())
        pass

    for admin in CONFIG["admin_tg_id"]:
        await bot.send_message(admin,
                               f"Новая оплата подписки от @{m.from_user.username} ( {m.from_user.id} ) на <b>{month}</b> мес. : {getCostBySale(month)} руб.",
                               parse_mode="HTML")

    try:
        print(paymentsCount)
        if paymentsCount <= 1:
            await addTrialForReferrerByUserId(m.from_user.id)
    except Exception as err:
        print('***--- ADD TRIAL TO REFERRER AFTER PAY ERROR ---***')
        print(err)
        print(traceback.format_exc())
        pass


bot.add_custom_filter(asyncio_filters.StateFilter(bot))


def checkTime():
    global e
    while True:
        try:
            time.sleep(20)

            conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
            dbCur = conn.cursor(pymysql.cursors.DictCursor)
            dbCur.execute(f"SELECT * FROM userss")
            log = dbCur.fetchall()
            dbCur.close()
            conn.close()

            for i in log:
                try:
                    time_now = int(time.time())
                    remained_time = int(i['subscription']) - time_now
                    if remained_time <= 0 and i['banned'] == False:
                        conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
                        dbCur = conn.cursor(pymysql.cursors.DictCursor)
                        dbCur.execute(f"UPDATE userss SET banned=true where tgid=%s", (i['tgid'],))
                        conn.commit()
                        dbCur.close()
                        conn.close()

                        asyncio.run(switchUserActivity(str(i['tgid']), False))
                        asyncio.run(switchUserActivityQueue(str(i['tgid']), False))

                        dateto = datetime.utcfromtimestamp(int(i['subscription']) + CONFIG['UTC_time'] * 3600).strftime(
                            '%d.%m.%Y %H:%M')
                        Butt_main = types.ReplyKeyboardMarkup(resize_keyboard=True)
                        Butt_main.add(
                            types.KeyboardButton(e.emojize(f":red_circle: Подписка закончилась: {dateto} МСК")))
                        Butt_main.add(types.KeyboardButton(e.emojize(f"Продлить подписку :money_bag:")),
                                      types.KeyboardButton(e.emojize(f"Как подключить :gear:")))
                        Butt_main.add(
                            types.KeyboardButton(
                                e.emojize(f"Наши преимущества :gem_stone:")),
                            types.KeyboardButton(e.emojize(f"Пригласить :wrapped_gift:")),
                            types.KeyboardButton(e.emojize(f"Помощь :heart_hands:")))
                        if i['tgid'] in CONFIG["admin_tg_id"]:
                            Butt_main.add(
                                types.KeyboardButton(e.emojize(f"Админ-панель :smiling_face_with_sunglasses:")))

                        BotCheck.send_message(i['tgid'],
                                              texts_for_bot["ended_sub_message"],
                                              reply_markup=Butt_main, parse_mode="HTML")

                        Butt_reffer = types.InlineKeyboardMarkup()
                        Butt_reffer.add(
                            types.InlineKeyboardButton(
                                e.emojize(f"Продлить подписку :money_bag:"),
                                callback_data="PayBlock"))
                        Butt_reffer.add(
                            types.InlineKeyboardButton(
                                e.emojize(f"Пригласить друга :wrapped_gift:"),
                                callback_data="Referrer"))
                        BotCheck.send_message(i['tgid'],
                                              texts_for_bot[
                                                  "ended_sub_message_2"] + f"По всем вопросам пишите {SUPPORT_USERNAME}",
                                              reply_markup=Butt_reffer, parse_mode="HTML")

                    elif remained_time > 0 and remained_time <= 7200:
                        conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
                        dbCur = conn.cursor(pymysql.cursors.DictCursor)
                        dbCur.execute(
                            f"SELECT * FROM notions where tgid=%s and notion_type='type_2hours'",
                            (i['tgid'],))
                        log = dbCur.fetchone()
                        dbCur.close()
                        conn.close()

                        if log is None:
                            Butt_reffer = types.InlineKeyboardMarkup()
                            Butt_reffer.add(
                                types.InlineKeyboardButton(
                                    e.emojize(f"Продлить подписку :money_bag:"),
                                    callback_data="PayBlock"))
                            Butt_reffer.add(
                                types.InlineKeyboardButton(
                                    e.emojize(f"Пригласить друга :wrapped_gift:"),
                                    callback_data="Referrer"))
                            BotCheck.send_message(i['tgid'], texts_for_bot[
                                "alert_to_renew_sub_2hours"] + f"Пишите {SUPPORT_USERNAME}",
                                                  reply_markup=Butt_reffer,
                                                  parse_mode="HTML")

                            conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
                            dbCur = conn.cursor(pymysql.cursors.DictCursor)
                            dbCur.execute(f"INSERT INTO notions (tgid,notion_type) values (%s,%s)",
                                          (i['tgid'], 'type_2hours',))
                            conn.commit()
                            dbCur.close()
                            conn.close()

                    elif remained_time > 7200 and remained_time <= 86400:
                        conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
                        dbCur = conn.cursor(pymysql.cursors.DictCursor)
                        dbCur.execute(
                            f"SELECT * FROM notions where tgid=%s and notion_type='type_24hours'",
                            (i['tgid'],))
                        log = dbCur.fetchone()
                        dbCur.close()
                        conn.close()

                        if log is None:
                            Butt_reffer = types.InlineKeyboardMarkup()
                            Butt_reffer.add(
                                types.InlineKeyboardButton(e.emojize(f"Продлить подписку :money_bag:"),
                                                           callback_data="PayBlock"))
                            BotCheck.send_message(i['tgid'], texts_for_bot["alert_to_renew_sub_24hours"],
                                                  reply_markup=Butt_reffer, parse_mode="HTML")

                            conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
                            dbCur = conn.cursor(pymysql.cursors.DictCursor)
                            dbCur.execute(f"INSERT INTO notions (tgid,notion_type) values (%s,%s)",
                                          (i['tgid'], 'type_24hours',))
                            conn.commit()
                            dbCur.close()
                            conn.close()

                except ApiTelegramException as exception:
                    if (exception.description == 'Forbidden: bot was blocked by the user'):
                        conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
                        dbCur = conn.cursor(pymysql.cursors.DictCursor)
                        dbCur.execute(f"Update userss set blocked=true where tgid=%s", (i['tgid']))
                        conn.commit()
                        dbCur.close()
                        conn.close()
                    pass

            # payments
            conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
            dbCur = conn.cursor(pymysql.cursors.DictCursor)
            dbCur.execute(f"SELECT * FROM payments WHERE status <> 'success' and time < NOW() - INTERVAL 55 MINUTE")
            log = dbCur.fetchall()
            dbCur.close()
            conn.close()
            for i in log:
                tgId = i['tgid']
                messageId = i['message_id']
                if messageId:
                    try:
                        BotCheck.delete_message(tgId, messageId)
                    except:
                        pass

            conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
            dbCur = conn.cursor(pymysql.cursors.DictCursor)
            dbCur.execute(f"DELETE FROM payments WHERE status <> 'success' and time < NOW() - INTERVAL 61 MINUTE")
            conn.commit()
            dbCur.execute(f"SELECT * FROM payments WHERE status <> 'success'")
            log = dbCur.fetchall()
            dbCur.close()
            conn.close()

            testTimeSubscribe = 100 * 30 * 24 * 60 * 60

            for i in log:
                try:
                    paymentId = i['bill_id']

                    if i['time_to_add'] == testTimeSubscribe:
                        paymentSuccess(paymentId)

                    paymentData = Pay(PAYMENT_SYSTEM_CODE).findPay(paymentId)
                    if paymentData and paymentData['success']:
                        if paymentData['payment'].status == 'succeeded':
                            paymentSuccess(paymentId)

                except ApiTelegramException as exception:
                    if (exception.description == 'Forbidden: bot was blocked by the user'):
                        conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
                        dbCur = conn.cursor(pymysql.cursors.DictCursor)
                        dbCur.execute(f"Update userss set blocked=true where tgid=%s", (i['tgid']))
                        conn.commit()
                        dbCur.close()
                        conn.close()
                    pass

        except ApiTelegramException as exception:
            print("ApiTelegramException")
            print(exception.description)
            print(traceback.format_exc())
            pass
        except Exception as err:
            print('NOT AWAIT ERROR')
            print(err)
            print(traceback.format_exc())
            pass


def checkQueue():
    while True:
        try:
            conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
            dbCur = conn.cursor(pymysql.cursors.DictCursor)
            dbCur.execute(f"SELECT * FROM queue WHERE status <> 'success'")
            log = dbCur.fetchall()
            dbCur.close()
            conn.close()

            for i in log:
                result = False

                if i['type'] == 'add_user':
                    dataJson = i['data']
                    data = json.loads(dataJson)
                    tgId = data['user_id']
                    userName = data['user_name']
                    result = asyncio.run(addUser(str(tgId), str(userName)))
                if i['type'] == 'switch_user':
                    dataJson = i['data']
                    data = json.loads(dataJson)
                    tgId = data['tgid']
                    val = data['val']
                    result = asyncio.run(switchUserActivity(str(tgId), val))

                if result:
                    conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
                    dbCur = conn.cursor(pymysql.cursors.DictCursor)
                    dbCur.execute(f"delete from queue where id=%s",
                                  (i['id']))
                    conn.commit()
                    dbCur.close()
                    conn.close()

        except Exception as err:
            print('CHECK QUEUE ERROR')
            print(err)
            print(traceback.format_exc())
            pass

        time.sleep(10)


def checkUsers():
    while True:
        try:
            conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
            dbCur = conn.cursor(pymysql.cursors.DictCursor)
            dbCur.execute(
                f"SELECT * FROM userss WHERE TIME(date_create) > TIME(CURRENT_TIME() - INTERVAL 60 MINUTE) ORDER BY id DESC LIMIT 100;")
            log = dbCur.fetchall()
            dbCur.close()
            conn.close()

            for i in log:
                asyncio.run(addUserQueue(i['tgid'], i['username']))

            conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
            dbCur = conn.cursor(pymysql.cursors.DictCursor)
            dbCur.execute(
                f"SELECT * FROM payments WHERE TIME(time) > TIME(CURRENT_TIME() - INTERVAL 60 MINUTE) ORDER BY id DESC LIMIT 100")
            log = dbCur.fetchall()
            dbCur.close()
            conn.close()

            for i in log:
                asyncio.run(switchUserActivityQueue(str(i['tgid']), True))

        except Exception as err:
            print('CHECK USERS ERROR')
            print(err)
            print(traceback.format_exc())
            pass

        time.sleep(120)

def checkBackup():
    while True:
        try:
            backupDir = CONFIG["backup_dir"]
            dateString = f'{datetime.now():%Y_%m_%d_%H_%M_%S%z}'
            subprocess.call(
                'find ' + backupDir + '* -mtime +5 -exec rm {} \;\n',
                shell=True)
            subprocess.call(
                'mysqldump -v -h localhost -u ' + DBUSER + ' -p' + DBPASSWORD + ' --skip-comments ducksvpn > ' + backupDir + '/dump_' + dateString + '.sql\n',
                shell=True)
            time.sleep(43200)
        except Exception as err:
            print('BACKUP ERROR')
            print(err)
            print(traceback.format_exc())
            pass


if __name__ == '__main__':
    threadcheckTime = threading.Thread(target=checkTime, name="checkTime1")
    threadcheckTime.start()
    threadcheckBackup = threading.Thread(target=checkBackup, name="checkBackup1")
    threadcheckBackup.start()
    threadcheckQueue = threading.Thread(target=checkQueue(), name="checkUsers1")
    threadcheckQueue.start()
    threadcheckUsers = threading.Thread(target=checkUsers(), name="checkUsers1")
    threadcheckUsers.start()

    try:
        asyncio.run(bot.infinity_polling(request_timeout=300, timeout=123, skip_pending=True))
    except Exception as err:
        print('asyncio error')
        print(err)
        print(traceback.format_exc())
        pass
