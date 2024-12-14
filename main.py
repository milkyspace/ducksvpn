import json
import time
import emoji
import emoji as e
import threading
import traceback
import asyncio
import subprocess
from datetime import datetime
from telebot import TeleBot
from telebot import asyncio_filters
from telebot import types
from telebot.apihelper import ApiTelegramException
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage
from telebot.asyncio_handler_backends import State, StatesGroup

import backprocesses
from modules.db.db import Db
from modules.bot.config import Config
from modules.bot.buttons import main_buttons, admin_buttons, admin_buttons_back, \
    admin_buttons_output_users
from modules.requests.smrequests import getConnectionLinks, getAmneziaConnectionFile, switchUserActivity, addUser
from modules.users.dbworker import User
from modules.pay.pay import Pay
from modules.bot.admin import adminfunc
from modules.utils import utils

CONFIG = Config.getConfig()
with open("modules/bot/texts.json", encoding="utf-8") as file_handler:
    text_mess = json.load(file_handler)
    texts_for_bot = text_mess

BOTAPIKEY = CONFIG["tg_token"]
BotCheck = TeleBot(BOTAPIKEY)
bot = AsyncTeleBot(CONFIG["tg_token"], state_storage=StateMemoryStorage())

PAYMENT_SYSTEM_CODE = CONFIG["payment_system_code"]
SUPPORT_LINK = CONFIG["support_link"]
SUPPORT_USERNAME = CONFIG["support_username"]


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
    update50Users = State()
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
        db = Db()
        cursor = db.getCursor()
        cursor.execute(f"select * from users_keys where tgid = %s and type = %s order by id desc limit 1",
                       (tgId, device))
        userKeyLog = cursor.fetchone()
        del db

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
                db = Db()
                cursor = db.getCursor()
                cursor.execute(f"insert into users_keys (tgid,type,user_key) values (%s,%s,%s)",
                               (tgId, device, link))
                db.commit()
                del db

            additionalText = ("\r\n\r\n<b>ВАЖНО!</b>"
                              "\r\n<b>При первом подключении</b> ваш ключ может дойти на все серверы с задержкой." \
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
            instructionWindows = f"<b>Подключение VPN DUCKS на Windows</b>\n\r\n\r1. Установите приложение Amnezia VPN <a href='https://github.com/amnezia-vpn/amnezia-client/releases/download/4.8.2.3/AmneziaVPN_4.8.2.3_x64.exe'>по этой ссылке</a>\r\n2. Скопируйте ссылку, прикрепленную ниже, перейдите в приложение Amnezia VPN, внутри приложения перейди во вкладку «Соединение» (нажав на +), далее нажмите на кнопку \"Вставить\" (или \"Insert\")\n\r3. Приложение попросит разрешения на вставку, дайте разрешения нажмите \"Продолжить\"\n\r4. Нажмите на кнопку \"Подключиться\" и включите VPN большой круглой кнопкой.\n\r\n\rГотово! 🎉\r\n\r\nЧто-то не получилось или vpn работает не стабильно? Напишите {SUPPORT_USERNAME}, мы оперативно поможем 🙌🏻"
            instructionMacOS = f"<b>Подключение VPN DUCKS на MacOS</b>\n\r\n\r1. Установите приложение <a href='https://apps.apple.com/ru/app/foxray/id6448898396'>FoXray из AppStore</a>\n\r2. Скопируйте ссылку (начинающуюся с vless://), прикрепленную ниже, и вставьте в приложение FoXray, нажав на кнопку, обведенную на скриншоте ниже. (кнопка крайняя справа)\n\r3. Нажмите на кнопку ▶️ для запуска VPN.\n\r\n\rГотово! 🎉\n\r\n\rЧто-то не получилось или vpn работает не стабильно? Напишите {SUPPORT_USERNAME}, мы оперативно поможем 🙌🏻"
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

            if (device == "MacOS"):
                await bot.send_photo(user_dat.tgid,
                                     "https://img1.teletype.in/files/c7/94/c79495ad-e4fd-49d0-8121-0ead1a0e6f08.webp")

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
                                   reply_markup=await admin_buttons())


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

        db = Db()
        cursor = db.getCursor()
        cursor.execute(
            f"Update userss set subscription=subscription+{addTrialTime}, banned=false where tgid={referrer_id}")
        db.commit()
        del db

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
        db = Db()
        cursor = db.getCursor()
        cursor.execute(f"Update userss set subscription = %s, banned=false where tgid=%s",
                       (str(int(time.time()) + timetoadd), userdat.tgid))
        cursor.execute(f"DELETE FROM notions where tgid=%s", (userdat.tgid))
        db.commit()
        del db

        await switchUserActivity(str(userdat.tgid), True)

        await bot.send_message(userdat.tgid, e.emojize(
            f'<b>Информация о подписке обновлена</b>\n\nНеобходимо отключить и заново включить соединение с vpn в приложении.\n\r\n\rЧто-то не получилось? Напишите нам {SUPPORT_USERNAME}'),
                               parse_mode="HTML", reply_markup=await main_buttons(userdat, True))
    else:
        db = Db()
        cursor = db.getCursor()
        cursor.execute(f"Update userss set subscription = %s where tgid=%s",
                       (str(int(userdat.subscription) + timetoadd), userdat.tgid))
        db.commit()
        del db

        await switchUserActivity(str(userdat.tgid), True)
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
        db = Db()
        cursor = db.getCursor()
        cursor.execute(f"Update userss set subscription = %s, banned=false where tgid=%s",
                       (str(int(time.time()) + timetoadd), userdat.tgid))
        cursor.execute(f"DELETE FROM notions where tgid=%s", (userdat.tgid))
        db.commit()
        del db

        asyncio.run(switchUserActivity(str(userdat.tgid), True))

        BotCheck.send_message(userdat.tgid, e.emojize(
            f'<b>Информация о подписке обновлена</b>\n\nНеобходимо отключить и заново включить соединение с vpn в приложении.\n\r\n\rЧто-то не получилось? Напишите нам {SUPPORT_USERNAME}'),
                              parse_mode="HTML", reply_markup=asyncio.run(main_buttons(userdat, True)))
    else:
        db = Db()
        cursor = db.getCursor()
        cursor.execute(f"Update userss set subscription = %s where tgid=%s",
                       (str(int(userdat.subscription) + timetoadd), userdat.tgid))
        db.commit()
        del db

        asyncio.run(switchUserActivity(str(userdat.tgid), True))
        BotCheck.send_message(userdat.tgid, e.emojize(
            'Информация о подписке обновлена'), parse_mode="HTML",
                              reply_markup=asyncio.run(main_buttons(userdat, True)))


