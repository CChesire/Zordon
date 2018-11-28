from telegram import Bot, Update
from telegram.ext import CommandHandler, Updater
import functools

from app.handlers.chat_type import ChatType
from app.handlers.context import Context

from app.handlers.impl import basic


class Dispatcher:
    def __init__(self, updater: Updater):
        self._bind_all(updater)

    def _handler(self, chat_filters: list, handler_function, bot: Bot, update: Update):
        if update.effective_user and update.effective_user.is_bot:
            return
        if not ChatType.is_valid(chat_filters, update):
            return
        with Context(update, bot) as context:
            if handler_function:
                handler_function(context)

    def _make_handler(self, chat_filters: list, raw_callable):
        return functools.partial(Dispatcher._handler, self, chat_filters, raw_callable)

    def _bind_all(self, updater: Updater):
        handlers = [
            CommandHandler(['start', 'help'],
                           self._make_handler([ChatType.PRIVATE, ChatType.GROUP], basic.on_help_or_start)),
        ]

        for handler in handlers:
            updater.dispatcher.add_handler(handler)
