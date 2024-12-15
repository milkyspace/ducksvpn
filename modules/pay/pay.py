from modules.bot.config import Config
from modules.pay.yookassapay import YooKassa

CONFIG = Config.getConfig()


class Pay:
    paySystem = YooKassa()
    STATUS_CREATED = 'created'
    STATUS_SUCCESS = 'success'
    STATUS_FAIL = 'fail'

    def __init__(self, paySystemCode):
        self.paySystem = None
        if (paySystemCode == YooKassa.code):
            self.paySystem = YooKassa()

    @classmethod
    async def createPay(self, tgid, price, currency, label):
        return await self.paySystem.createPay(tgid=tgid, price=price, currency=currency, label=label)

    def findPay(self, id):
        return self.paySystem.findPay(id)
