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
    "server_manager_token": os.getenv("SERVER_MANAGER_TOKEN"),
}

SERVER_MANAGER_URL = CONFIG["server_manager_url"]
SERVER_MANAGER_EMAIL = CONFIG["server_manager_email"]
SERVER_MANAGER_PASSWORD = CONFIG["server_manager_password"]
SERVER_MANAGER_TOKEN = CONFIG["server_manager_token"]


async def getToken():
    return SERVER_MANAGER_TOKEN


async def addUser(userid, username, type=''):
    token = f"Bearer {await getToken()}"
    response = requests.post(
        f"{SERVER_MANAGER_URL}/vpnservers",
        headers={"Accept": "application/json",
                 "Content-Type": "application/json",
                 "Authorization": token},
        data=json.dumps({
            "id": str(userid),
            "name": str(username),
            "limit_ip": 3,
            "type": type,
        }), timeout=10, verify=False)

    if response:
        return True

    return False


async def getConnectionLinks(tgId, keyType='default'):
    print('getConnectionLinks start')
    token = f"Bearer {await getToken()}"
    requestAddress = f"{SERVER_MANAGER_URL}/vpnservers/{tgId}/getLink/{keyType}"
    if keyType == 'TikTok':
        requestAddress = requestAddress + '/' + keyType
    response = requests.get(requestAddress,
                            headers={"Accept": "application/json",
                                     "Content-Type": "application/json",
                                     "Authorization": token}, timeout=10, verify=False)
    print('getConnectionLinks stop')
    if response:
        print('getConnectionLinks response success')
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
        print('getConnectionLinks response NOT success')
        return {
            'success': False,
            'data': {}
        }


async def getAmneziaConnectionFile(tgId):
    token = f"Bearer {await getToken()}"
    response = requests.get(f"{SERVER_MANAGER_URL}/vpnservers/{tgId}/getAmneziaFile",
                            headers={"Accept": "application/json",
                                     "Content-Type": "application/json",
                                     "Authorization": token}, timeout=10, verify=False)

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
    print('switchUserActivity start')
    if (val == True):
        update = {
            "enable": '1'
        }
    else:
        update = {
            "enable": '0'
        }

    update.update({'limit_ip': 3})

    token = f"Bearer {await getToken()}"
    print('switchUserActivity response start')
    print('switchUserActivity token ' + str(token))
    print('switchUserActivity json.dumps(update) ' + json.dumps(update))
    print('switchUserActivity f"{SERVER_MANAGER_URL}/vpnservers/{tgid}" ' + f"{SERVER_MANAGER_URL}/vpnservers/{tgid}")
    response = requests.put(
        f"{SERVER_MANAGER_URL}/vpnservers/{tgid}",
        headers={"Accept": "application/json",
                 "Content-Type": "application/json",
                 "Authorization": token},
        data=json.dumps(update), timeout=10, verify=False)
    print('switchUserActivity response stop')
    print(response)
    if response:
        return True

    return False
