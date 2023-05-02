from telegram.ext import *
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update

import langid
import translators as ts

print('Starting a bot....')

with open('lang_bot_token.txt', 'r') as file:
    tn = file.read().replace('\n', '')


class Language:
    def __init__(self, full_name: str, lang_id: int, lang_shorty: str):
        self.full_name = full_name
        self.id = lang_id
        self.lang_shorty = lang_shorty


languages = dict()
language_buttons = []


def init_languages():
    languages[0] = Language("Английский", 0, 'en')
    languages[1] = Language("Испанский", 1, 'es')
    languages[2] = Language("Немецкий", 2, 'de')

    for lang in languages.values():
        language_buttons.append([InlineKeyboardButton(lang.full_name, callback_data="lang: " + str(lang.id))])


class Translator:
    def __init__(self, current_lang: Language):
        self.lang = current_lang

    def switch_language(self, language: Language):
        self.lang = language

    def do_translate(self, text: str):
        text_lang = langid.classify(text)
        if text_lang[0] == self.lang.lang_shorty:
            return ts.translate_text(text, from_language=self.lang.lang_shorty, to_language='ru')
        elif text_lang[0] == 'ru':
            return ts.translate_text(text, to_language=self.lang.lang_shorty)
        else:
            return 'Невозможно определить язык'


def get_help_message():
    help_msg = "This is a bot for translating text from different languages. See how to operate with it:\n" \
               "`/start` - command to test the bot\n" \
               "`/choose_lang` - button to select the language to translate to\n" \
               "`/translate` - enter to translation mode. Write text to translate\n" \
               "`/done` - return from any mode back to commands, e.g. end translating.\n" \
               "`/help` - receive this message."
    return help_msg


async def start_commmand(update: Update, _):
    await update.message.reply_text('*Hello! Welcome To language learning bot!*', parse_mode='Markdown')
    await update.message.reply_text(get_help_message(), parse_mode='Markdown')
    return MAIN_STATE


async def help_command(update: Update, _) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(get_help_message(), parse_mode='Markdown')
    return MAIN_STATE


async def choose_lang(update: Update, _) -> None:
    """Select language to translate from message."""
    await update.message.reply_text("Выбери язык:", reply_markup=reply_markup)
    return MAIN_STATE


async def button(update: Update, _) -> None:
    """Button handler."""
    query = update.callback_query
    print(query)
    variant = query.data

    await query.answer()

    if variant.startswith('lang: '):
        lang = languages[int(variant[len('lang: '):])]
        await query.edit_message_text(text=f"Выбранный язык: _{lang.full_name}_", parse_mode='Markdown')
        translator.switch_language(lang)


async def translate(update: Update, _):
    """Translate the user message."""
    await update.message.reply_text("Enter phrase to translate.")
    return TRANSLATING


async def return_to_main_state(update: Update, _):
    """Set state to main back."""
    await update.message.reply_text("Done. Returned to main state.")
    return MAIN_STATE


async def text_for_translate(update: Update, _) -> None:
    """Enter phrase to translate."""
    await update.message.reply_text(translator.do_translate(update.message.text))
    return TRANSLATING


async def done(update: Update, _) -> int:
    """The output of the collected information and the end of the conversation."""
    return ConversationHandler.END


MAIN_STATE, TRANSLATING = range(2)

if __name__ == '__main__':
    init_languages()
    translator = Translator(languages[0])

    application = Application.builder().token(tn).build()

    # Commands
    application.add_handler(ConversationHandler(
        entry_points=[CommandHandler("start", start_commmand)],
        states={
            MAIN_STATE: [
                CommandHandler('choose_lang', choose_lang),
                CallbackQueryHandler(button),
                CommandHandler('translate', translate),
                CommandHandler('help', help_command),
            ],
            TRANSLATING: [
                CommandHandler('done', return_to_main_state),
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, text_for_translate
                )
            ],
        },
        fallbacks=[MessageHandler(filters.Regex("^Done$"), done)],
    ))

    # Create the ReplyKeyboardMarkup object
    reply_markup = InlineKeyboardMarkup(language_buttons)

    # Run bot
    application.run_polling(1.0)
