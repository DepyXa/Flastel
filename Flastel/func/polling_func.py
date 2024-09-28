import aiohttp
import asyncio
import logging

logger = logging.getLogger(__name__)

def keyboard_create(callback=None, reply_keyboard=None):
    reply_markup = None

    if callback:
        reply_markup = {"inline_keyboard": []}
        for key, value in callback.items():
            if value.startswith("http://") or value.startswith("https://"):
                reply_markup["inline_keyboard"].append([{"text": key, "url": value}])
            else:
                reply_markup["inline_keyboard"].append([{"text": key, "callback_data": value}])
    elif reply_keyboard:
        reply_markup = {
            "keyboard": [[{"text": button} for button in row] for row in reply_keyboard],
            "resize_keyboard": True,
            "one_time_keyboard": True
        }

    return reply_markup

class TelegramPollingBot:
    def __init__(self, bot_token, pro_logaut=False):
        self.bot_token = bot_token
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/"
        self.message_handlers = {}
        self.commands = {}
        self.param_commands = {}
        self.payment_handlers = {}
        self.successful_payment_handlers = {}
        self.pro_logaut = pro_logaut
        
    async def get_updates(self, offset=None):
        url = f"{self.api_url}getUpdates"
        params = {"offset": offset, "timeout": 60}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("result", [])
                    else:
                        logger.error(f"Ошибка получения обновлений: {response.status}")
                        await self.handle_server_error(response.status)
            except aiohttp.ClientError as e:
                logger.error(f"Ошибка соединения: {str(e)}")
                await self.wait_for_reconnect()

            return []

    async def wait_for_reconnect(self):
        wait_time = random.choice([60, 120, 1200])
        logger.info(f"Ожидание {wait_time} секунд перед повторной попыткой...")
        await asyncio.sleep(wait_time)

    async def handle_server_error(self, status_code):
        logger.error(f"Обработка ошибки сервера: {status_code}")
        await self.wait_for_reconnect()

    async def send_message(self, chat_id, text, parse_mode=None, callback=None, reply_keyboard=None):
        url = f"{self.api_url}sendMessage"
        reply_markup = keyboard_create(callback, reply_keyboard)
        payload = {
            "chat_id": chat_id,
            "text": text,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_markup:
            payload["reply_markup"] = reply_markup
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("result", {})
                logger.error(f"Ошибка отправки сообщения: {response.status}")
                return None

    async def send_pay(self, user_id, title, description, payload, currency, prices, in_support=True, provider_token=None, photo_url=None, photo_size=None, photo_width=None, photo_height=None):
        url = f"{self.api_url}sendInvoice"
        Prices = [{"label": prices[0], "amount": prices[1]}]
        if in_support:
            description_original = description + " For support/core bot Flastel."
            description = description_original
        if currency == "XTR":
          TEXT_BUTTON = f"⭐Pay {prices[1]}"
        else:
          TEXT_BUTTON = f"Pay {prices[1]} {currency}"
        payload_data = {
            "chat_id": user_id,
            "title": title,
            "description": description,
            "payload": payload,
            "provider_token": provider_token,
            "currency": currency,
            "prices": Prices,
            "start_parameter": "payment_start",
            "reply_markup": {
                "inline_keyboard": [
                    [{"text": TEXT_BUTTON, "pay": True}]
                ]
            }
        }
        if photo_url:
            payload_data.update({
                "photo_url": photo_url,
                "photo_size": photo_size,
                "photo_width": photo_width,
                "photo_height": photo_height
            })

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload_data) as response:
                    if response.status == 200:
                        data = await response.json()
                        invoice_data = json.loads(json.dumps(data.get("result", {})), object_hook=lambda d: SimpleNamespace(**d))
                        return invoice_data
                    else:
                        logging.error(f"Error: Received status code {response.status}")
                        return None
        except Exception as e:
            logging.error(f"Exception occurred: {str(e)}")
            return None

    async def run_polling(self):
        offset = 0
        while True:
            try:
                updates = await self.get_updates(offset)
                for update in updates:
                    offset = update["update_id"] + 1
                    message_data = update.get("message")
                    pre_checkout_query = update.get("pre_checkout_query")
                
                    if message_data:
                        successful_payment = update.get("message", {}).get("successful_payment")
                        if successful_payment:
                            payment_data = TelegramSuccessfulPayment(successful_payment)
                            handler = self.successful_payment_handlers.get((payment_data.currency, payment_data.total_amount))
                            if handler:
                                await handler(payment_data)
                            if self.pro_logaut:
                                logger.info(f"Успішний платіж: {payment_data.total_amount} {payment_data.currency}")
                        else:
                            message = TelegramMessage(message_data)
                            await self.process_message(message)
                            if self.pro_logaut:
                                logger.info(f"Получено сообщение: {message.text} от {message.from_user.all_name}")
                
                    if pre_checkout_query:
                        query_data = TelegramPAY(pre_checkout_query)
                        handler = self.payment_handlers.get((query_data.currency, query_data.total_amount))
                        if handler:
                            await handler(query_data)
                        if self.pro_logaut:
                            logger.info(f"Перевіряємо оплату.")

            except Exception as e:
                logger.error(f"Помилка під час обробки оновлень: {e}")
                await self.wait_for_reconnect()
        
            await asyncio.sleep(1)

    def pay_pre(self, currency, prices):
        def decorator(func):
            for price in prices:
                self.payment_handlers[(currency, price)] = func
            return func
        return decorator

    async def ok_pay(self, query_data):
        url = f"{self.api_url}answerPreCheckoutQuery"
        payload = {"pre_checkout_query_id": query_data.id, "ok": True}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Платіж підтверджено: {data}")
                else:
                    logger.error(f"Error: Received status code {response.status}")

    def successful_payment(self, currency, prices):
        def decorator(func):
            for price in prices:
                self.successful_payment_handlers[(currency, price)] = func
            return func
        return decorator

    async def process_message(self, message):
        text = message.text
        logger.info(f"Обробляється повідомлення: {text}")
        logger.info(f"Доступні команди: {self.commands.keys()}")

        if text.startswith("/"):
            parts = text.split()
            command = parts[0].lower()
            params = parts[1:] if len(parts) > 1 else []

            if command in self.param_commands:
                handler, allowed_params = self.param_commands[command]
                if params and any(param in allowed_params for param in params):
                    logger.info(f"Знайдено команду з параметрами: {params}")
                    await handler(message, params)
                    return

            if command in self.commands:
                logger.info(f"Знайдено команду без параметрів: {command}")
                await self.commands[command](message)
            else:
                logger.info(f"Команда {command} не знайдена в {self.commands}")
        else:
            await self.messges[messages_txt](message)

    def messages(self, messages_txt, caps_ignore=False):
        def decorator(func):
            for message_txt in messages_txt:
                if caps_ignore:
                    self.message_handlers[message_txt.lower()] = func
                    self.message_handlers[message_txt.upper()] = func
                else:
                    self.message_handlers[message_txt] = func
                logger.info(f"Текстовий хандлер зареєстрована: {message_txt}")
            return func
        return decorator

    def command(self, commands, caps_ignore=True):
        def decorator(func):
            for command in commands:
                if caps_ignore:
                    self.commands[command.lower()] = func
                    self.commands[command.upper()] = func
                else:
                    self.commands[command] = func
                logger.info(f"Команда зареєстрована: {command}")
            return func
        return decorator

    def command_with_params(self, commands, params, caps_ignore=True):
        def decorator(func):
            for command in commands:
                if caps_ignore:
                    self.param_commands[command.lower()] = (func, params)
                    self.param_commands[command.upper()] = (func, params)
                else:
                    self.param_commands[command] = (func, params)
            return func
        return decorator
