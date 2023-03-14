from datetime import datetime

from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import Forbidden
from telegram.ext import CallbackContext
from telegram.helpers import escape_markdown

from util.DB import DB


async def update_user(uid: int, bot: Bot) -> None:
    result: str = 'Aktuelle Vertretungen:\n\n'
    is_new: bool = False
    for substitution in DB.get_all_substitutions_for_user(uid):
        line: str = datetime.fromtimestamp(substitution.day).strftime('%a, %d.%m')
        line += f', {substitution.lesson}: {substitution.teacher} {substitution.subject} {substitution.room}'
        if substitution.notes:
            line += f' ({substitution.notes})'
        line = escape_markdown(line, version=2)
        if substitution.is_new:
            line = f'*{line}*'
            is_new = True
        result += line + '\n'
    if is_new:
        try:
            await bot.send_message(chat_id=uid, text=result, parse_mode=ParseMode.MARKDOWN_V2)
            DB.update_user(uid)
        except Forbidden:
            DB.delete_user(uid)


async def message_users(context: CallbackContext) -> None:
    for uid in DB.get_all_updated_users():
        await update_user(uid, context.bot)

