import time
import pymysql
import pymysql.cursors

CONFIG={}

SERVER_MANAGER_URL = CONFIG["server_manager_url"]
SERVER_MANAGER_EMAIL = CONFIG["server_manager_email"]
SERVER_MANAGER_PASSWORD = CONFIG["server_manager_password"]

DBHOST = "localhost"
DBUSER = "vpnducks"
DBPASSWORD = "199612Kolva"
DBNAME = "ducksvpn"


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
                f"INSERT INTO userss (tgid,subscription,username,fullname,referrer_id) values (%s,%s,%s,%s,%s)",
                (self.tgid, str(int(time.time()) + int(CONFIG['trial_period']) * 86400), str(username),
                 str(full_name), referrer_id))
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

        print()

        return 0 if log[0] is None else log[0]['count']
