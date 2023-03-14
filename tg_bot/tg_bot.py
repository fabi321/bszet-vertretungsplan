import html
import json
import logging
import traceback
from os import getenv

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

import tg_bot.set_class_flow
import tg_bot.stop_flow
import tg_bot.update_users
import tg_bot.verify_flow
from util.DB import DB

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


async def removeclass(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    DB.clear_user_class(update.effective_user.id)
    await update.message.reply_text(f'Letzte Klasse erfolgreich entfernt.')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    DB.add_user(update.effective_user.id)
    await update.message.reply_text('Um diesen Bot zu verwenden, verifiziere dich mit /verify.')


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Sorry, den Befehl kenne ich nicht.")


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
    app: Application = ApplicationBuilder().token(getenv('BOT_API_TOKEN')).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(tg_bot.verify_flow.get_handler())
    app.add_handler(tg_bot.set_class_flow.get_handler())
    app.add_handler(tg_bot.stop_flow.get_handler())
    app.add_handler(CommandHandler('clear_class', removeclass))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))
    app.add_error_handler(error_handler)
    app.job_queue.run_repeating(tg_bot.update_users.message_users, 5 * 60)
    app.run_polling()
