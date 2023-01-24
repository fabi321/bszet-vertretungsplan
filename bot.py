from os import getenv
from pathlib import Path
import logging
import html
import json
import traceback

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode

import check_credentials
import update_substitutions
from DB import DB

global db
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text: str = update.message.text.replace('/verify ', '').replace(',', ' ')
    parts: list[str] = text.split()
    if len(parts) != 2:
        await update.message.reply_text('Please specify the current login for geschuetzt.bszet.de, separated by space. E.g. /verify username password ')
        return
    is_valid: bool = check_credentials.check(parts[0], parts[1])
    if not is_valid:
        await update.message.reply_text('Please use the following format: "username" "password".')
    db.add_credentials_if_new(parts[0], parts[1])
    db.trust_user(update.effective_user.id)
    await update.message.reply_text('You have been successfully verified. Feel free to use /setclass now.')


async def setclass(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not db.is_trusted_user(update.effective_user.id):
        await update.message.reply_text('You need to be verified in order to use this command')
        return
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
    db.update_user(update.effective_user.id, True)
    await update.message.reply_text(f'You have successfully selected the class "{text}".')
    await update_substitutions.update_user(update.effective_user.id, db, context.bot)


async def removeclass(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db.clear_user_class(update.effective_user.id)
    await update.message.reply_text(f'You have successfully removed your previous class.')


async def listclasses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not db.is_trusted_user(update.effective_user.id):
        await update.message.reply_text('You need to be verified in order to use this command')
        return
    response: str = 'All known classes:\n'
    response += '\n'.join(db.get_all_recent_classes())
    await update.message.reply_text(response)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db.add_user(update.effective_user.id)
    await update.message.reply_text('To start using this bot, please verify that you know the login using /verify.')


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Sorry, I didn't understand that command.")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    # Finally, send the message
    await context.bot.send_message(
        chat_id=getenv("OWNER_ID"), text=message, parse_mode=ParseMode.HTML
    )


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
    app.add_handler(MessageHandler(filters.COMMAND, unknown))
    app.add_error_handler(error_handler)
    updater_context: update_substitutions.CustomContext = update_substitutions.CustomContext(db)
    app.job_queue.run_repeating(update_substitutions.update, 5*60, data=updater_context)
    app.run_polling()


if __name__ == '__main__':
    main()
