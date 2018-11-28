import argparse
import json
import logging
import pathlib


class Configuration:
    def __init__(self, _telegram_bot_token, _proxy_params):
        self.telegram_bot_token: str = _telegram_bot_token
        self.proxy_params = _proxy_params

    @classmethod
    def load(cls):
        args = cls._get_command_line_arguments()
        json_config = cls._get_configuration_file_content(args.configuration_file)

        def maybe_get_value(option_name: str):
            value = getattr(args, option_name)
            return value if value else json_config.get(option_name, None)

        return cls(maybe_get_value('telegram_bot_token'),
                   cls.make_proxy_parameters(maybe_get_value('proxy_url'),
                                             maybe_get_value('proxy_user'),
                                             maybe_get_value('proxy_password')))

    @staticmethod
    def _get_command_line_arguments() -> argparse.Namespace:
        parser = argparse.ArgumentParser(description='Telegram bot.')
        parser.add_argument('--configuration-file', '-c', type=str, default='configuration.json',
                            dest='configuration_file',
                            help='Json-formatted file with all configuration parameters.')
        parser.add_argument('--telegram-bot-token', '-t', type=str, dest='telegram_bot_token',
                            help='Telegram bot token, received from @BotFather.')
        parser.add_argument('--proxy-url', '-p', type=str, dest='proxy_url', help='Socks5 proxy server URL.')
        parser.add_argument('--proxy-user', '-pu', type=str, dest='proxy_user', help='Username for the proxy server.')
        parser.add_argument('--proxy-password', '-pp', type=str, dest='proxy_password',
                            help='Password for the proxy server.')
        return parser.parse_args()

    @staticmethod
    def make_proxy_parameters(proxy_url, proxy_user, proxy_password):
        if not proxy_url:
            return None
        params = {'proxy_url': proxy_url}
        if proxy_user or proxy_password:
            params['urllib3_proxy_kwargs'] = {}
            if proxy_user:
                params['urllib3_proxy_kwargs']['username'] = proxy_user
            if proxy_password:
                params['urllib3_proxy_kwargs']['password'] = proxy_password
        return params

    @staticmethod
    def _get_configuration_file_content(configuration_file_path: str) -> dict:
        file_location_path = pathlib.Path(configuration_file_path)
        if file_location_path.is_file():
            with file_location_path.open() as configuration_file:
                return json.load(configuration_file)
        logging.info('Configuration file is missing, using only command line parameters.')
        return {}
