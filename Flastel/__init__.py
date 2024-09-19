from .func.polling_func import TelegramPollingBot, polling_func
from .func.webhook_func import webhook_func
from .func.methods import TelegramBot

__all__ = ["polling_func", "webhook_func", "TelegramBot", "TelegramPollingBot"]
