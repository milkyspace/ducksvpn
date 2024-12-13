import os
from dotenv import load_dotenv
import json
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
    "server_manager_token": os.getenv("SERVER_MANAGER_TOKEN"),
}

DBHOST = CONFIG["db_host"]
DBUSER = CONFIG["db_user"]
DBPASSWORD = CONFIG["db_password"]
DBNAME = CONFIG["db_name"]

async def addUserQueue(userid, username, type=''):
    data = {
        'user_id': userid,
        'user_name': username,
    }
    dataJson = json.dumps(data, indent=2)

    conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
    dbCur = conn.cursor(pymysql.cursors.DictCursor)
    dbCur.execute(f"insert into queue (type,status,data) values (%s,%s,%s)",('add_user', 'new', dataJson))
    conn.commit()
    dbCur.close()
    conn.close()

async def switchUserActivityQueue(tgid, val):
    data = {
        'tgid': tgid,
        'val': val,
    }
    dataJson = json.dumps(data, indent=2)

    conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASSWORD, database=DBNAME)
    dbCur = conn.cursor(pymysql.cursors.DictCursor)
    dbCur.execute(f"insert into queue (type,status,data) values (%s,%s,%s)", ('switch_user', 'new', dataJson))
    conn.commit()
    dbCur.close()
    conn.close()