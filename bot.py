from os import getenv
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes

import check_credentials
import update_substitutions
from DB import DB

global db


async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text: str = update.message.text.replace('/verify ', '').replace(',', ' ')
    parts: list[str] = text.split()
    if len(parts) != 2:
        await update.message.reply_text('Please specify the current login for geschuetzt.bszet.de, separated by space.')
        return
    is_valid: bool = check_credentials.check(parts[0], parts[1])
    if not is_valid:
        await update.message.reply_text('Please use the following format: "username" "password".')
    db.add_credentials_if_new(parts[0], parts[1])
    db.trust_user(update.effective_user.id)
    await update.message.reply_text('You have been successfully verified. Feel free to use /setclass now.')


async def setclass(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text: str = update.message.text.replace('/setclass', '').strip()
    if not text or len(text) >= 15:
        await update.message.reply_text('Please specify a class like "/setclass C_MI 21/3".')
        return
    if text not in db.get_all_recent_classes():
        await update.message.reply_text(
            f'The class {text} is not known. If you believe that this is an error, check back later.'
            )
        return
    db.add_user_to_class(update.effective_user.id, text)
    await update.message.reply_text(f'You have successfully selected the class "{text}".')


async def removeclass(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db.clear_user_class(update.effective_user.id)
    await update.message.reply_text(f'You have successfully removed your previous class.')


async def listclasses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response: str = 'All known classes:\n'
    response += '\n'.join(db.get_all_recent_classes())
    await update.message.reply_text(response)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db.add_user(update.effective_user.id)
    await update.message.reply_text('To start using this bot, please verify that you know the login using /verify.')


def main() -> None:
    global db
    load_dotenv()
    app: Application = ApplicationBuilder().token(getenv('BOT_API_TOKEN')).build()
    db = DB(Path(getenv('DATABASE_FILE')))
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('verify', verify))
    app.add_handler(CommandHandler('setclass', setclass))
    app.add_handler(CommandHandler('removeclass', removeclass))
    app.add_handler(CommandHandler('listclasses', listclasses))
    updater_context: update_substitutions.CustomContext = update_substitutions.CustomContext(db)
    app.job_queue.run_repeating(update_substitutions.update, 10, data=updater_context)
    app.run_polling()


if __name__ == '__main__':
    main()
