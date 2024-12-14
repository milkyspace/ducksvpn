import time
from datetime import datetime
from telebot import types
from telebot.apihelper import ApiTelegramException
import emoji as e
import traceback

import main
from modules.db.db import Db
from modules.bot.config import Config
from modules.users.dbworker import User
from modules.bot.buttons import main_buttons, admin_buttons, admin_buttons_edit_user, admin_buttons_back, \
    admin_buttons_output_users
from modules.requests.smrequests import getConnectionLinks, getAmneziaConnectionFile, switchUserActivity, \
    switchUsersActivity, addUser

CONFIG = Config.getConfig()

SUPPORT_LINK = CONFIG["support_link"]


async def editUser(m: types.Message, bot, MyStates):
    async with bot.retrieve_data(m.from_user.id) as data:
        tgid = data['usertgid']
    user_dat = await User.GetInfo(tgid)
    if e.demojize(m.text) == "Назад :right_arrow_curving_left:":
        await bot.reset_data(m.from_user.id)
        await bot.delete_state(m.from_user.id)
        await bot.send_message(m.from_user.id, "Вернул вас назад!", reply_markup=await admin_buttons())
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


async def editUserResetTime(m: types.Message, bot, MyStates):
    async with bot.retrieve_data(m.from_user.id) as data:
        tgid = data['usertgid']

    if e.demojize(m.text) == "Да":
        db = Db()
        cursor = db.getCursor()
        cursor.execute(f"Update userss set subscription = %s, banned=false where tgid=%s",
                       (str(int(time.time())), tgid))
        db.commit()
        del db

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
                           reply_markup=await admin_buttons_edit_user(user_dat), parse_mode="HTML")


async def UserAddTimeDays(m: types.Message, bot, MyStates):
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


async def UserAddTimeHours(m: types.Message, bot, MyStates):
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


async def UserAddTimeMinutes(m: types.Message, bot, MyStates):
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


async def UserAddTimeApprove(m: types.Message, bot, MyStates):
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
        await main.AddTimeToUser(tgid, all_time)

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
                           reply_markup=await admin_buttons_edit_user(user_dat), parse_mode="HTML")


async def findUserViaId(m: types.Message, bot, MyStates):
    await bot.delete_state(m.from_user.id)
    try:
        user_id = int(m.text)
    except:
        await bot.send_message(m.from_user.id, "Неверный Id!", reply_markup=await admin_buttons())
        return
    user_dat = await User.GetInfo(user_id)
    if not user_dat.registered:
        await bot.send_message(m.from_user.id, "Такого пользователя не существует!",
                               reply_markup=await admin_buttons())
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
                           reply_markup=await admin_buttons_edit_user(user_dat), parse_mode="HTML")


async def prepareUserForSendMessage(m: types.Message, bot, MyStates):
    await bot.delete_state(m.from_user.id)
    try:
        user_id = int(m.text)
    except:
        await bot.send_message(m.from_user.id, "Неверный Id!", reply_markup=await admin_buttons())
        return
    user_dat = await User.GetInfo(user_id)
    if not user_dat.registered:
        await bot.send_message(m.from_user.id, "Такого пользователя не существует!",
                               reply_markup=await admin_buttons())
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


async def sendMessageToUser(m: types.Message, bot, MyStates):
    async with bot.retrieve_data(m.from_user.id) as data:
        tgid = data['usertgid']
    await bot.send_message(tgid, e.emojize(m.text), parse_mode="HTML")
    await bot.delete_state(m.from_user.id)
    await bot.send_message(m.from_user.id, "Сообщение отправлено", reply_markup=await admin_buttons())


async def sendMessageToAllUser(m: types.Message, bot, MyStates):
    if e.demojize(m.text) == "Назад :right_arrow_curving_left:":
        await bot.delete_state(m.from_user.id)
        await bot.send_message(m.from_user.id, "Вернул вас назад!", reply_markup=await admin_buttons())
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
    await bot.send_message(m.from_user.id, "Сообщения отправлены", reply_markup=await admin_buttons())
    return


async def sendMessageToAmneziaUser(m: types.Message, bot, MyStates):
    if e.demojize(m.text) == "Назад :right_arrow_curving_left:":
        await bot.delete_state(m.from_user.id)
        await bot.send_message(m.from_user.id, "Вернул вас назад!", reply_markup=await admin_buttons())
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
    await bot.send_message(m.from_user.id, "Сообщения отправлены", reply_markup=await admin_buttons())
    return


async def sendMessageToAllInactiveUser(m: types.Message, bot, MyStates):
    if e.demojize(m.text) == "Назад :right_arrow_curving_left:":
        await bot.delete_state(m.from_user.id)
        await bot.send_message(m.from_user.id, "Вернул вас назад!", reply_markup=await admin_buttons())
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
    await bot.send_message(m.from_user.id, "Сообщения отправлены", reply_markup=await admin_buttons())
    return


