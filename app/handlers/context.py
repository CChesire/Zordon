from telegram import Bot, Chat, Message, Update


class Context:
    def __init__(self, update: Update, bot: Bot):
        self.update = update
        self.bot = bot

    def send_response_message(self, text, **kwargs) -> Message:
        return self.update.effective_chat.send_message(text, **kwargs)
