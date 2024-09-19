from func import polling_func
from func import webhook_func

class TelegramBot:
    def __init__(self, bot_token):
        self.bot_token = bot_token
     
    async def set_webhook(host, bot_token):
      await func.set_webhook(host, bot_token):
  
    async def send_message(user_id, message_text, parse_mode=None, callback=None, reply_keyboard=None):
      await func.send_message(user_id, message_text, parse_mode, callback, reply_keyboard)
    
    async def send_photo(user_id, photo_path, caption=None, parse_mode=None, callback=None, reply_keyboard=None):
      await func.send_photo(user_id, photo_path, caption, parse_mode, callback, reply_keyboard):
    
    async def send_document(user_id, document_path, caption=None, parse_mode=None, callback=None, reply_keyboard=None):
      await func.send_document(user_id, document_path, caption, parse_mode, callback, reply_keyboard):
    
    async def send_audio(user_id, audio_path, caption=None, parse_mode=None, callback=None, reply_keyboard=None):
      await func.send_audio(user_id, audio_path, caption, parse_mode, callback, reply_keyboard):
    
    async def send_video(user_id, video_path, caption=None, parse_mode=None, callback=None, reply_keyboard=None):
      await func.send_video(user_id, video_path, caption, parse_mode, callback, reply_keyboard):
    
    async def send_invoice(user_id, title, description, payload, currency, prices, provider_token=None, photo_url=None, photo_size=None, photo_width=None, photo_height=None):
      await func.send_invoice(user_id, title, description, payload, currency, prices, provider_token, photo_url, photo_size, photo_width, photo_height):
  
  #