async def sendMessageToLast50User(m: types.Message, bot, MyStates):
    if e.demojize(m.text) == "Назад :right_arrow_curving_left:":
        await bot.delete_state(m.from_user.id)
        await bot.send_message(m.from_user.id, "Вернул вас назад!", reply_markup=await admin_buttons())
        return

    db = Db()
    cursor = db.getCursor()
    cursor.execute(f"SELECT * FROM userss order by id desc limit 50")
    log = cursor.fetchall()
    del db

    for i in log:
        try:
            supportButtons = types.InlineKeyboardMarkup(row_width=1)
            supportButtons.add(
                types.InlineKeyboardButton(e.emojize(":woman_technologist: Чат с поддержкой"),
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
    await bot.send_message(m.from_user.id, "Сообщения отправлены", reply_markup=await admin_buttons())
    return


async def findUsersByName(m: types.Message, bot, MyStates):
    if e.demojize(m.text) == "Назад :right_arrow_curving_left:":
        await bot.delete_state(m.from_user.id)
        await bot.send_message(m.from_user.id, "Вернул вас назад!", reply_markup=await admin_buttons())
        return

    user_dat = await User.GetInfo(m.from_user.id)
    allusers = await user_dat.GetAllUsers()
    for i in allusers:
        if i['username'] == m.text or i['username'] == '@' + m.text:
            try:
                await bot.send_message(m.from_user.id, "Пользователь найден:",
                                       reply_markup=await admin_buttons())
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
                           reply_markup=await admin_buttons())
    await bot.delete_state(m.from_user.id)
    return


async def switchActiveUserManual(m: types.Message, bot, MyStates):
    if e.demojize(m.text) == "Назад :right_arrow_curving_left:":
        await bot.delete_state(m.from_user.id)
        await bot.send_message(m.from_user.id, "Вернул вас назад!", reply_markup=await admin_buttons())
        return

    user_dat = await User.GetInfo(m.from_user.id)
    allusers = await user_dat.GetAllUsers()
    for i in allusers:
        if i['username'] == m.text or i['username'] == '@' + m.text or i['tgid'] == m.text:
            try:
                await bot.send_message(m.from_user.id, "Пользователь найден:",
                                       reply_markup=await admin_buttons())
                await bot.send_message(m.from_user.id, f"{i['tgid']}", parse_mode="HTML")
                await bot.send_message(m.from_user.id, f"{i['username']}", parse_mode="HTML")
                await bot.send_message(m.from_user.id, f"Полное имя: {i['fullname']}", parse_mode="HTML")
                await bot.send_message(m.from_user.id,
                                       f"Подписка до: {datetime.utcfromtimestamp(int(i['subscription']) + CONFIG['UTC_time'] * 3600).strftime('%d.%m.%Y %H:%M')}",
                                       parse_mode="HTML")
                if i['banned'] == False:
                    await switchUserActivity(str(i['tgid']), True)
                    await bot.send_message(m.from_user.id, f"Пользователь активирован", parse_mode="HTML")
                else:
                    await bot.send_message(m.from_user.id, f"У пользователя закончилась подписка", parse_mode="HTML")

                await bot.delete_state(m.from_user.id)
                return
            except TypeError:
                await bot.send_message(m.from_user.id, f"Произошла какая-то ошибка", parse_mode="HTML")
                pass

    await bot.send_message(m.from_user.id, "Пользователь не найден",
                           reply_markup=await admin_buttons())
    await bot.delete_state(m.from_user.id)
    return


async def updateAllUsers(m: types.Message, bot, MyStates):
    if e.demojize(m.text) == "Назад :right_arrow_curving_left:":
        await bot.delete_state(m.from_user.id)
        await bot.send_message(m.from_user.id, "Вернул вас назад!", reply_markup=await admin_buttons())
        return

    db = Db()
    cursor = db.getCursor()
    cursor.execute(f"SELECT * FROM userss where banned = true")
    log = cursor.fetchall()
    del db

    try:
        disabled = []
        for i in log:
            disabled.append(i['tgid'])
        await switchUsersActivity(disabled, False)
    except Exception as err:
        print('UPDATE DISABLED USERS ERROR')
        print(err)
        print(traceback.format_exc())
        pass

    db = Db()
    cursor = db.getCursor()
    cursor.execute(f"SELECT * FROM userss where banned = false")
    log = cursor.fetchall()
    del db

    try:
        enabled = []
        for i in log:
            enabled.append(i['tgid'])
        await switchUsersActivity(enabled, True)

    except Exception as err:
        print('UPDATE ENABLED USERS ERROR')
        print(err)
        print(traceback.format_exc())
        pass

    await bot.send_message(m.from_user.id, "Обновления запущены в очередь",
                           reply_markup=await admin_buttons())
    await bot.delete_state(m.from_user.id)
    return


async def update50Users(m: types.Message, bot, MyStates):
    if e.demojize(m.text) == "Назад :right_arrow_curving_left:":
        await bot.delete_state(m.from_user.id)
        await bot.send_message(m.from_user.id, "Вернул вас назад!", reply_markup=await admin_buttons())
        return

    db = Db()
    cursor = db.getCursor()
    cursor.execute(f"SELECT * FROM userss order by id desc limit 50")
    log = cursor.fetchall()
    del db

    try:
        for i in log:
            # user = await User.GetInfo(i['tgid'])
            print('Пользователь ' + i['tgid'])
            await addUser(i['tgid'], i['username'])
            # timenow = int(time.time())
            # if int(user.subscription) < timenow:
            #     await switchUserActivity(str(i['tgid']), False)
            # if int(user.subscription) >= timenow:
            #     await switchUserActivity(str(i['tgid']), True)

    except Exception as err:
        print('UPDATE 10 USERS ERROR')
        print(err)
        print(traceback.format_exc())
        pass

    await bot.send_message(m.from_user.id, "Обновления запущены в очередь",
                           reply_markup=await admin_buttons())
    await bot.delete_state(m.from_user.id)
    return
