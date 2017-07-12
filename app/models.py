from os.path import dirname, realpath, sep
import peewee as pw
import peewee_migrate as pwm
import re
from telegram import Bot, TelegramError
import datetime

from .definitions import database_credentials, superuser_login, cooldown_time_minutes


_database = pw.PostgresqlDatabase(database_credentials['NAME'],
                                  user=database_credentials['USER'],
                                  password=database_credentials['PASSWORD'],
                                  host=database_credentials['HOST'],
                                  port=database_credentials['PORT'])
_router = pwm.Router(_database, migrate_dir=dirname(realpath(__file__)) + sep + "migrations")
_router.run()


class _BaseModel(pw.Model):
    """ Base model, that uses PostgreSQL database """
    class Meta:
        database = _database


class User(_BaseModel):
    """ Telegram user, signed for bot's services """
    telegram_user_id = pw.IntegerField(primary_key=True)
    telegram_login = pw.TextField(default='')
    rights_level = pw.IntegerField(default=0)
    pending_action = pw.IntegerField(default=0)
    is_active = pw.BooleanField(default=True)
    is_disabled_chat = pw.BooleanField(default=False)

    def has_right(self, command: str):
        if self.telegram_login == superuser_login:
            return True
        elif command in {'moderator_list', 'moderator_add', 'moderator_remove'}:
            return False
        elif command in {'summon', 'activity_add', 'activity_rem'}:
            return self.rights_level > 0
        return True

    def send_message(self, bot: Bot, *args, **kwargs):
        if self.is_disabled_chat:
            return

        try:
            bot.send_message(chat_id=self.telegram_user_id, *args, parse_mode='Markdown', **kwargs)
        except TelegramError:
            self.is_disabled_chat = True
            self.save()


class Activity(_BaseModel):
    """ Some activity, to which users can be invited """
    name = pw.TextField(unique=True)
    owner = pw.ForeignKeyField(User, on_delete='CASCADE')

    @classmethod
    def try_to_create(cls, new_activity_name: str, user: User):
        max_length = 25
        new_activity_name = new_activity_name.strip()
        if len(new_activity_name) > max_length:
            return None, 'name should be no longer than *{0}* characters.'.format(max_length)
        if len(new_activity_name) == 0:
            return None, 'name is empty.'
        if not re.match("^[\w\ \_\.\-]*$", new_activity_name):
            return None, 'allowed only alphanumeric characters, spaces and `_.-`'
        if cls.select().where(cls.name == new_activity_name).exists():
            return None, 'activity with name *{0}* already exists.'.format(new_activity_name)
        return cls.create(name=new_activity_name, owner=user), ''

    @classmethod
    def get_from_callback_data(cls, activity_name: str):
        activity_name = activity_name.split(' ', 1)[1]
        try:
            activity = Activity.get(Activity.name == activity_name)
        except Activity.DoesNotExist:
            return None, 'Activity *{0}* not found.'.format(activity_name)
        return activity, None

    def has_right_to_remove(self, user: User):
        if user.has_right('activity_rem'):
            return self.owner == user or user.telegram_login == superuser_login
        return False


class Participant(_BaseModel):
    """ User, agreed to take part in some activity """
    report_time = pw.TimestampField()
    is_accepted = pw.BooleanField(default=True)
    user = pw.ForeignKeyField(User, on_delete='CASCADE')
    activity = pw.ForeignKeyField(Activity, on_delete='CASCADE')

    @classmethod
    def clear_inactive(cls):
        lower_bound = datetime.datetime.now() - datetime.timedelta(minutes=cooldown_time_minutes)
        cls.delete().where(cls.report_time < lower_bound)

    @classmethod
    def select_active_users(cls, activity: Activity, user: User):
        return User.select().join(cls).where((cls.activity == activity) &
                                             (cls.user != user) &
                                             (cls.is_accepted is True))

    @classmethod
    def select_inactive_users(cls, activity: Activity):
        return (User.select().where(User.is_active)
                    .join(Subscription).where(Subscription.activity == activity).switch(User)
                    .join(Participant, pw.JOIN_LEFT_OUTER).where((Participant.activity == activity) &
                                                                 (Participant.id.is_null(True))))

    @classmethod
    def response_to_summon(cls, bot: Bot, user: User, activity: Activity, join_mode: str):
        cls.clear_inactive()
        is_accepted = join_mode != 'decline'
        messages = {'join': '{0} join you in *{1}*',
                    'later': '{0} will join you in *{1}* in a short while',
                    'decline': '{0} declined summon for *{1}*'}
        participant, was_created = cls.get_or_create(activity=activity, user=user,
                                                     defaults={'report_time': datetime.datetime.now(),
                                                               'is_accepted': is_accepted})
        if was_created or is_accepted is not participant.is_accepted:
            for active_user in cls.select_active_users(activity, user):
                active_user.send_message(bot, text=messages[join_mode].format(user.telegram_login, activity.name))
        if not was_created:
            participant.is_accepted = True
            participant.report_time = datetime.datetime.now()
            participant.save()


class Subscription(_BaseModel):
    """ User, receiving notifications and able to call other users for activity """
    user = pw.ForeignKeyField(User, on_delete='CASCADE')
    activity = pw.ForeignKeyField(Activity, on_delete='CASCADE')
