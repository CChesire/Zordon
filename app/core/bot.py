from telegram.ext import Updater
import logging

from app.core.configuration import Configuration
from app.core.info import APP_DIR
from app.handlers.dispatcher import Dispatcher


class Bot:
    def __init__(self):
        self.updater: Updater = None
        self.configuration: Configuration = None

    def run(self):
        self._set_up()
        logging.info('Launching bot: ' + str(self.updater.bot.get_me()))
        self._start_updater()
        # This call will lock execution until worker threads are stopped with SIGINT(2), SIGTERM(15) or SIGABRT(6).
        self.updater.idle()

    def _start_updater(self):
        logging.info('Polling mode.')
        self.updater.start_polling()

    def _set_up(self):
        logging.basicConfig(format='%(asctime)s:%(name)s:%(levelname)s - %(message)s', level=logging.INFO)
        self.configuration = Configuration.load()
        self.updater = Updater(token=self.configuration.telegram_bot_token,
                               request_kwargs=self.configuration.proxy_params)
        self.dispatcher = Dispatcher(self.updater)
