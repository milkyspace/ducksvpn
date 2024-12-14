import pymysql
import pymysql.cursors

from modules.bot.config import Config

CONFIG = Config.getConfig()

DBHOST = CONFIG["db_host"]
DBUSER = CONFIG["db_user"]
DBPASSWORD = CONFIG["db_password"]
DBNAME = CONFIG["db_name"]

class Db:
    @classmethod
    def __init__(self):
        self.conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
        self.cur = self.conn.cursor(pymysql.cursors.DictCursor)

    def getCursor(self):
        return self.cur

    def commit(self):
        self.conn.commit()

    def __del__(self):
        self.cur.close()
        self.conn.close()

