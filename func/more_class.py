class TelegramMessage:
    def __init__(self, message_data):
        self.message_id = message_data.get("message_id")
        self.text = message_data.get("text")
        self.chat_id = message_data["chat"]["id"]
        self.from_user = TelegramUser(message_data["from"])

class TelegramUser:
    def __init__(self, user_data):
        self.id = user_data.get("id")
        self.first_name = user_data.get("first_name")
        self.last_name = user_data.get("last_name")
        self.username = user_data.get("username")

    @property
    def all_name(self):
        return f"{self.first_name} {self.last_name}".strip()
#
