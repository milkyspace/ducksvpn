import time
import os
from dotenv import load_dotenv
import pymysql
import pymysql.cursors
import yookassa
from yookassa import Configuration
from yookassa import Payment

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

    "yookassa_shop_id": os.getenv("YOOKASSA_SHOP_ID"),
    "yookassa_secret_key": os.getenv("YOOKASSA_SECRET_KEY"),
}

YOOKASSA_SHOP_ID = CONFIG["yookassa_shop_id"]
YOOKASSA_SECRET_KEY = CONFIG["yookassa_secret_key"]

DBHOST = CONFIG["db_host"]
DBUSER = CONFIG["db_user"]
DBPASSWORD = CONFIG["db_password"]
DBNAME = CONFIG["db_name"]


class YooKassa:
    code = 'yookassa'

    def __init__(self):
        Configuration.configure(YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY)

    @classmethod
    async def init(cls):
        self = YooKassa()

    async def createPay(self, tgid, price, currency, label):
        res = Payment.create(
            {
                "amount": {
                    "value": price,
                    "currency": currency
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": f"https://t.me/{CONFIG['bot_name']}?pay_success=" + str(tgid)
                },
                "capture": True,
                "description": label,
            }
        )

        try:
            if res.confirmation and res.confirmation.confirmation_url:
                return {
                    'success': True,
                    'link': res.confirmation.confirmation_url,
                    'id': res.id
                }
        except:
            pass

        return {
            'success': False,
            'link': '',
            'id': ''
        }

    def findPay(self, id):
        try:
            payment = Payment.find_one(id)
            return {
                'success': True,
                'payment': payment,
            }
        except:
            pass

        return {
            'success': False,
            'payment': {},
        }