async def AddTimeToUserAsync(tgid, timetoadd):
    userdat = await User.GetInfo(tgid)
    if userdat.subscription == None:
        return
    if int(userdat.subscription) < int(time.time()):
        db = Db()
        cursor = db.getCursor()
        cursor.execute(f"Update userss set subscription = %s, banned=false where tgid=%s",
                       (str(int(time.time()) + timetoadd), userdat.tgid))
        cursor.execute(f"DELETE FROM notions where tgid=%s", (userdat.tgid))
        db.commit()
        del db

        await switchUserActivity(str(userdat.tgid), True)

        await bot.send_message(userdat.tgid, e.emojize(
            f'<b>Информация о подписке обновлена</b>\n\nНеобходимо отключить и заново включить соединение с vpn в приложении.\n\r\n\rЧто-то не получилось? Напишите нам {SUPPORT_USERNAME}'),
                               parse_mode="HTML", reply_markup=await main_buttons(userdat, True))
    else:
        db = Db()
        cursor = db.getCursor()
        cursor.execute(f"Update userss set subscription = %s where tgid=%s",
                       (str(int(userdat.subscription) + timetoadd), userdat.tgid))
        db.commit()
        del db

        await switchUserActivity(str(userdat.tgid), True)
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


def paymentSuccess(paymentId):
    db = Db()
    cursor = db.getCursor()
    cursor.execute(f"UPDATE payments SET status='success' WHERE bill_id = %s", (paymentId,))
    db.commit()
    del db

    db = Db()
    cursor = db.getCursor()
    cursor.execute(f"SELECT * FROM payments where bill_id=%s", (paymentId,))
    log = cursor.fetchone()
    del db

    tgid = log['tgid']
    amount = log['amount']
    addTimeSubscribe = log['time_to_add']
    additional = log['additional']
    paymentsCount = 0

    try:
        # находим прошлые оплаты
        db = Db()
        cursor = db.getCursor()
        cursor.execute(f"select COUNT(*) as count from payments where tgid=%s and status='success'", (tgid,))
        paymentsConn = cursor.fetchone()
        paymentsCount = paymentsConn['count']
        del db
    except Exception as err:
        print('***--- FOUND PAYMENTS ERROR ---***')
        print(err)
        print(traceback.format_exc())
        pass

    user_dat = asyncio.run(User.GetInfo(tgid))

    if additional == 'gift':
        secret = utils.randomword(10)
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
        BotCheck.send_message(tgid, msg, reply_markup=asyncio.run(main_buttons(user_dat, True)),
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
                              reply_markup=asyncio.run(main_buttons(user_dat, True)), parse_mode="HTML")
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

    # Приветствуем нового пользователя (реферала)
    user_dat = await User.GetInfo(tgId)
    trialText = e.emojize(f"Привет, {user_dat.fullname}!\n\r\n\r" \
                          f"🎁 <b>Дарим вам 7 дней бесплатного доступа!</b>\n\r\n\r" \
                          f"Пожалуйста, выберите тип телефона или планшета, для которого нужна инструкция для подключения:\n\r")

    trialButtons = await getTrialButtons()
    await bot.send_message(tgId, trialText, parse_mode="HTML", reply_markup=trialButtons)

    await addUser(tgId, username)


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
async def enterGiftSecret(m: types.Message):
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

    db = Db()
    cursor = db.getCursor()
    cursor.execute(f"select * from gifts where id = %s and secret = %s and status='new' order by id desc limit 1",
                   (giftId, secretCode))
    giftLog = cursor.fetchone()
    del db

    if giftLog is not None:
        db = Db()
        cursor = db.getCursor()
        cursor.execute(f"select * from payments where bill_id = %s and additional='gift' order by id desc limit 1",
                       (giftLog['payment_id']))
        paymentLog = cursor.fetchone()
        del db

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

            db = Db()
            cursor = db.getCursor()
            cursor.execute(f"update gifts set status='success', recipient_tgid=%s where id = %s",
                           (m.chat.id, giftId))
            db.commit()
            del db

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
async def editUser(m: types.Message):
    await adminfunc.editUser(m, bot, MyStates)