class TelegramMessage:
    def __init__(self, message_data):
        self.chat_id = message_data["chat"]["id"]
        self.text = message_data.get("text", "")
        self.from_user = TelegramUser(message_data["from"])
        self.photo = message_data.get("photo", [])
        self.sticker = message_data.get("sticker", None)
        self.message_id = message_data.get("message_id", None)

class TelegramUser:
    def __init__(self, user_data):
        self.user_id = user_data["id"]
        self.first_name = user_data.get("first_name", "")
        self.last_name = user_data.get("last_name", "")
        self.username = user_data.get("username", "")
        self.all_name = f"{self.first_name} {self.last_name}".strip()

class TelegramPAY:
    def __init__(self, pay_data):
        self.id = pay_data["id"]
        self.currency = pay_data["currency"]
        self.total_amount = pay_data["total_amount"]
        self.payment_method = pay_data.get("payment_method", "unknown")

class TelegramSuccessfulPayment:
    def __init__(self, payment_data):
        self.chat_id = payment_data.get("chat", {}).get("id", None)
        self.currency = payment_data["currency"]
        self.total_amount = payment_data["total_amount"]
        self.invoice_payload = payment_data["invoice_payload"]
        self.shipping_option_id = payment_data.get("shipping_option_id", None)
        self.order_info = payment_data.get("order_info", {})
        self.provider_payment_charge_id = payment_data.get("provider_payment_charge_id", None)
