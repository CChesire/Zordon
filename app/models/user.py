from telegram import Bot, TelegramError

from app.definitions import commands_by_level, commands_set, superuser_login
from app.models.base import UserBase as _Base, DefferedUser as _Deffered


class User(_Base):
    def has_right_to(self, command: str):
        assert command in commands_set
        if self.is_superuser():
            return True
        for level in range(0, self.rights_level + 1):
            if command in commands_by_level[level]:
                return True
        return False

    def is_superuser(self):
        return self.telegram_login == superuser_login

    def send_message(self, bot: Bot, *args, **kwargs):
        try:
            bot.send_message(self.telegram_user_id, *args, **kwargs)
        except TelegramError:
            User.send_message_to_superuser(bot, text='{0} disabled chat'.format(self.telegram_login))
            self.is_disabled_chat = True
            self.save()

    @staticmethod
    def send_message_to_superuser(bot: Bot, *args, **kwargs):
        try:
            superuser = User.get(User.telegram_login == superuser_login)
        except User.DoesNotExist:
            return

        superuser.send_message(bot, *args, **kwargs)


_Deffered.set_model(User)