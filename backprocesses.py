import json
import time
import traceback
import asyncio
import subprocess
from datetime import datetime
from telebot import TeleBot
from telebot import types
from telebot.apihelper import ApiTelegramException
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage

import main
from modules.db.db import Db
from modules.bot.config import Config
from modules.requests.smrequests import switchUserActivity
from modules.pay.pay import Pay

CONFIG = Config.getConfig()
with open("modules/bot/texts.json", encoding="utf-8") as file_handler:
    text_mess = json.load(file_handler)
    texts_for_bot = text_mess

BOTAPIKEY = CONFIG["tg_token"]
BotCheck = TeleBot(BOTAPIKEY)
bot = AsyncTeleBot(CONFIG["tg_token"], state_storage=StateMemoryStorage())

DBHOST = CONFIG["db_host"]
DBUSER = CONFIG["db_user"]
DBPASSWORD = CONFIG["db_password"]
DBNAME = CONFIG["db_name"]

PAYMENT_SYSTEM_CODE = CONFIG["payment_system_code"]
SUPPORT_LINK = CONFIG["support_link"]
SUPPORT_USERNAME = CONFIG["support_username"]

def checkTime():
    global e
    while True:
        try:
            time.sleep(20)

            db = Db()
            cursor = db.getCursor()
            cursor.execute(f"SELECT * FROM userss")
            log = cursor.fetchall()
            del db

            for i in log:
                try:
                    time_now = int(time.time())
                    remained_time = int(i['subscription']) - time_now
                    if remained_time <= 0 and i['banned'] == False:
                        db = Db()
                        cursor = db.getCursor()
                        cursor.execute(f"UPDATE userss SET banned=true where tgid=%s", (i['tgid'],))
                        db.commit()
                        del db

                        asyncio.run(switchUserActivity(str(i['tgid']), False))

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
                        db = Db()
                        cursor = db.getCursor()
                        cursor.execute(f"SELECT * FROM notions where tgid=%s and notion_type='type_2hours'",
                                       (i['tgid'],))
                        log = cursor.fetchone()
                        del db

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

                            db = Db()
                            cursor = db.getCursor()
                            cursor.execute(f"INSERT INTO notions (tgid,notion_type) values (%s,%s)",
                                           (i['tgid'], 'type_2hours',))
                            db.commit()
                            del db

                    elif remained_time > 7200 and remained_time <= 86400:
                        db = Db()
                        cursor = db.getCursor()
                        cursor.execute(f"SELECT * FROM notions where tgid=%s and notion_type='type_24hours'",
                                       (i['tgid'],))
                        log = cursor.fetchone()
                        del db

                        if log is None:
                            Butt_reffer = types.InlineKeyboardMarkup()
                            Butt_reffer.add(
                                types.InlineKeyboardButton(e.emojize(f"Продлить подписку :money_bag:"),
                                                           callback_data="PayBlock"))
                            BotCheck.send_message(i['tgid'], texts_for_bot["alert_to_renew_sub_24hours"],
                                                  reply_markup=Butt_reffer, parse_mode="HTML")

                            db = Db()
                            cursor = db.getCursor()
                            cursor.execute(f"INSERT INTO notions (tgid,notion_type) values (%s,%s)",
                                           (i['tgid'], 'type_24hours',))
                            db.commit()
                            del db

                except ApiTelegramException as exception:
                    if (exception.description == 'Forbidden: bot was blocked by the user'):
                        db = Db()
                        cursor = db.getCursor()
                        cursor.execute(f"Update userss set blocked=true where tgid=%s", (i['tgid']))
                        db.commit()
                        del db
                    pass

            # payments
            db = Db()
            cursor = db.getCursor()
            cursor.execute(f"SELECT * FROM payments WHERE status <> 'success' and time < NOW() - INTERVAL 55 MINUTE")
            log = cursor.fetchall()
            del db

            for i in log:
                tgId = i['tgid']
                messageId = i['message_id']
                if messageId:
                    try:
                        BotCheck.delete_message(tgId, messageId)
                    except:
                        pass

            db = Db()
            cursor = db.getCursor()
            cursor.execute(f"DELETE FROM payments WHERE status <> 'success' and time < NOW() - INTERVAL 61 MINUTE")
            db.commit()
            del db

            db = Db()
            cursor = db.getCursor()
            cursor.execute(f"SELECT * FROM payments WHERE status <> 'success'")
            log = cursor.fetchall()
            del db

            testTimeSubscribe = 100 * 30 * 24 * 60 * 60

            for i in log:
                try:
                    paymentId = i['bill_id']

                    if i['time_to_add'] == testTimeSubscribe:
                        main.paymentSuccess(paymentId)

                    paymentData = Pay(PAYMENT_SYSTEM_CODE).findPay(paymentId)
                    if paymentData and paymentData['success']:
                        if paymentData['payment'].status == 'succeeded':
                            main.paymentSuccess(paymentId)

                except ApiTelegramException as exception:
                    if (exception.description == 'Forbidden: bot was blocked by the user'):
                        db = Db()
                        cursor = db.getCursor()
                        cursor.execute(f"Update userss set blocked=true where tgid=%s", (i['tgid']))
                        db.commit()
                        del db
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