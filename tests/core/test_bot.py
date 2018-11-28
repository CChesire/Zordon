from unittest.mock import MagicMock, patch

import app.core.bot
from tests.base import BaseTestCase


class TestLaunch(BaseTestCase):
    @patch('app.core.bot.Updater', new=MagicMock())
    def test_polling(self):
        zordon_bot = app.core.bot.Bot()
        zordon_bot.run()

        zordon_bot.updater.start_polling.assert_called_once_with()
        # zordon_bot.updater.dispatcher.add_handler.assert_called_with(MatcherAny())
        self.assertFalse(zordon_bot.updater.start_webhook.called)
