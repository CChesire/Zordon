from telegram import Update, Bot, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from ..models import User


commands_map = {
    # User-related commands
    'start': 'start',
    'status': 'status',
    'activate': 'ready',
    'deactivate': 'do_not_disturb',
    'cancel': 'cancel',

    # Commands with activities
    'activity_list': 'list_activities',
    'activity_add': 'add_activity',
    'activity_rem': 'remove_activity',
    'subscribe': 'subscribe',
    'unsubscribe': 'unsubscribe',

    # Summoning commands
    'summon': 'summon',
    'join': 'will_join',
    'later': 'will_join_later',
    'decline': 'will_not_join',

    # Bot management (superuser-only)
    'user_promote': 'user_promote',
    'user_demote': 'user_demote',
    'raw_data': 'raw_data',
}


pending_user_actions = {
    'none': 0,
    'activity_add': 1,
}


def build_inline_keyboard(buttons: list):
    if not buttons:
        return None
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(button[0], callback_data=button[1]) for button in row] for row in buttons])


def build_default_keyboard(user: User):
    buttons = [['Do not disturb' if user.is_active else 'Ready', 'Status'], ['Activities list']]
    if user.pending_action != pending_user_actions['none']:
        buttons[0].insert(0, 'Cancel action')
    if user.has_right('summon'):
        buttons[1].append('Summon friends')
    if user.has_right('raw_data'):
        buttons[1].append('Raw data')
    return ReplyKeyboardMarkup([[KeyboardButton(x) for x in row] for row in buttons], resize_keyboard=True)


def build_summon_response_keyboard(activity_name: str):
    return build_inline_keyboard([[('Join now', 'join ' + activity_name),
                                   ('Coming', 'later ' + activity_name),
                                   ('Decline', 'decline ' + activity_name)]])


def callback_only(decorated_handler):
    def handler_wrapper(bot: Bot, update: Update):
        if update.callback_query:
            return decorated_handler(bot, update)
    return handler_wrapper


def send_response(user: User, bot: Bot, response):
    if not response:
        return
    if isinstance(response, tuple):
        user.send_message(bot, text=response[0], reply_markup=response[1])
    else:
        user.send_message(bot, text=response)


def personal_command(command=None):
    def personal_command_impl(decorated_handler):
        def decorated_handler_wrapper(bot: Bot, update: Update, user=None):
            if update.callback_query:
                update.callback_query.answer()

            if not user:
                user = User.get_or_create(telegram_user_id=update.effective_user.id,
                                          defaults={'telegram_login': update.effective_user.name})[0]
                if user.is_disabled_chat or user.telegram_login != update.effective_user.name:
                    user.telegram_login = update.effective_user.name
                    user.is_disabled_chat = False
                    user.save()

            if command and not user.has_right(command):
                send_response(user, bot, ('Not enough rights', build_default_keyboard(user)))
            else:
                send_response(user, bot, decorated_handler(bot, update, user))
        return decorated_handler_wrapper
    return personal_command_impl
