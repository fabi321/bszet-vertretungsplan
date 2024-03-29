from telegram import Update
from telegram.ext import ConversationHandler, ContextTypes, CommandHandler, MessageHandler, filters

from util import check_credentials
from util.DB import DB

ENTER_USERNAME, ENTER_PASSWORD = range(2)


async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Bitte gib den Nutzernamen für geschuetzt.bszet.de ein oder brich mit /cancel ab.')
    return ENTER_USERNAME


async def entered_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['username'] = update.message.text
    await update.message.reply_text('Und das Passwort')
    return ENTER_PASSWORD


async def entered_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    password: str = update.message.text
    username: str = context.user_data['username']
    del context.user_data['username']
    is_valid: bool = check_credentials(username, password)
    if is_valid:
        DB.trust_user(update.effective_user.id)
        await update.message.reply_text(
            'Du wurdest erfolgreich verifiziert. Die Klasse kannst du mit /set_class setzen'
        )
    else:
        await update.message.reply_text('Die Verifikation war nicht erfolgreich.')
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if 'username' in context.user_data:
        del context.user_data['username']
    await update.message.reply_text('Erfolgreich abgebrochen')
    return ConversationHandler.END


def get_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler('verify', verify)],
        states={
            ENTER_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, entered_username)],
            ENTER_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, entered_password)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
