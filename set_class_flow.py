from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ConversationHandler, ContextTypes, CommandHandler, MessageHandler, filters

import update_substitutions
from DB import DB

SELECT_AREA, SELECT_CLASS = range(2)


def group_entries(plain: list[str]) -> list[list[str]]:
    return [plain[n:n + 2] for n in range(0, len(plain), 2)]


async def set_class(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not DB.is_trusted_user(update.effective_user.id):
        await update.message.reply_text('Du musst dich zuerst verifizieren! Das ist möglich mit /verify')
        return ConversationHandler.END
    areas: list[list[str]] = group_entries(DB.get_areas())
    markup: ReplyKeyboardMarkup = ReplyKeyboardMarkup(
        areas, one_time_keyboard=True, resize_keyboard=True, input_field_placeholder='Bereich'
    )
    await update.message.reply_text('Bitte wähle den Bereich aus oder brich mit /cancel ab.', reply_markup=markup)
    return SELECT_AREA


async def area_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    area: str = update.message.text
    classes: list[list[str]] = group_entries(DB.get_all_recent_classes_for_area(area))
    if not classes:
        await update.message.reply_text(
            'Leider wurden für den Bereich keine Klassen gefunden', reply_markup=ReplyKeyboardRemove()
            )
        return ConversationHandler.END
    context.user_data['area'] = area
    markup: ReplyKeyboardMarkup = ReplyKeyboardMarkup(
        classes, one_time_keyboard=True, resize_keyboard=True, input_field_placeholder='Klasse'
    )
    await update.message.reply_text('Und die Klasse.', reply_markup=markup)
    return SELECT_CLASS


async def class_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    class_name: str = update.message.text
    area: str = context.user_data['area']
    del context.user_data['area']
    if not DB.check_if_class_exists(area, class_name):
        await update.message.reply_text('Leider wurde die Klasse nicht gefunden', reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    DB.add_user_to_class(update.effective_user.id, class_name)
    DB.update_user(update.effective_user.id, True)
    await update.message.reply_text(
        f'Du hast erfolgreich die Klasse {class_name} ausgewählt.', reply_markup=ReplyKeyboardRemove()
    )
    await update_substitutions.update_user(update.effective_user.id, context.bot)
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if 'area' in context.user_data:
        del context.user_data['area']
    await update.message.reply_text('Erfolgreich abgebrochen', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def get_conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler('set_class', set_class)],
        states={
            SELECT_AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, area_selected)],
            SELECT_CLASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, class_selected)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
