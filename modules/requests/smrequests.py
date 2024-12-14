from modules.bot.config import Config
import requests
import json

CONFIG = Config.getConfig()

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
        }), timeout=120, verify=False)

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
                                     "Authorization": token}, timeout=120, verify=False)
    print('getConnectionLinks stop')
    print(response)
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
                                     "Authorization": token}, timeout=120, verify=False)

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
        data=json.dumps(update), timeout=240, verify=False)
    print('switchUserActivity response stop')
    print(response)
    if response:
        return True

    return False


async def switchUsersActivity(users, val):
    print('switchUsersActivity start')
    if (val == True):
        update = {
            "users": users,
            "enable": '1'
        }
    else:
        update = {
            "users": users,
            "enable": '0'
        }

    token = f"Bearer {await getToken()}"
    print('switchUsersActivity response start')
    print('switchUsersActivity token ' + str(token))
    print('switchUsersActivity json.dumps(update) ' + json.dumps(update))
    print('switchUsersActivity f"{SERVER_MANAGER_URL}/vpnservers/{tgid}" ' + f"{SERVER_MANAGER_URL}/vpnservers/0")
    response = requests.put(
        f"{SERVER_MANAGER_URL}/vpnservers/0",
        headers={"Accept": "application/json",
                 "Content-Type": "application/json",
                 "Authorization": token},
        data=json.dumps(update), timeout=240, verify=False)
    print('switchUsersActivity response stop')
    print(response)
    if response:
        return True

    return False
