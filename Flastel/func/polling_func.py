import time
import aiohttp
import asyncio
import logging
from typing import List, Callable

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

def convert_time(self, time_str):
        if time_str == "9999w":
            return None
        num, unit = int(time_str[:-1]), time_str[-1]
        current_time = int(time.time())

        if unit == 's':
            return current_time + num
        elif unit == 'm':
            return current_time + num * 60
        elif unit == 'h':
            return current_time + num * 3600
        elif unit == 'd':
            return current_time + num * 86400
        elif unit == 'w':
            return current_time + num * 7 * 86400
        else:
            return None

class TelegramPollingBot:
    def __init__(self, bot_token, pro_logaut=False):
        self.bot_token = bot_token
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/"
        self.message_handlers = {}
        self.commands = {}
        self.param_commands = {}
        self.payment_handlers = {}
        self.successful_payment_handlers = {}
        self.timers = []
        self.logic_handlers = []
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

    def timer(self, data: List[str], moon: List[int], time: List[str]):
        def decorator(func: Callable):
            self.timers.append((data, moon, time, func))
            return func
        return decorator

    def logic_handler(self, condition: Callable, range: int = None, audit: int = 1):
        def decorator(func: Callable):
            self.logic_handlers.append((condition, func, range, audit))
            return func
        return decorator

    async def check_timers(self):
        while True:
            now = datetime.now()
            for data, moon, time, func in self.timers:
                for t in time:
                    scheduled_time = now.replace(hour=int(t.split(':')[0]), minute=int(t.split(':')[1]), second=0, microsecond=0)
                    if scheduled_time <= now < scheduled_time + timedelta(seconds=60):
                        await func()
            await asyncio.sleep(60)

    async def check_logic_handlers(self):
        while True:
            for condition, func, range_seconds, audit_seconds in self.logic_handlers:
                if await condition():
                    await func()  
                    await asyncio.sleep(range_seconds)
                else:
                    await asyncio.sleep(audit_seconds)

    async def run_polling(self):
        offset = 0
        while True:
            try:
                await asyncio.gather(
                        self.check_timers(),
                        self.check_logic_handlers()
                        )
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
        logger.info(f"Обробляється повідомлення: {text or 'не текстове повідомлення'}")
        if text and text.startswith("/"):
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
            if message.photo and "photo" in self.message_handlers:
                logger.info("Обробляється фото")
                await self.message_handlers["photo"](message)
            elif message.video and "video" in self.message_handlers:
                logger.info("Обробляється відео")
                await self.message_handlers["video"](message)
            elif message.document and "document" in self.message_handlers:
                logger.info("Обробляється документ")
                await self.message_handlers["document"](message)
            elif message.audio and "audio" in self.message_handlers:
                logger.info("Обробляється аудіо")
                await self.message_handlers["audio"](message)
            elif message.voice and "voice" in self.message_handlers:
                logger.info("Обробляється голосове повідомлення")
                await self.message_handlers["voice"](message)
            elif message.contact and "contact" in self.message_handlers:
                logger.info("Обробляється контакт")
                await self.message_handlers["contact"](message)
            elif message.sticker and "sticker" in self.message_handlers:
                logger.info("Обробляється стікер")
                await self.message_handlers["sticker"](message)
            elif message.location and "location" in self.message_handlers:
                logger.info("Обробляється місцезнаходження")
                await self.message_handlers["location"](message)
            elif message.venue and "venue" in self.message_handlers:
                logger.info("Обробляється місце")
                await self.message_handlers["venue"](message)
            elif message.poll and "poll" in self.message_handlers:
                logger.info("Обробляється опитування")
                await self.message_handlers["poll"](message)
            elif message.dice and "dice" in self.message_handlers:
                logger.info("Обробляється кубик")
                await self.message_handlers["dice"](message)
            elif message.web_app_data and "web_app_data" in self.message_handlers:
                logger.info("Обробляються дані веб-додатка")
                await self.message_handlers["web_app_data"](message)
            elif message.game and "game" in self.message_handlers:
                logger.info("Обробляється гра")
                await self.message_handlers["game"](message)
            elif text and "text" in self.message_handlers:
                logger.info("Обробляється текст")
                await self.message_handlers["text"](message)
            else:
                logger.warning("Тип повідомлення не підтримується, обробка невідома.")
                if "unknown" in self.message_handlers:
                    await self.message_handlers["unknown"](message)

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

    def message_photo(self):
        def decorator(func):
            self.message_handlers["photo"] = func
            logger.info("Фото хендлер зареєстровано")
            return func
        return decorator

    def message_video(self):
        def decorator(func):
            self.message_handlers["video"] = func
            logger.info("Відео хендлер зареєстровано")
            return func
        return decorator

    def message_document(self):
        def decorator(func):
            self.message_handlers["document"] = func
            logger.info("Документ хендлер зареєстровано")
            return func
        return decorator

    def message_audio(self):
        def decorator(func):
            self.message_handlers["audio"] = func
            logger.info("Аудіо хендлер зареєстровано")
            return func
        return decorator

    def message_voice(self):
        def decorator(func):
            self.message_handlers["voice"] = func
            logger.info("Голосовий хендлер зареєстровано")
            return func
        return decorator

    def message_contact(self):
        def decorator(func):
            self.message_handlers["contact"] = func
            logger.info("Контакт хендлер зареєстровано")
            return func
        return decorator

    def message_sticker(self):
        def decorator(func):
            self.message_handlers["sticker"] = func
            logger.info("Стікери хендлер зареєстровано")
            return func
        return decorator

    def message_location(self):
        def decorator(func):
            self.message_handlers["location"] = func
            logger.info("Хендлер для місцезнаходження зареєстровано")
            return func
        return decorator

    def message_venue(self):
        def decorator(func):
            self.message_handlers["venue"] = func
            logger.info("Хендлер для місця зареєстровано")
            return func
        return decorator

    def message_poll(self):
        def decorator(func):
            self.message_handlers["poll"] = func
            logger.info("Хендлер для опитувань зареєстровано")
            return func
        return decorator

    def message_dice(self):
        def decorator(func):
            self.message_handlers["dice"] = func
            logger.info("Хендлер для кубиків зареєстровано")
            return func
        return decorator

    def message_web_app_data(self):
        def decorator(func):
            self.message_handlers["web_app_data"] = func
            logger.info("Хендлер для даних веб-додатків зареєстровано")
            return func
        return decorator

    def message_game(self):
        def decorator(func):
            self.message_handlers["game"] = func
            logger.info("Хендлер для ігор зареєстровано")
            return func
        return decorator

    def message_text(self, messages_txt, caps_ignore=False):
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

    def message_unknown(self):
        def decorator(func):
            self.message_handlers["unknown"] = func
            logger.info("Хендлер для невідомих типів повідомлень зареєстровано")
            return func
        return decorator

    async def ban_user(self, chat_id, user_id, until_time=None):
        until_date = self.convert_time(until_time) if until_time else None

        url = f"{self.api_url}banChatMember"
        payload = {
            "chat_id": chat_id,
            "user_id": user_id,
        }
        if until_date:
            payload["until_date"] = until_date

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    logger.info(f"Користувача {user_id} було заблоковано в чаті {chat_id} до {until_date}")
                    return True
                else:
                    logger.error(f"Не вдалося заблокувати користувача {user_id} в чаті {chat_id}: {response.status}")
                    return False


    async def unban_user(self, chat_id, user_id):
        url = f"{self.api_url}unbanChatMember"
        payload = {
            "chat_id": chat_id,
            "user_id": user_id,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    logger.info(f"Користувача {user_id} було розблоковано в чаті {chat_id}")
                    return True
                else:
                    logger.error(f"Не вдалося розблокувати користувача {user_id} в чаті {chat_id}: {response.status}")
                    return False

    async def set_permissions(self, chat_id, user_id, 
                              can_send_messages=True, 
                              can_send_media_messages=True, 
                              can_send_polls=True, 
                              can_change_info=True, 
                              can_invite_users=True, 
                              can_pin_messages=True, 
                              can_manage_chat=False, 
                              can_delete_messages=False, 
                              can_manage_video_chats=False, 
                              can_restrict_members=False, 
                              can_promote_members=False, 
                              until_time=None):
        
        until_date = self.convert_time(until_time) if until_time else None
        
        url = f"{self.api_url}restrictChatMember"
        permissions = {
            "can_send_messages": can_send_messages,
            "can_send_media_messages": can_send_media_messages,
            "can_send_polls": can_send_polls,
            "can_change_info": can_change_info,
            "can_invite_users": can_invite_users,
            "can_pin_messages": can_pin_messages,
            "can_manage_chat": can_manage_chat, 
            "can_delete_messages": can_delete_messages, 
            "can_manage_video_chats": can_manage_video_chats, 
            "can_restrict_members": can_restrict_members, 
            "can_promote_members": can_promote_members,
        }

        payload = {
            "chat_id": chat_id,
            "user_id": user_id,
            "permissions": permissions,
        }
        if until_date:
            payload["until_date"] = until_date

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    logger.info(f"Налаштовано права для користувача {user_id} в чаті {chat_id}")
                    return True
                else:
                    logger.error(f"Не вдалося налаштувати права для користувача {user_id} в чаті {chat_id}: {response.status}")
                    return False

    async def apply_temporary_restrictions(self, chat_id, user_id, 
                                            can_send_messages=False, 
                                            can_send_media_messages=False, 
                                            until_time=None):
        until_date = self.convert_time(until_time) if until_time else None

        url = f"{self.api_url}restrictChatMember"
        permissions = {
            "can_send_messages": can_send_messages,
            "can_send_media_messages": can_send_media_messages,
        }

        payload = {
            "chat_id": chat_id,
            "user_id": user_id,
            "permissions": permissions,
        }
        if until_date:
            payload["until_date"] = until_date  # Додаємо дату, до якої діють обмеження
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    logger.info(f"Тимчасові обмеження накладено на користувача {user_id} в чаті {chat_id} до {until_date}")
                    return True
                else:
                    logger.error(f"Не вдалося накласти обмеження на користувача {user_id} в чаті {chat_id}: {response.status}")
                    return False

    async def set_permissions(self, chat_id, user_id,
                                    can_manage_chat=True,
                                    can_delete_messages=True,
                                    can_manage_video_chats=True,
                                    can_restrict_members=True,
                                    can_promote_members=True,
                                    can_change_info=True,
                                    can_invite_users=True,
                                    can_pin_messages=True,
                                    until_time=None):
        until_date = self.convert_time(until_time) if until_time else None

        url = f"{self.api_url}promoteChatMember"
        payload = {
            "chat_id": chat_id,
            "user_id": user_id,
            "can_manage_chat": can_manage_chat,
            "can_delete_messages": can_delete_messages,
            "can_manage_video_chats": can_manage_video_chats,
            "can_restrict_members": can_restrict_members,
            "can_promote_members": can_promote_members,
            "can_change_info": can_change_info,
            "can_invite_users": can_invite_users,
            "can_pin_messages": can_pin_messages,
        }
        if until_date:
            payload["until_date"] = until_date

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    logger.info(f"Користувач {user_id} отримав права адміністратора в чаті {chat_id} до {until_date}")
                    return True
                else:
                    logger.error(f"Не вдалося призначити адміністратора {user_id} в чаті {chat_id}: {response.status}")
                    return False

class TelegramMessage:
    def __init__(self, message_data):
        # Mandatory fields
        self.chat_id = message_data["chat"]["id"]
        self.message_id = message_data.get("message_id", None)
        self.text = message_data.get("text", "")
        self.from_user = TelegramUser(message_data.get("from", {}))
        
        # Optional fields
        self.message_thread_id = message_data.get("message_thread_id", None)
        self.sender_chat = TelegramChat(message_data.get("sender_chat", {}))
        self.sender_boost_count = message_data.get("sender_boost_count", None)
        self.sender_business_bot = TelegramUser(message_data.get("sender_business_bot", {}))
        self.date = message_data.get("date", None)
        self.business_connection_id = message_data.get("business_connection_id", "")
        self.forward_origin = TelegramMessageOrigin(message_data.get("forward_origin", {}))
        self.is_topic_message = message_data.get("is_topic_message", False)
        self.is_automatic_forward = message_data.get("is_automatic_forward", False)
        self.reply_to_message = TelegramMessage(message_data.get("reply_to_message", {})) if "reply_to_message" in message_data else None
        self.external_reply = ExternalReplyInfo(message_data.get("external_reply", {}))
        self.quote = TextQuote(message_data.get("quote", {}))
        self.reply_to_story = Story(message_data.get("reply_to_story", {}))
        self.via_bot = TelegramUser(message_data.get("via_bot", {}))
        self.edit_date = message_data.get("edit_date", None)
        self.has_protected_content = message_data.get("has_protected_content", False)
        self.is_from_offline = message_data.get("is_from_offline", False)
        self.media_group_id = message_data.get("media_group_id", None)
        self.author_signature = message_data.get("author_signature", None)
        self.entities = [MessageEntity(e) for e in message_data.get("entities", [])]
        self.link_preview_options = LinkPreviewOptions(message_data.get("link_preview_options", {}))
        self.effect_id = message_data.get("effect_id", None)
        
        # Media
        self.photo = [TelegramPhoto(p) for p in message_data.get("photo", [])]
        self.sticker = TelegramSticker(message_data.get("sticker", {})) if "sticker" in message_data else None
        self.animation = TelegramAnimation(message_data.get("animation", {})) if "animation" in message_data else None
        self.audio = TelegramAudio(message_data.get("audio", {})) if "audio" in message_data else None
        self.document = TelegramDocument(message_data.get("document", {})) if "document" in message_data else None
        self.video = TelegramVideo(message_data.get("video", {})) if "video" in message_data else None
        self.video_note = TelegramVideoNote(message_data.get("video_note", {})) if "video_note" in message_data else None
        self.voice = TelegramVoice(message_data.get("voice", {})) if "voice" in message_data else None
        
        # Other content
        self.caption = message_data.get("caption", None)
        self.caption_entities = [MessageEntity(e) for e in message_data.get("caption_entities", [])]
        self.show_caption_above_media = message_data.get("show_caption_above_media", False)
        self.has_media_spoiler = message_data.get("has_media_spoiler", False)
        self.contact = TelegramContact(message_data.get("contact", {})) if "contact" in message_data else None
        self.dice = TelegramDice(message_data.get("dice", {})) if "dice" in message_data else None
        self.game = TelegramGame(message_data.get("game", {})) if "game" in message_data else None
        self.poll = TelegramPoll(message_data.get("poll", {})) if "poll" in message_data else None
        self.venue = TelegramVenue(message_data.get("venue", {})) if "venue" in message_data else None
        self.location = TelegramLocation(message_data.get("location", {})) if "location" in message_data else None
        
        # Chat-related service messages
        self.new_chat_members = [TelegramUser(u) for u in message_data.get("new_chat_members", [])]
        self.left_chat_member = TelegramUser(message_data.get("left_chat_member", {})) if "left_chat_member" in message_data else None
        self.new_chat_title = message_data.get("new_chat_title", None)
        self.new_chat_photo = [TelegramPhoto(p) for p in message_data.get("new_chat_photo", [])]
        self.delete_chat_photo = message_data.get("delete_chat_photo", False)
        self.group_chat_created = message_data.get("group_chat_created", False)
        self.supergroup_chat_created = message_data.get("supergroup_chat_created", False)
        self.channel_chat_created = message_data.get("channel_chat_created", False)
        self.message_auto_delete_timer_changed = MessageAutoDeleteTimerChanged(message_data.get("message_auto_delete_timer_changed", {}))
        self.migrate_to_chat_id = message_data.get("migrate_to_chat_id", None)
        self.migrate_from_chat_id = message_data.get("migrate_from_chat_id", None)
        self.pinned_message = TelegramMessage(message_data.get("pinned_message", {})) if "pinned_message" in message_data else None

        # Payment messages
        self.invoice = TelegramInvoice(message_data.get("invoice", {})) if "invoice" in message_data else None
        self.successful_payment = TelegramSuccessfulPayment(message_data.get("successful_payment", {})) if "successful_payment" in message_data else None
        self.refunded_payment = TelegramRefundedPayment(message_data.get("refunded_payment", {})) if "refunded_payment" in message_data else None
        
        # Special service messages
        self.users_shared = UsersShared(message_data.get("users_shared", {})) if "users_shared" in message_data else None
        self.chat_shared = ChatShared(message_data.get("chat_shared", {})) if "chat_shared" in message_data else None
        self.connected_website = message_data.get("connected_website", None)
        self.write_access_allowed = WriteAccessAllowed(message_data.get("write_access_allowed", {})) if "write_access_allowed" in message_data else None
        self.passport_data = TelegramPassportData(message_data.get("passport_data", {})) if "passport_data" in message_data else None
        self.proximity_alert_triggered = ProximityAlertTriggered(message_data.get("proximity_alert_triggered", {}))
        self.boost_added = ChatBoostAdded(message_data.get("boost_added", {})) if "boost_added" in message_data else None
        self.chat_background_set = ChatBackground(message_data.get("chat_background_set", {})) if "chat_background_set" in message_data else None
        
        # Forum topics
        self.forum_topic_created = ForumTopicCreated(message_data.get("forum_topic_created", {})) if "forum_topic_created" in message_data else None
        self.forum_topic_edited = ForumTopicEdited(message_data.get("forum_topic_edited", {})) if "forum_topic_edited" in message_data else None
        self.forum_topic_closed = ForumTopicClosed(message_data.get("forum_topic_closed", {})) if "forum_topic_closed" in message_data else None
        self.forum_topic_reopened = ForumTopicReopened(message_data.get("forum_topic_reopened", {})) if "forum_topic_reopened" in message_data else None
        self.general_forum_topic_hidden = GeneralForumTopicHidden(message_data.get("general_forum_topic_hidden", {})) if "general_forum_topic_hidden" in message_data else None
        self.general_forum_topic_unhidden = GeneralForumTopicUnhidden(message_data.get("general_forum_topic_unhidden", {})) if "general_forum_topic_unhidden" in message_data else None

        # Giveaways
        self.giveaway_created = GiveawayCreated(message_data.get("giveaway_created", {})) if "giveaway_created" in message_data else None
        self.giveaway = Giveaway(message_data.get("giveaway", {})) if "giveaway" in message_data else None
        self.giveaway_winners = GiveawayWinners(message_data.get("giveaway_winners", {})) if "giveaway_winners" in message_data else None
        self.giveaway_completed = GiveawayCompleted(message_data.get("giveaway_completed", {})) if "giveaway_completed" in message_data else None
        
        # Video chats
        self.video_chat_scheduled = VideoChatScheduled(message_data.get("video_chat_scheduled", {})) if "video_chat_scheduled" in message_data else None
        self.video_chat_started = VideoChatStarted(message_data.get("video_chat_started", {})) if "video_chat_started" in message_data else None
        self.video_chat_ended = VideoChatEnded(message_data.get("video_chat_ended", {})) if "video_chat_ended" in message_data else None
        self.video_chat_participants_invited = VideoChatParticipantsInvited(message_data.get("video_chat_participants_invited", {})) if "video_chat_participants_invited" in message_data else None
        
        # Web App data
        self.web_app_data = WebAppData(message_data.get("web_app_data", {})) if "web_app_data" in message_data else None
        
        # Request data
        self.request = TelegramRequest(message_data.get("request", {})) if "request" in message_data else None

class TelegramMessageOrigin:
    def __init__(self, origin_data):
        self.message_id = origin_data.get("message_id", None)
        self.forward_from_user = TelegramUser(origin_data.get("forward_from", {})) if "forward_from" in origin_data else None
        self.forward_from_chat = TelegramChat(origin_data.get("forward_from_chat", {})) if "forward_from_chat" in origin_data else None
        self.forward_from_message_id = origin_data.get("forward_from_message_id", None)
        self.forward_signature = origin_data.get("forward_signature", None)
        self.forward_sender_name = origin_data.get("forward_sender_name", None)
        self.forward_date = origin_data.get("forward_date", None)

class MessageEntity:
    def __init__(self, entity_data):
        self.type = entity_data.get("type", None)
        self.offset = entity_data.get("offset", 0)
        self.length = entity_data.get("length", 0)
        self.url = entity_data.get("url", None)
        self.user = TelegramUser(entity_data.get("user", {})) if "user" in entity_data else None
        self.language = entity_data.get("language", None)
        self.custom_emoji_id = entity_data.get("custom_emoji_id", None)

class TelegramChat:
    def __init__(self, chat_data):
        self.id = chat_data.get("id", None)
        self.type = chat_data.get("type", None)
        self.title = chat_data.get("title", None)
        self.username = chat_data.get("username", None)
        self.first_name = chat_data.get("first_name", None)
        self.last_name = chat_data.get("last_name", None)
        self.is_forum = chat_data.get("is_forum", False)
        self.photo = TelegramChatPhoto(chat_data.get("photo", {})) if "photo" in chat_data else None
        self.bio = chat_data.get("bio", None)
        self.has_private_forwards = chat_data.get("has_private_forwards", False)
        self.has_restricted_voice_and_video_messages = chat_data.get("has_restricted_voice_and_video_messages", False)
        self.join_to_send_messages = chat_data.get("join_to_send_messages", False)
        self.join_by_request = chat_data.get("join_by_request", False)
        self.description = chat_data.get("description", None)
        self.invite_link = chat_data.get("invite_link", None)
        self.pinned_message = TelegramMessage(chat_data.get("pinned_message", {})) if "pinned_message" in chat_data else None
        self.permissions = TelegramChatPermissions(chat_data.get("permissions", {})) if "permissions" in chat_data else None
        self.slow_mode_delay = chat_data.get("slow_mode_delay", None)
        self.message_auto_delete_time = chat_data.get("message_auto_delete_time", None)
        self.has_aggressive_anti_spam_enabled = chat_data.get("has_aggressive_anti_spam_enabled", False)
        self.has_hidden_members = chat_data.get("has_hidden_members", False)
        self.has_protected_content = chat_data.get("has_protected_content", False)

class TelegramChat:
    def __init__(self, chat_data):
        self.id = chat_data.get("id", None)
        self.type = chat_data.get("type", None)
        self.title = chat_data.get("title", None)
        self.username = chat_data.get("username", None)
        self.first_name = chat_data.get("first_name", None)
        self.last_name = chat_data.get("last_name", None)
        self.is_forum = chat_data.get("is_forum", False)
        self.photo = TelegramChatPhoto(chat_data.get("photo", {})) if "photo" in chat_data else None
        self.bio = chat_data.get("bio", None)
        self.has_private_forwards = chat_data.get("has_private_forwards", False)
        self.has_restricted_voice_and_video_messages = chat_data.get("has_restricted_voice_and_video_messages", False)
        self.join_to_send_messages = chat_data.get("join_to_send_messages", False)
        self.join_by_request = chat_data.get("join_by_request", False)
        self.description = chat_data.get("description", None)
        self.invite_link = chat_data.get("invite_link", None)
        self.pinned_message = TelegramMessage(chat_data.get("pinned_message", {})) if "pinned_message" in chat_data else None
        self.permissions = TelegramChatPermissions(chat_data.get("permissions", {})) if "permissions" in chat_data else None
        self.slow_mode_delay = chat_data.get("slow_mode_delay", None)
        self.message_auto_delete_time = chat_data.get("message_auto_delete_time", None)
        self.has_aggressive_anti_spam_enabled = chat_data.get("has_aggressive_anti_spam_enabled", False)
        self.has_hidden_members = chat_data.get("has_hidden_members", False)
        self.has_protected_content = chat_data.get("has_protected_content", False)

class TelegramChatPhoto:
    def __init__(self, photo_data):
        self.small_file_id = photo_data.get("small_file_id", None)
        self.small_file_unique_id = photo_data.get("small_file_unique_id", None)
        self.big_file_id = photo_data.get("big_file_id", None)
        self.big_file_unique_id = photo_data.get("big_file_unique_id", None)

class TelegramUser:
    def __init__(self, user_data):
        self.id = user_data.get("id", None)
        self.is_bot = user_data.get("is_bot", False)
        self.first_name = user_data.get("first_name", "")
        self.last_name = user_data.get("last_name", None)
        self.username = user_data.get("username", None)
        self.language_code = user_data.get("language_code", None)
        self.is_premium = user_data.get("is_premium", False)
        self.added_to_attachment_menu = user_data.get("added_to_attachment_menu", False)
        self.can_join_groups = user_data.get("can_join_groups", True)
        self.can_read_all_group_messages = user_data.get("can_read_all_group_messages", False)
        self.supports_inline_queries = user_data.get("supports_inline_queries", False)

        self.all_name = f"{self.first_name} {self.last_name}".strip()

class TelegramVoice:
    def __init__(self, voice_data):
        self.file_id = voice_data["file_id"]
        self.file_unique_id = voice_data["file_unique_id"]
        self.duration = voice_data["duration"]
        self.mime_type = voice_data.get("mime_type")
        self.file_size = voice_data.get("file_size")

class TelegramAudio:
    def __init__(self, audio_data):
        self.file_id = audio_data.get("file_id", None)
        self.file_unique_id = audio_data.get("file_unique_id", None)
        self.duration = audio_data.get("duration", None)
        self.performer = audio_data.get("performer", None)
        self.title = audio_data.get("title", None)
        self.mime_type = audio_data.get("mime_type", None)
        self.file_size = audio_data.get("file_size", None)
        self.thumb = TelegramPhoto(audio_data.get("thumb", {})) if "thumb" in audio_data else None

class TelegramDocument:
    def __init__(self, document_data):
        self.file_id = document_data.get("file_id", None)
        self.file_unique_id = document_data.get("file_unique_id", None)
        self.thumb = TelegramPhoto(document_data.get("thumb", {})) if "thumb" in document_data else None
        self.file_name = document_data.get("file_name", None)
        self.mime_type = document_data.get("mime_type", None)
        self.file_size = document_data.get("file_size", None)

class TelegramVideo:
    def __init__(self, video_data):
        self.file_id = video_data["file_id"]
        self.file_unique_id = video_data["file_unique_id"]
        self.width = video_data["width"]
        self.height = video_data["height"]
        self.duration = video_data["duration"]
        self.mime_type = video_data.get("mime_type")
        self.file_size = video_data.get("file_size")

class TelegramAnimation:
    def __init__(self, animation_data):
        self.file_id = animation_data.get("file_id", None)
        self.file_unique_id = animation_data.get("file_unique_id", None)
        self.width = animation_data.get("width", None)
        self.height = animation_data.get("height", None)
        self.duration = animation_data.get("duration", None)
        self.thumb = TelegramPhoto(animation_data.get("thumb", {})) if "thumb" in animation_data else None
        self.file_name = animation_data.get("file_name", None)
        self.mime_type = animation_data.get("mime_type", None)
        self.file_size = animation_data.get("file_size", None)

class TelegramPhoto:
    def __init__(self, photo_data):
        self.file_id = photo_data.get("file_id", None)
        self.file_unique_id = photo_data.get("file_unique_id", None)
        self.width = photo_data.get("width", None)
        self.height = photo_data.get("height", None)
        self.file_size = photo_data.get("file_size", None)

class TelegramSticker:
    def __init__(self, sticker_data):
        self.file_id = sticker_data.get("file_id", None)
        self.file_unique_id = sticker_data.get("file_unique_id", None)
        self.width = sticker_data.get("width", None)
        self.height = sticker_data.get("height", None)
        self.is_animated = sticker_data.get("is_animated", False)
        self.is_video = sticker_data.get("is_video", False)
        self.thumb = TelegramPhoto(sticker_data.get("thumb", {})) if "thumb" in sticker_data else None
        self.emoji = sticker_data.get("emoji", None)
        self.set_name = sticker_data.get("set_name", None)
        self.mask_position = sticker_data.get("mask_position", None)
        self.file_size = sticker_data.get("file_size", None)

class TelegramLocation:
    def __init__(self, location_data):
        self.longitude = location_data.get("longitude", None)
        self.latitude = location_data.get("latitude", None)
        self.horizontal_accuracy = location_data.get("horizontal_accuracy", None)
        self.live_period = location_data.get("live_period", None)
        self.heading = location_data.get("heading", None)
        self.proximity_alert_radius = location_data.get("proximity_alert_radius", None)

class TelegramMaskPosition:
    def __init__(self, mask_data):
        self.point = mask_data.get("point", None)
        self.x_shift = mask_data.get("x_shift", 0.0)
        self.y_shift = mask_data.get("y_shift", 0.0)
        self.scale = mask_data.get("scale", 1.0)

class TelegramContact:
    def __init__(self, contact_data):
        self.phone_number = contact_data.get("phone_number", None)
        self.first_name = contact_data.get("first_name", None)
        self.last_name = contact_data.get("last_name", None)
        self.user_id = contact_data.get("user_id", None)
        self.vcard = contact_data.get("vcard", None)  # Візитна картка (якщо є)

class TelegramPoll:
    def __init__(self, poll_data):
        self.id = poll_data.get("id", None)
        self.question = poll_data.get("question", None)
        self.options = [TelegramPollOption(option) for option in poll_data.get("options", [])]
        self.is_closed = poll_data.get("is_closed", False)

class TelegramPollOption:
    def __init__(self, option_data):
        self.text = option_data.get("text", None)
        self.voter_count = option_data.get("voter_count", 0)

class TelegramGame:
    def __init__(self, game_data):
        self.title = game_data.get("title", None)
        self.description = game_data.get("description", None)
        self.photo = [TelegramPhoto(photo) for photo in game_data.get("photo", [])]
        self.text = game_data.get("text", None)
        self.text_entities = [TelegramMessageEntity(entity) for entity in game_data.get("text_entities", [])]
        self.animation = TelegramAnimation(game_data.get("animation", {})) if "animation" in game_data else None

class TelegramVenue:
    def __init__(self, venue_data):
        self.location = TelegramLocation(venue_data.get("location", {}))
        self.title = venue_data.get("title", None)
        self.address = venue_data.get("address", None)
        self.foursquare_id = venue_data.get("foursquare_id", None)
        self.foursquare_type = venue_data.get("foursquare_type", None)

class WebAppData:
    def __init__(self, web_app_data):
        self.data = web_app_data.get("data", None)
        self.button_text = web_app_data.get("button_text", None)

class TelegramPAY:
    def __init__(self, pay_data):
        self.id = pay_data["id"]
        self.currency = pay_data["currency"]
        self.total_amount = pay_data["total_amount"]
        self.payment_method = pay_data.get("payment_method", "unknown")

class TelegramSuccessfulPayment:
    def __init__(self, payment_data):
        self.chat_id = payment_data.get("chat", {}).get("id", None)
        self.currency = payment_data.get("currency", None)
        self.total_amount = payment_data.get("total_amount", None)
        self.invoice_payload = payment_data.get("invoice_payload", None)
        self.shipping_option_id = payment_data.get("shipping_option_id", None)
        self.order_info = payment_data.get("order_info", None)
        self.telegram_payment_charge_id = payment_data.get("telegram_payment_charge_id", None)
        self.provider_payment_charge_id = payment_data.get("provider_payment_charge_id", None)

class TelegramRefundedPayment:
    def __init__(self, refunded_data):
        self.payment_id = refunded_data.get("payment_id", None)
        self.amount = refunded_data.get("amount", None)
        self.currency = refunded_data.get("currency", None)
        self.reason = refunded_data.get("reason", None)

class UsersShared:
    def __init__(self, shared_data):
        self.user_ids = shared_data.get("user_ids", [])

class ChatShared:
    def __init__(self, chat_data):
        self.chat_id = chat_data.get("chat_id", None)
        self.shared_by_user = chat_data.get("shared_by_user", None)

class WriteAccessAllowed:
    def __init__(self, access_data):
        self.is_allowed = access_data.get("is_allowed", False)

class TelegramPassportData:
    def __init__(self, passport_data):
        self.data = passport_data.get("data", None)
        self.credentials = passport_data.get("credentials", None)

class ProximityAlertTriggered:
    def __init__(self, alert_data):
        self.traveler = TelegramUser(alert_data.get("traveler", {}))
        self.watcher = TelegramUser(alert_data.get("watcher", {}))
        self.distance = alert_data.get("distance", None)

class ChatBoostAdded:
    def __init__(self, boost_data):
        self.boosted_by = TelegramUser(boost_data.get("boosted_by", {}))
        self.boost_level = boost_data.get("boost_level", None)

class ChatBackground:
    def __init__(self, background_data):
        self.image = background_data.get("image", None)
        self.color = background_data.get("color", None)

class ForumTopicCreated:
    def __init__(self, topic_data):
        self.title = topic_data.get("title", None)
        self.creator = TelegramUser(topic_data.get("creator", {}))

class ForumTopicEdited:
    def __init__(self, topic_data):
        self.title = topic_data.get("title", None)
        self.edited_by = TelegramUser(topic_data.get("edited_by", {}))

class ForumTopicClosed:
    def __init__(self, topic_data):
        self.closed_by = TelegramUser(topic_data.get("closed_by", {}))

class ForumTopicReopened:
    def __init__(self, topic_data):
        self.reopened_by = TelegramUser(topic_data.get("reopened_by", {}))

class GeneralForumTopicHidden:
    def __init__(self, topic_data):
        self.hidden_by = TelegramUser(topic_data.get("hidden_by", {}))

class GeneralForumTopicUnhidden:
    def __init__(self, topic_data):
        self.unhidden_by = TelegramUser(topic_data.get("unhidden_by", {}))

class GiveawayCreated:
    def __init__(self, giveaway_data):
        self.title = giveaway_data.get("title", None)
        self.created_by = TelegramUser(giveaway_data.get("created_by", {}))

class Giveaway:
    def __init__(self, giveaway_data):
        self.title = giveaway_data.get("title", None)
        self.description = giveaway_data.get("description", None)

class GiveawayWinners:
    def __init__(self, winners_data):
        self.winner_ids = winners_data.get("winner_ids", [])

class GiveawayCompleted:
    def __init__(self, giveaway_data):
        self.completed_by = TelegramUser(giveaway_data.get("completed_by", {}))

class VideoChatScheduled:
    def __init__(self, chat_data):
        self.start_time = chat_data.get("start_time", None)
        self.scheduled_by = TelegramUser(chat_data.get("scheduled_by", {}))

class VideoChatStarted:
    def __init__(self, chat_data):
        self.started_by = TelegramUser(chat_data.get("started_by", {}))

class VideoChatEnded:
    def __init__(self, chat_data):
        self.ended_by = TelegramUser(chat_data.get("ended_by", {}))
        self.duration = chat_data.get("duration", None)

class VideoChatParticipantsInvited:
    def __init__(self, chat_data):
        self.invitees = [TelegramUser(user) for user in chat_data.get("invitees", [])]

class TelegramRequest:
    def __init__(self, request_data):
        self.request_id = request_data.get("request_id", None)
        self.user = TelegramUser(request_data.get("user", {}))
        self.data = request_data.get("data", None)
