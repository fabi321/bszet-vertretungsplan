import re

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.constants import ParseMode
from telegram.ext import ConversationHandler, ContextTypes, CommandHandler, MessageHandler, filters

import update_substitutions
from DB import DB

SELECT_AREA, SELECT_CLASS, SAVE_CLASS = range(3)
CLASS_REGEX: re.Pattern = re.compile(r'^(?:[A-Z]_[A-Z]+ ?[0-9]+/[0-9]+|[A-Z]+ ?[0-9]+)$')


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
    if area == 'bgy':
        await update.message.reply_text(
            '*Warnung: Es ist bekannt, dass der Vertretungsplan für das BGy manchmal nicht korrekt eingelesen wird\\!* '
            'Ob eine Vertretung da ist oder nicht, sollte funktionieren, aber die Details könnten fehlen\\.',
            parse_mode=ParseMode.MARKDOWN_V2
            )
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
        if CLASS_REGEX.match(class_name) and len(class_name) < 20:
            context.user_data['class'] = class_name
            context.user_data['area'] = area
            await update.message.reply_text(
                'Die Klasse wurde noch nicht gefunden. Bist du dir sicher, dass du sie richtig geschrieben hast?',
                reply_markup=ReplyKeyboardMarkup([['Nein', 'Ja']], resize_keyboard=True)
            )
            return SAVE_CLASS
        await update.message.reply_text('Leider wurde die Klasse nicht gefunden', reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    DB.add_user_to_class(update.effective_user.id, class_name)
    DB.update_user(update.effective_user.id, True)
    await update.message.reply_text(
        f'Du hast erfolgreich die Klasse {class_name} ausgewählt.', reply_markup=ReplyKeyboardRemove()
    )
    await update_substitutions.update_user(update.effective_user.id, context.bot)
    return ConversationHandler.END


async def save_class(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    class_name: str = context.user_data['class']
    area: str = context.user_data['area']
    context.user_data.clear()
    if update.message.text == 'Ja':
        DB.add_class_if_not_exists(class_name, area)
        await update.message.reply_text(
            f'Erfolgreich zu Klasse {class_name} hinzugefügt.', reply_markup=ReplyKeyboardRemove()
        )
    else:
        await update.message.reply_text('Nicht zur Gruppe hinzugefüft', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text('Erfolgreich abgebrochen', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def get_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler('set_class', set_class)],
        states={
            SELECT_AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, area_selected)],
            SELECT_CLASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, class_selected)],
            SAVE_CLASS: [MessageHandler(filters.TEXT, save_class)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
