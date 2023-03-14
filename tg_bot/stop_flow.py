from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ConversationHandler, ContextTypes, CommandHandler, MessageHandler, filters

from util.DB import DB

STOP: int = 0


async def stop_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    markup: ReplyKeyboardMarkup = ReplyKeyboardMarkup([['Nein', 'Ja']], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        'Bist du dir sicher, dass du keine weiteren Vertretungen erhalten und alle deine Daten löschen möchtest?',
        reply_markup=markup
    )
    return STOP


async def actually_stop_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message_content: str = 'Vielen dank, dass du dich entshieden hast, zu bleiben.'
    if update.message.text == 'Ja':
        DB.delete_user(update.effective_user.id)
        message_content = ('Auf wiedersehen. Bedenke, dass du zuerst /start aufrufen musst, '
                           'bevor du weitere Befehle verwenden kannst')
    await update.message.reply_text(message_content, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def get_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler('stop', stop_bot)],
        states={
            STOP: [MessageHandler(filters.TEXT, actually_stop_bot)],
        },
        fallbacks=[],
    )
