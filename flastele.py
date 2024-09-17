import requests


def send_invoice(user_id, title, description, payload, currency, prices, provider_token=None, photo_url=None, photo_size=None, photo_width=None, photo_height=None):
    url = f"https://api.telegram.org/bot{bot_token}/sendInvoice"
    
    Prices = [{"label": prices[0], "amount": prices[1]}]

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
                [{"text": f"⭐Pay {prices[1]}", "pay": True}]
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

    response = requests.post(url, json=payload_data)
    return response.status_code == 200

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


def send_message(user_id, message_text, parse_mode=None, callback=None, reply_keyboard=None):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    reply_markup = keyboard_create(callback, reply_keyboard)
    payload = {
        "chat_id": user_id,
        "text": message_text,
        "parse_mode": parse_mode
    }
    
    if reply_markup:
        payload["reply_markup"] = reply_markup
    
    response = requests.post(url, json=payload)
    return response.status_code == 200


def send_photo(user_id, photo_path, caption=None, parse_mode=None):
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    reply_markup = keyboard_create(callback, reply_keyboard)
    payload = {
        "chat_id": user_id,
        "caption": caption,
        "parse_mode": parse_mode
    }
    
    if reply_markup:
        payload["reply_markup"] = reply_markup
    
    with open(photo_path, 'rb') as photo:
        files = {'photo': photo}
        response = requests.post(url, data=payload, files=files)
        
    return response.status_code == 200


def send_document(user_id, document_path, caption=None, parse_mode=None):
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    reply_markup = keyboard_create(callback, reply_keyboard)
    payload = {
        "chat_id": user_id,
        "caption": caption,
        "parse_mode": parse_mode
    }
    
    if reply_markup:
        payload["reply_markup"] = reply_markup
    
    with open(document_path, 'rb') as document:
        files = {'document': document}
        response = requests.post(url, data=payload, files=files)
        
    return response.status_code == 200


def send_audio(user_id, audio_path, caption=None, parse_mode=None):
    url = f"https://api.telegram.org/bot{bot_token}/sendAudio"
    reply_markup = keyboard_create(callback, reply_keyboard)
    payload = {
        "chat_id": user_id,
        "caption": caption,
        "parse_mode": parse_mode
    }
    
    if reply_markup:
        payload["reply_markup"] = reply_markup
    
    with open(audio_path, 'rb') as audio:
        files = {'audio': audio}
        response = requests.post(url, data=payload, files=files)
        
    return response.status_code == 200


def send_video(user_id, video_path, caption=None, parse_mode=None):
    url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
    reply_markup = keyboard_create(callback, reply_keyboard)
    payload = {
        "chat_id": user_id,
        "caption": caption,
        "parse_mode": parse_mode
    }
    
    if reply_markup:
        payload["reply_markup"] = reply_markup
    
    with open(video_path, 'rb') as video:
        files = {'video': video}
        response = requests.post(url, data=payload, files=files)
        
    return response.status_code == 200
