import os
from dotenv import load_dotenv
import requests
import json

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


async def getToken(breakLoop=True):
    response = requests.post(f"{SERVER_MANAGER_URL}/auth/login",
                             headers={"Content-Type": "application/json", },
                             data=json.dumps({"email": SERVER_MANAGER_EMAIL, "password": SERVER_MANAGER_PASSWORD}))
    if response:
        return response.json()["token"]
    elif breakLoop:
        requests.get(f"{SERVER_MANAGER_URL}/sanctum/csrf-cookie")
        return await getToken(False)
    else:
        return ""


def getTokenDefault(breakLoop=True):
    response = requests.post(f"{SERVER_MANAGER_URL}/auth/login",
                             headers={"Content-Type": "application/json", },
                             data=json.dumps({"email": SERVER_MANAGER_EMAIL, "password": SERVER_MANAGER_PASSWORD}))
    if response:
        return response.json()["token"]
    elif breakLoop:
        requests.get(f"{SERVER_MANAGER_URL}/sanctum/csrf-cookie")
        return getToken(False)
    else:
        return ""


async def addUser(userid, username):
    token = f"Bearer {await getToken()}"
    response = requests.post(
        f"{SERVER_MANAGER_URL}/vpnservers",
        headers={"Accept": "application/json",
                 "Content-Type": "application/json",
                 "Authorization": token},
        data=json.dumps({
            "tg_id": str(userid),
            "name": str(username),
            "limit_ip": 3
        }))

    if response:
        return True

    print(response.content)
    return False


async def getConnectionLinks(tgId):
    token = f"Bearer {await getToken()}"
    response = requests.get(f"{SERVER_MANAGER_URL}/vpnservers/{tgId}/getLink",
                            headers={"Accept": "application/json",
                                     "Content-Type": "application/json",
                                     "Authorization": token})
    if response:
        jsonResponse = response.json()
        data = jsonResponse['data']
        link = data['link']
        qrCode = data['qr_code']  # qrCode['html'] and qrCode['svg']

        return {
            'success': True,
            'data': {
                'link': link,
                'qrCode': qrCode
            }
        }
    else:
        return {
            'success': False,
            'data': {}
        }


async def getAmneziaConnectionFile(tgId):
    token = f"Bearer {await getToken()}"
    response = requests.get(f"{SERVER_MANAGER_URL}/vpnservers/{tgId}/getAmneziaFile",
                            headers={"Accept": "application/json",
                                     "Content-Type": "application/json",
                                     "Authorization": token})

    if response:
        contentDisposition = response.headers["Content-Disposition"]
        filename = f"data/{contentDisposition.split('filename=')[1]}"
        with open(filename, "wb") as code:
            code.write(response.content)
        configFull = open(filename, 'rb')

        return {
            'success': True,
            'data': {
                'file': configFull,
            }
        }
    else:
        return {
            'success': False,
            'data': {}
        }


async def switchUserActivity(tgid, val):
    if (val == True):
        update = {
            "expiry_time": '0',
            "enable": '1'
        }
    else:
        update = {
            "expiry_time": 'now',
            "enable": '0'
        }

    update.update({'limit_ip': 3})

    token = f"Bearer {await getToken()}"
    response = requests.put(
        f"{SERVER_MANAGER_URL}/vpnservers/{tgid}",
        headers={"Accept": "application/json",
                 "Content-Type": "application/json",
                 "Authorization": token},
        data=json.dumps(update))

    if response:
        return True

    return False
