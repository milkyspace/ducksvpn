from modules.bot.config import Config
from yookassa import Configuration
from yookassa import Payment

CONFIG = Config.getConfig()

YOOKASSA_SHOP_ID = CONFIG["yookassa_shop_id"]
YOOKASSA_SECRET_KEY = CONFIG["yookassa_secret_key"]


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