@bot.message_handler(state=MyStates.editUserResetTime, content_types=["text"])
async def editUserResetTime(m: types.Message):
    await adminfunc.editUserResetTime(m, bot, MyStates)


@bot.message_handler(state=MyStates.UserAddTimeDays, content_types=["text"])
async def UserAddTimeDays(m: types.Message):
    await adminfunc.UserAddTimeDays(m, bot, MyStates)


@bot.message_handler(state=MyStates.UserAddTimeHours, content_types=["text"])
async def UserAddTimeHours(m: types.Message):
    await adminfunc.UserAddTimeHours(m, bot, MyStates)


@bot.message_handler(state=MyStates.UserAddTimeMinutes, content_types=["text"])
async def UserAddTimeMinutes(m: types.Message):
    await adminfunc.UserAddTimeMinutes(m, bot, MyStates)


@bot.message_handler(state=MyStates.UserAddTimeApprove, content_types=["text"])
async def UserAddTimeApprove(m: types.Message):
    await adminfunc.UserAddTimeApprove(m, bot, MyStates)


@bot.message_handler(state=MyStates.findUserViaId, content_types=["text"])
async def findUserViaId(m: types.Message):
    await adminfunc.UserAddTimeApprove(m, bot, MyStates)


@bot.message_handler(state=MyStates.prepareUserForSendMessage, content_types=["text"])
async def prepareUserForSendMessage(m: types.Message):
    await adminfunc.prepareUserForSendMessage(m, bot, MyStates)


@bot.message_handler(state=MyStates.sendMessageToUser, content_types=["text"])
async def sendMessageToUser(m: types.Message):
    await adminfunc.sendMessageToUser(m, bot, MyStates)


@bot.message_handler(state=MyStates.sendMessageToAllUser, content_types=["text"])
async def sendMessageToAllUser(m: types.Message):
    await adminfunc.sendMessageToAllUser(m, bot, MyStates)


@bot.message_handler(state=MyStates.sendMessageToAmneziaUser, content_types=["text"])
async def sendMessageToAmneziaUser(m: types.Message):
    await adminfunc.sendMessageToAmneziaUser(m, bot, MyStates)


@bot.message_handler(state=MyStates.sendMessageToAllInactiveUser, content_types=["text"])
async def sendMessageToAllInactiveUser(m: types.Message):
    await adminfunc.sendMessageToAllInactiveUser(m, bot, MyStates)


@bot.message_handler(state=MyStates.sendMessageToLast50User, content_types=["text"])
async def sendMessageToLast50User(m: types.Message):
    await adminfunc.sendMessageToLast50User(m, bot, MyStates)


