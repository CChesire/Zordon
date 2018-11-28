from app.core.info import PROJECT_FULL_NAME
from app.handlers.context import Context


def on_help_or_start(context: Context):
    message_template = 'Hello world!\n{project}'
    context.send_response_message(message_template.format(project=PROJECT_FULL_NAME))
