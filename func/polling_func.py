import aiohttp
import asyncio
import logging
from * import more_class

class TelegramPollingBot:
    def __init__(self, bot_token):
        self.bot_token = bot_token
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/"
        self.commands = {}
        self.text_handlers = []

    # Метод для отримання оновлень через polling
    async def get_updates(self, offset=None):
        url = f"{self.api_url}getUpdates"
        params = {"offset": offset, "timeout": 60}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("result", [])
                return []

    # Метод для відправки повідомлень
    async def send_message(self, chat_id, text):
        url = f"{self.api_url}sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("result", {})
                return None

    # Метод polling для отримання оновлень
    async def run_polling(self):
        offset = None
        while True:
            updates = await self.get_updates(offset)
            for update in updates:
                offset = update["update_id"] + 1
                message_data = update.get("message")
                if message_data:
                    message = TelegramMessage(message_data)
                    await self.process_message(message)
            await asyncio.sleep(1)

    # Обробка отриманих повідомлень
    async def process_message(self, message):
        text = message.text

        # Обробка команд
        if text.startswith("/"):
            command = text.split()[0].lower()
            if command in self.commands:
                await self.commands[command](message)
        else:
            # Обробка звичайних повідомлень
            for handler in self.text_handlers:
                await handler(message)

    # Декоратор для обробки команд
    def command(self, commands, caps_ignore=True):
        def decorator(func):
            for command in commands:
                if caps_ignore:
                    self.commands[command.lower()] = func
                    self.commands[command.upper()] = func
                else:
                    self.commands[command] = func
            return func
        return decorator

    # Декоратор для обробки текстових повідомлень
    def send_message_handler(self, message_text, start_abc=False, caps_ignore=True):
        def decorator(func):
            async def wrapper(message):
                text = message.text
                if start_abc:
                    if any(text.lower().startswith(m.lower()) for m in message_text):
                        await func(message)
                else:
                    if caps_ignore:
                        if text.lower() in [m.lower() for m in message_text]:
                            await func(message)
                    else:
                        if text in message_text:
                            await func(message)
            self.text_handlers.append(wrapper)
            return wrapper
        return decorator
#
