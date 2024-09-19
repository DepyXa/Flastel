import logging
import aiohttp
import json
from types import SimpleNamespace

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
            "resize_keyboard": True,  # Додаємо опцію для автоматичного підстроювання розміру
            "one_time_keyboard": True  # Клавіатура сховається після вибору
        }

    return reply_markup

async def set_webhook(host, bot_token):
    url = f"https://api.telegram.org/bot{token}/setWebhook"
    webhook_url = f"{host}/{token}"

    payload = {
        "url": webhook_url
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("ok"):
                        logging.info("Webhook set successfully.")
                        return data
                    else:
                        logging.error(f"Error: {data.get('description')}")
                        return None
                else:
                    logging.error(f"Error: Received status code {response.status}")
                    return None
    except Exception as e:
        logging.error(f"Exception occurred: {str(e)}")
        return None

async def send_message(user_id, message_text, parse_mode=None, callback=None, reply_keyboard=None):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    reply_markup = keyboard_create(callback, reply_keyboard)
    payload = {
        "chat_id": user_id,
        "text": message_text,
        "parse_mode": parse_mode
    }
    
    if reply_markup:
        payload["reply_markup"] = reply_markup
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    message = json.loads(json.dumps(data.get("result", {})), object_hook=lambda d: SimpleNamespace(**d))
                    return message
                else:
                    logging.error(f"Error: Received status code {response.status}")
                    return None
    except Exception as e:
        logging.error(f"Exception occurred: {str(e)}")
        return None

async def send_photo(user_id, photo_path, caption=None, parse_mode=None, callback=None, reply_keyboard=None):
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    
    reply_markup = keyboard_create(callback, reply_keyboard)
    payload = {
        "chat_id": user_id,
        "caption": caption,
        "parse_mode": parse_mode
    }

    if reply_markup:
        payload["reply_markup"] = reply_markup

    try:
        async with aiohttp.ClientSession() as session:
            with open(photo_path, 'rb') as photo:
                form_data = aiohttp.FormData()
                form_data.add_field('photo', photo, filename=photo_path)
                form_data.add_field('chat_id', str(user_id))
                if caption:
                    form_data.add_field('caption', caption)
                if parse_mode:
                    form_data.add_field('parse_mode', parse_mode)

                async with session.post(url, data=form_data) as response:
                    if response.status == 200:
                        data = await response.json()
                        message = json.loads(json.dumps(data.get("result", {})), object_hook=lambda d: SimpleNamespace(**d))
                        return message
                    else:
                        logging.error(f"Error: Received status code {response.status}")
                        return None
    except Exception as e:
        logging.error(f"Exception occurred: {str(e)}")
        return None


async def send_document(user_id, document_path, caption=None, parse_mode=None, callback=None, reply_keyboard=None):
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    
    reply_markup = keyboard_create(callback, reply_keyboard)
    payload = {
        "chat_id": user_id,
        "caption": caption,
        "parse_mode": parse_mode
    }

    if reply_markup:
        payload["reply_markup"] = reply_markup

    try:
        async with aiohttp.ClientSession() as session:
            with open(document_path, 'rb') as document:
                form_data = aiohttp.FormData()
                form_data.add_field('document', document, filename=document_path)
                form_data.add_field('chat_id', str(user_id))
                if caption:
                    form_data.add_field('caption', caption)
                if parse_mode:
                    form_data.add_field('parse_mode', parse_mode)

                async with session.post(url, data=form_data) as response:
                    if response.status == 200:
                        data = await response.json()
                        message = json.loads(json.dumps(data.get("result", {})), object_hook=lambda d: SimpleNamespace(**d))
                        return message
                    else:
                        logging.error(f"Error: Received status code {response.status}")
                        return None
    except Exception as e:
        logging.error(f"Exception occurred: {str(e)}")
        return None


async def send_audio(user_id, audio_path, caption=None, parse_mode=None, callback=None, reply_keyboard=None):
    url = f"https://api.telegram.org/bot{bot_token}/sendAudio"
    
    reply_markup = keyboard_create(callback, reply_keyboard)
    payload = {
        "chat_id": user_id,
        "caption": caption,
        "parse_mode": parse_mode
    }

    if reply_markup:
        payload["reply_markup"] = reply_markup

    try:
        async with aiohttp.ClientSession() as session:
            # Асинхронне відкриття та відправка аудіо файлу
            with open(audio_path, 'rb') as audio:
                form_data = aiohttp.FormData()
                form_data.add_field('audio', audio, filename=audio_path)
                form_data.add_field('chat_id', str(user_id))
                if caption:
                    form_data.add_field('caption', caption)
                if parse_mode:
                    form_data.add_field('parse_mode', parse_mode)

                # Відправка запиту
                async with session.post(url, data=form_data) as response:
                    if response.status == 200:
                        data = await response.json()
                        message = json.loads(json.dumps(data.get("result", {})), object_hook=lambda d: SimpleNamespace(**d))
                        return message
                    else:
                        logging.error(f"Error: Received status code {response.status}")
                        return None
    except Exception as e:
        logging.error(f"Exception occurred: {str(e)}")
        return None


async def send_video(user_id, video_path, caption=None, parse_mode=None, callback=None, reply_keyboard=None):
    url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
    
    reply_markup = keyboard_create(callback, reply_keyboard)
    payload = {
        "chat_id": user_id,
        "caption": caption,
        "parse_mode": parse_mode
    }

    if reply_markup:
        payload["reply_markup"] = reply_markup

    try:
        async with aiohttp.ClientSession() as session:
            # Асинхронне відкриття та відправка відео файлу
            with open(video_path, 'rb') as video:
                form_data = aiohttp.FormData()
                form_data.add_field('video', video, filename=video_path)
                form_data.add_field('chat_id', str(user_id))
                if caption:
                    form_data.add_field('caption', caption)
                if parse_mode:
                    form_data.add_field('parse_mode', parse_mode)

                # Відправка запиту
                async with session.post(url, data=form_data) as response:
                    if response.status == 200:
                        data = await response.json()
                        message = json.loads(json.dumps(data.get("result", {})), object_hook=lambda d: SimpleNamespace(**d))
                        return message
                    else:
                        logging.error(f"Error: Received status code {response.status}")
                        return None
    except Exception as e:
        logging.error(f"Exception occurred: {str(e)}")
        return None

async def send_invoice(user_id, title, description, payload, currency, prices, provider_token=None, photo_url=None, photo_size=None, photo_width=None, photo_height=None):
    url = f"https://api.telegram.org/bot{bot_token}/sendInvoice"
    
    description_original = description + " For support FlasTele."
    description = description_original
    
    Prices = [{"label": prices[0], "amount": prices[1]}]
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
#
