import time
import os
from dotenv import load_dotenv
import pymysql
import pymysql.cursors

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
}

SERVER_MANAGER_URL = CONFIG["server_manager_url"]
SERVER_MANAGER_EMAIL = CONFIG["server_manager_email"]
SERVER_MANAGER_PASSWORD = CONFIG["server_manager_password"]

DBHOST = CONFIG["db_host"]
DBUSER = CONFIG["db_name"]
DBPASSWORD = CONFIG["db_user"]
DBNAME = CONFIG["db_password"]


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

    @classmethod
    async def GetInfo(cls, tgid):
        self = User()
        self.tgid = tgid

        conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
        dbCur = conn.cursor(pymysql.cursors.DictCursor)
        dbCur.execute("SELECT * FROM userss WHERE tgid= %s ", (tgid))
        log = dbCur.fetchone()
        dbCur.close()
        conn.close()

        if not log is None:
            self.id = log["id"]
            self.subscription = log["subscription"]
            self.trial_subscription = log["banned"]
            self.registered = True
            self.username = log["username"]
            self.fullname = log["fullname"]
            self.referrer_id = log["referrer_id"]
            self.type = log["type"]
        else:
            self.registered = False
        return self

    async def PaymentInfo(self):
        conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
        dbCur = conn.cursor(pymysql.cursors.DictCursor)
        dbCur.execute(f"SELECT * FROM payments where tgid=%s", (self.tgid,))
        log = dbCur.fetchone()
        dbCur.close()
        conn.close()

        return log

    async def CancelPayment(self):
        conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
        dbCur = conn.cursor(pymysql.cursors.DictCursor)
        dbCur.execute(f"DELETE FROM payments where tgid=%s",
                      (self.tgid,))
        conn.commit()
        dbCur.close()
        conn.close()

    async def NewPay(self, bill_id, summ, time_to_add, mesid):
        conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
        dbCur = conn.cursor(pymysql.cursors.DictCursor)
        dbCur.execute(f"INSERT INTO payments (tgid,bill_id,amount,time_to_add,mesid) values (%s,%s,%s,%s,%s)",
                      (self.tgid, str(bill_id), summ, int(time_to_add), str(mesid)))
        conn.commit()
        dbCur.close()
        conn.close()

    async def GetAllPaymentsInWork(self):
        conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
        dbCur = conn.cursor(pymysql.cursors.DictCursor)
        dbCur.execute(f"SELECT * FROM payments")
        log = dbCur.fetchall()
        dbCur.close()
        conn.close()

        return log

    async def Adduser(self, userid, username, full_name, referrer_id):
        if self.registered == False:
            conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
            dbCur = conn.cursor(pymysql.cursors.DictCursor)
            dbCur.execute(
                f"INSERT INTO userss (tgid,subscription,username,fullname,referrer_id, type) values (%s,%s,%s,%s,%s,%s)",
                (self.tgid, str(int(time.time()) + int(CONFIG['trial_period']) * 86400), str(username),
                 str(full_name), referrer_id, 'xui'))
            conn.commit()
            dbCur.close()
            conn.close()

            self.registered = True

    async def GetAllUsers(self):
        conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
        dbCur = conn.cursor(pymysql.cursors.DictCursor)
        dbCur.execute(f"SELECT * FROM userss")
        log = dbCur.fetchall()
        dbCur.close()
        conn.close()

        return log

    async def GetAllUsersWithSub(self):
        conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
        dbCur = conn.cursor(pymysql.cursors.DictCursor)
        dbCur.execute(f"SELECT * FROM userss where subscription > %s", (str(int(time.time())),))
        log = dbCur.fetchall()
        dbCur.close()
        conn.close()
        return log

    async def GetAllUsersWithoutSub(self):
        conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
        dbCur = conn.cursor(pymysql.cursors.DictCursor)
        dbCur.execute(f"SELECT * FROM userss where banned = true")
        log = dbCur.fetchall()
        dbCur.close()
        conn.close()

        return log

    async def CheckNewNickname(self, message):
        try:
            username = "@" + str(message.from_user.username)
        except:
            username = str(message.from_user.id)

        if message.from_user.full_name != self.fullname or username != self.username:
            conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
            dbCur = conn.cursor(pymysql.cursors.DictCursor)
            dbCur.execute(f"Update userss set username = %s, fullname = %s where id = %s",
                          (username, message.from_user.full_name, self.id))
            conn.commit()
            dbCur.close()
            conn.close()

    async def countReferrerByUser(self):
        conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
        dbCur = conn.cursor(pymysql.cursors.DictCursor)
        dbCur.execute(f"select count(*) as count from userss where referrer_id=%s",
                      (self.tgid,))
        log = dbCur.fetchall()
        dbCur.close()
        conn.close()

        return 0 if log[0] is None else log[0]['count']

    async def changeType(self):
        conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
        dbCur = conn.cursor(pymysql.cursors.DictCursor)
        dbCur.execute("SELECT * FROM userss WHERE tgid= %s ", (self.tgid,))
        log = dbCur.fetchone()
        dbCur.close()
        conn.close()

        if log is None:
            return False

        newType = 'xui'
        if log['type'] is None or log['type'] == 'amnezia':
            newType = 'xui'
        elif log['type'] == 'xui':
            newType = 'amnezia'

        conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
        dbCur = conn.cursor(pymysql.cursors.DictCursor)
        dbCur.execute(f"Update userss set type = %s where tgid = %s",
                      (newType, self.tgid))
        conn.commit()
        dbCur.close()
        conn.close()

        return True