@bot.message_handler(state=MyStates.findUsersByName, content_types=["text"])
async def findUsersByName(m: types.Message):
    await adminfunc.findUsersByName(m, bot, MyStates)


@bot.message_handler(state=MyStates.switchActiveUserManual, content_types=["text"])
async def switchActiveUserManual(m: types.Message):
    await adminfunc.switchActiveUserManual(m, bot, MyStates)


@bot.message_handler(state=MyStates.updateAllUsers, content_types=["text"])
async def updateAllUsers(m: types.Message):
    await adminfunc.updateAllUsers(m, bot, MyStates)


@bot.message_handler(state=MyStates.update50Users, content_types=["text"])
async def update50Users(m: types.Message):
    await adminfunc.update50Users(m, bot, MyStates)


@bot.callback_query_handler(func=lambda c: 'Init:' in c.data)
async def Init(call: types.CallbackQuery):
    user_dat = await User.GetInfo(call.from_user.id)
    device = str(call.data).split(":")[1]
    await sendConfigAndInstructions(user_dat.tgid, device, user_dat.type)
    await addUser(user_dat.tgid, user_dat.username)
    await bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: 'Help:' in c.data)
async def Help(call: types.CallbackQuery):
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


@bot.callback_query_handler(func=lambda c: 'toActivatePromo:' in c.data)
async def toActivatePromo(call: types.CallbackQuery):
    userDat = await User.GetInfo(call.from_user.id)

    await bot.send_message(chat_id=userDat.tgid, text="Подождите... Подписка активируется...",
                           reply_markup=await main_buttons(userDat))

    promo = str(call.data).split(":")[1]
    print(promo)

    db = Db()
    cursor = db.getCursor()
    cursor.execute(f"select * from promo where code = %s order by id desc limit 1",
                   (promo))
    promoLog = cursor.fetchone()
    del db

    if promoLog is None:
        await bot.send_message(chat_id=userDat.tgid, text="Такой акции уже нет :)",
                               reply_markup=await main_buttons(userDat))
        await bot.delete_state(userDat.tgid)
        return

    daysToAdd = promoLog['days_to_add']

    db = Db()
    cursor = db.getCursor()
    cursor.execute(f"select * from promo_activations where code = %s and tgid = %s order by id desc limit 1",
                   (promo, userDat.tgid))
    promoActivationLog = cursor.fetchone()
    del db

    if promoActivationLog is not None:
        await bot.send_message(chat_id=userDat.tgid, text="Вы уже участвовали в этой акции :)",
                               reply_markup=await main_buttons(userDat))
        await bot.delete_state(userDat.tgid)
        return

    await AddTimeToUserAsync(userDat.tgid, int(daysToAdd) * 24 * 60 * 60)

    db = Db()
    cursor = db.getCursor()
    cursor.execute(f"insert into promo_activations (tgid,code) values (%s,%s)",
                   (userDat.tgid, promo))
    db.commit()
    del db

    promoText = e.emojize(f"🎁 <b>Дарим вам {daysToAdd} дня бесплатного доступа!</b>\n\r\n\r" \
                          f"Пожалуйста, выберите тип телефона или планшета, для которого нужна инструкция для подключения:\n\r")
    trialButtons = await getTrialButtons()
    await bot.send_message(userDat.tgid, promoText, parse_mode="HTML", reply_markup=trialButtons)

    for admin in CONFIG["admin_tg_id"]:
        BotCheck.send_message(admin,
                              f"Пользователь {userDat.username} ({userDat.tgid}) активировал промо-акцию {promo}",
                              parse_mode="HTML")


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
            await bot.send_message(m.from_user.id, "Админ панель", reply_markup=await admin_buttons())
            return
        if e.demojize(m.text) == "Главное меню :right_arrow_curving_left:":
            await bot.send_message(m.from_user.id, e.emojize("Админ-панель :smiling_face_with_sunglasses:"),
                                   reply_markup=await main_buttons(user_dat))
            return
        if e.demojize(m.text) == "Вывести пользователей :bust_in_silhouette:":
            await bot.send_message(m.from_user.id, e.emojize("Выберите каких пользователей хотите вывести."),
                                   reply_markup=await admin_buttons_output_users())
            return

        if e.demojize(m.text) == "Назад :right_arrow_curving_left:":
            await bot.send_message(m.from_user.id, "Админ панель", reply_markup=await admin_buttons())
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
                await bot.send_message(m.from_user.id, e.emojize(i), reply_markup=await admin_buttons())
            return

        if e.demojize(m.text) == "Пользователей с подпиской":
            allusers = await user_dat.GetAllUsersWithSub()
            readymass = []
            readymes = ""
            if len(allusers) == 0:
                await bot.send_message(m.from_user.id, e.emojize("Нет пользователей с подпиской!"),
                                       reply_markup=await admin_buttons(), parse_mode="HTML")
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
                                   reply_markup=await admin_buttons_back())
            return

        if e.demojize(m.text) == "Отправить сообщение всем пользователям Amnezia :pencil:":
            await bot.set_state(m.from_user.id, MyStates.sendMessageToAmneziaUser)
            await bot.send_message(m.from_user.id, "Введите сообщение:",
                                   reply_markup=await admin_buttons_back())
            return

        if e.demojize(m.text) == "Отправить сообщение всем неактивным пользователям :pencil:":
            await bot.set_state(m.from_user.id, MyStates.sendMessageToAllInactiveUser)
            await bot.send_message(m.from_user.id, "Введите сообщение:",
                                   reply_markup=await admin_buttons_back())
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
                        db = Db()
                        cursor = db.getCursor()
                        cursor.execute(f"Update userss set blocked=true where tgid=%s", (i['tgid']))
                        db.commit()
                        del db
                    pass
                except Exception as err:
                    print(err)
                    print(traceback.format_exc())
                    pass

            await bot.delete_state(m.from_user.id)
            await bot.send_message(m.from_user.id, "Сообщения отправлены", reply_markup=await admin_buttons())
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

            await bot.send_message(m.from_user.id, "Сообщения отправлены", reply_markup=await admin_buttons())
            await bot.send_message(m.from_user.id, f"{len(allusers)} пользователям",
                                   reply_markup=await admin_buttons())

            return

        if e.demojize(m.text) == "Отправить сообщение последним 50 пользователям :pencil:":
            await bot.set_state(m.from_user.id, MyStates.sendMessageToLast50User)
            await bot.send_message(m.from_user.id, "Введите сообщение:",
                                   reply_markup=await admin_buttons_back())
            return

        if e.demojize(m.text) == "Поиск пользователя по никнейму :magnifying_glass_tilted_left:":
            await bot.set_state(m.from_user.id, MyStates.findUsersByName)
            await bot.send_message(m.from_user.id, "Введите никнейм пользователя:",
                                   reply_markup=await admin_buttons_back())
            return

        if e.demojize(m.text) == "Перезагрузить базу :optical_disk:":
            subprocess.call('sudo systemctl restart mysql\n', shell=True)
            await bot.send_message(m.from_user.id, "База перезагружена",
                                   reply_markup=await admin_buttons_back())
            return

        if e.demojize(m.text) == "Активировать пользователя вручную :man:":
            await bot.set_state(m.from_user.id, MyStates.switchActiveUserManual)
            await bot.send_message(m.from_user.id, "Введите никнейм или id пользователя:",
                                   reply_markup=await admin_buttons_back())
            return

        if e.demojize(m.text) == "Обновить последних 50 пользователей :man:":
            await bot.set_state(m.from_user.id, MyStates.update50Users)
            await bot.send_message(m.from_user.id,
                                   "Вы уверены, что хотите обновить последних 50 пользователей? Введите `Да`",
                                   reply_markup=await admin_buttons_back())
            return

        if e.demojize(m.text) == "Обновить всех пользователей :man:":
            await bot.set_state(m.from_user.id, MyStates.updateAllUsers)
            await bot.send_message(m.from_user.id, "Вы уверены, что хотите обновить всех? Введите `Да`",
                                   reply_markup=await admin_buttons_back())
            return

        if e.demojize(m.text) == "Добавить пользователя :plus:":
            await bot.send_message(m.from_user.id,
                                   "Введите имя для нового пользователя!\nМожно использовать только латинские символы и арабские цифры.",
                                   reply_markup=await admin_buttons_back())
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


bot.add_custom_filter(asyncio_filters.StateFilter(bot))

if __name__ == '__main__':
    threadcheckTime = threading.Thread(target=backprocesses.checkTime, name="checkTime1")
    threadcheckTime.start()
    threadcheckBackup = threading.Thread(target=backprocesses.checkBackup, name="checkBackup1")
    threadcheckBackup.start()

    try:
        asyncio.run(bot.infinity_polling(request_timeout=300, timeout=123, skip_pending=True))
    except Exception as err:
        print('asyncio error')
        print(err)
        print(traceback.format_exc())
        pass
