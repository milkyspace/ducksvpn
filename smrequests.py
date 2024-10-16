import requests
import json

CONFIG={}

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
