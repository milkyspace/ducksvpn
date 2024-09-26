from dbworker import User
from telebot import types
import emoji as e
import time
from datetime import datetime

CONFIG={}

async def main_buttons(user: User):
    Butt_main = types.InlineKeyboardMarkup()
    if user.subscription != "none":
        dateto = datetime.utcfromtimestamp(int(user.subscription)+CONFIG["UTC_time"]*3600).strftime('%d.%m.%Y %H:%M')
        timenow = int(time.time())
        if int(user.subscription)<timenow:
            Butt_main.add(types.InlineKeyboardButton(e.emojize(f":red_circle: Подписка закончилась: {dateto} МСК")))
        if int(user.subscription)>=timenow:
            Butt_main.add(types.InlineKeyboardButton(e.emojize(f":green_circle: Подписка активна до: {dateto} МСК")))

        Butt_main.add(types.InlineKeyboardButton(e.emojize(f"Продлить подписку :money_bag:")),types.KeyboardButton(e.emojize(f"Как подключить :gear:")))

        if user.trial_subscription == True:
            Butt_main.add(types.InlineKeyboardButton(e.emojize(f"Почему стоит выбрать нас? :smiling_face_with_sunglasses:")))

        if user.tgid in CONFIG["admin_tg_id"]:
            Butt_main.add(types.InlineKeyboardButton(e.emojize(f"Админ-панель :smiling_face_with_sunglasses:")))
        return Butt_main

async def admin_buttons():
    Butt_admin = types.ReplyKeyboardMarkup(resize_keyboard=True)
    Butt_admin.add(types.KeyboardButton(e.emojize(f"Вывести пользователей :bust_in_silhouette:")))
    Butt_admin.add(types.KeyboardButton(e.emojize(f"Редактировать пользователя по id")))
    Butt_admin.add(types.KeyboardButton(e.emojize(f"Отправить пользователю сообщение :pencil:")))
    Butt_admin.add(types.KeyboardButton(e.emojize(f"Статичные пользователи")))
    Butt_admin.add(types.KeyboardButton(e.emojize(f"Продлить пробный период")))
    Butt_admin.add(types.KeyboardButton(e.emojize("Главное меню :right_arrow_curving_left:")))
    return Butt_admin

async def admin_buttons_output_users():
    Butt_admin = types.ReplyKeyboardMarkup(resize_keyboard=True)
    Butt_admin.add(types.KeyboardButton(e.emojize(f"Пользователей с подпиской")))
    Butt_admin.add(types.KeyboardButton(e.emojize(f"Всех пользователей")))
    Butt_admin.add(types.KeyboardButton(e.emojize("Назад :right_arrow_curving_left:")))
    return Butt_admin

async def admin_buttons_static_users():
    Butt_admin = types.ReplyKeyboardMarkup(resize_keyboard=True)
    Butt_admin.add(types.KeyboardButton(e.emojize(f"Добавить пользователя :plus:")))
    Butt_admin.add(types.KeyboardButton(e.emojize(f"Вывести статичных пользователей")))
    Butt_admin.add(types.KeyboardButton(e.emojize("Назад :right_arrow_curving_left:")))
    return Butt_admin

async def admin_buttons_edit_user(user: User):
    Butt_admin = types.ReplyKeyboardMarkup(resize_keyboard=True)
    Butt_admin.add(types.KeyboardButton(e.emojize(f"Добавить время")))
    if int(user.subscription) > int(time.time()):
        Butt_admin.add(types.KeyboardButton(e.emojize(f"Обнулить время")))
    Butt_admin.add(types.KeyboardButton(e.emojize("Назад :right_arrow_curving_left:")))
    return Butt_admin

async def admin_buttons_back():
    Butt_admin = types.ReplyKeyboardMarkup(resize_keyboard=True)
    Butt_admin.add(types.KeyboardButton(e.emojize("Назад :right_arrow_curving_left:")))
    return Butt_admin
