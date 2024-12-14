import random
import string

from modules.bot.config import Config

CONFIG = Config.getConfig()

def randomword(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))