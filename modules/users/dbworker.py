import time

from modules.db.db import Db
from modules.bot.config import Config

CONFIG = Config.getConfig()

SERVER_MANAGER_URL = CONFIG["server_manager_url"]
SERVER_MANAGER_EMAIL = CONFIG["server_manager_email"]
SERVER_MANAGER_PASSWORD = CONFIG["server_manager_password"]


class User:
    def __init__(self):
        self.id = None
        self.tgid = None
        self.subscription = None
        self.trial_subscription = True
        self.registered = False
        self.username = None
        self.fullname = None
        self.referrer_id = None
        self.type = None
        self.blocked = None

    @classmethod
    async def GetInfo(cls, tgid):
        self = User()
        self.tgid = tgid

        db = Db()
        cursor = db.getCursor()
        cursor.execute("SELECT * FROM userss WHERE tgid= %s ", (tgid))
        log = cursor.fetchone()
        del db

        if not log is None:
            self.id = log["id"]
            self.subscription = log["subscription"]
            self.trial_subscription = log["banned"]
            self.registered = True
            self.username = log["username"]
            self.fullname = log["fullname"]
            self.referrer_id = log["referrer_id"]
            self.type = log["type"]
            self.blocked = log["blocked"]
        else:
            self.registered = False
        return self

    async def PaymentInfo(self):
        db = Db()
        cursor = db.getCursor()
        cursor.execute(f"SELECT * FROM payments where tgid=%s", (self.tgid,))
        log = cursor.fetchone()
        del db

        return log

    async def CancelPayment(self):
        db = Db()
        cursor = db.getCursor()
        cursor.execute(f"DELETE FROM payments where tgid=%s",
                       (self.tgid,))
        db.commit()
        del db

    async def NewPay(self, bill_id, summ, time_to_add, mesid, status='success', messageId=0, additional=''):
        db = Db()
        cursor = db.getCursor()
        cursor.execute(
            f"INSERT INTO payments (tgid,bill_id,amount,time_to_add,mesid,status,message_id,additional) values (%s,%s,%s,%s,%s,%s,%s,%s)",
            (self.tgid, str(bill_id), summ, int(time_to_add), str(mesid), status, messageId, additional))
        db.commit()
        del db

    async def GetAllPaymentsInWork(self):
        db = Db()
        cursor = db.getCursor()
        cursor.execute(f"SELECT * FROM payments")
        log = cursor.fetchall()
        del db

        return log

    async def newGift(self, payment_id, secret, status='new'):
        db = Db()
        cursor = db.getCursor()
        cursor.execute(f"INSERT INTO gifts (sender_tgid,payment_id,secret,status) values (%s,%s,%s,%s)",
                       (self.tgid, str(payment_id), secret, status))
        id = cursor.lastrowid
        db.commit()
        del db

        if id is None:
            return 0
        return id

    async def Adduser(self, userid, username, full_name, referrer_id):
        if self.registered == False:
            db = Db()
            cursor = db.getCursor()
            cursor.execute(
                f"INSERT INTO userss (tgid,subscription,username,fullname,referrer_id, type) values (%s,%s,%s,%s,%s,%s)",
                (self.tgid, str(int(time.time()) + int(CONFIG['trial_period']) * 86400), str(username),
                 str(full_name), referrer_id, 'xui'))
            db.commit()
            del db

            self.registered = True

    async def GetAllUsers(self):
        db = Db()
        cursor = db.getCursor()
        cursor.execute(f"SELECT * FROM userss where blocked=false")
        log = cursor.fetchall()
        del db

        return log

    async def GetAllUsersWithSub(self):
        db = Db()
        cursor = db.getCursor()
        cursor.execute(f"SELECT * FROM userss where subscription > %s", (str(int(time.time())),))
        log = cursor.fetchall()
        del db

        return log

    async def GetAllUsersWithoutSub(self):
        db = Db()
        cursor = db.getCursor()
        cursor.execute(f"SELECT * FROM userss where banned = true")
        log = cursor.fetchall()
        del db

        return log

    async def CheckNewNickname(self, message):
        try:
            username = "@" + str(message.from_user.username)
        except:
            username = str(message.from_user.id)

        if message.from_user.full_name != self.fullname or username != self.username:
            db = Db()
            cursor = db.getCursor()
            cursor.execute(f"Update userss set username = %s, fullname = %s where id = %s",
                           (username, message.from_user.full_name, self.id))
            db.commit()
            del db

    async def countReferrerByUser(self):
        db = Db()
        cursor = db.getCursor()
        cursor.execute(f"select count(*) as count from userss where referrer_id=%s",
                       (self.tgid,))
        log = cursor.fetchall()
        del db

        return 0 if log[0] is None else log[0]['count']

    async def changeType(self):
        db = Db()
        cursor = db.getCursor()
        cursor.execute("SELECT * FROM userss WHERE tgid= %s ", (self.tgid,))
        log = cursor.fetchall()
        del db

        if log is None:
            return False

        newType = 'xui'
        if log['type'] is None or log['type'] == 'amnezia':
            newType = 'xui'
        elif log['type'] == 'xui':
            newType = 'amnezia'

        db = Db()
        cursor = db.getCursor()
        cursor.execute(f"Update userss set type = %s where tgid = %s",
                       (newType, self.tgid))
        db.commit()
        del db

        return True
