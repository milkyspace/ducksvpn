import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    @classmethod
    def getConfig(cls):
        return {
            "admin_tg_id": [int(os.getenv("ADMIN_TG_ID_1")), int(os.getenv("ADMIN_TG_ID_2")),
                            int(os.getenv("ADMIN_TG_ID_3"))],
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
            "payment_system_code": os.getenv("PAYMENT_SYSTEM_CODE"),
            "support_link": os.getenv("SUPPORT_LINK"),
            "support_username": os.getenv("SUPPORT_USERNAME"),
            "backup_dir": os.getenv("BACKUP_DIR"),
        }
