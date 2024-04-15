from random import choice

from telebot import TeleBot, types, custom_filters
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage

from tts import TTS
from settings import Settings, set_up_env_var
from get_logger import get_logger
from database import SessionLocal, create_all_tables
from crud import UserCrud


class TTSStates(StatesGroup):

    inactive = State()
    active = State()


BOT_TOKEN: str
TTS_API_KEY: str
TTS_FOLDER_ID: str


def run_bot() -> None:

    bot = TeleBot(BOT_TOKEN, state_storage=StateMemoryStorage())

    bot.add_custom_filter(custom_filters.StateFilter(bot))

    initial_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    initial_markup.add(types.KeyboardButton(text='/help'))
    initial_markup.add(types.KeyboardButton(text='/start_tts'))

    @bot.message_handler(commands=['help', 'start'])
    def help_handler(message: types.Message):

        reply_message = (
            'Привет, я - бот-time-to-speech (перевожу текст в голос), вот мои команды:\n'
            '/help или /start - список всех команд (ты уже тут)\n'
            '/start_tts - запуск перевода сообщений в голос\n'
            f'P.S. На каждого пользователя есть лимит символов: {Settings.CHARACTER_LIMIT_BY_USER}, без этого никак('
        )

        bot.reply_to(message, reply_message, reply_markup=initial_markup)

    def ask_tts_safe_handler(message: types.Message) -> bytes | str:
        """Performs a safe request to TTS, returning a TTS answer or string if a user exceeds the character limit"""
        with SessionLocal() as db:

            user_crud = UserCrud(db)

            user = user_crud.get(telegram_id=message.from_user.id)

            if not user:
                user = user_crud.create(telegram_id=message.from_user.id)

            if user.characters_spent > Settings.CHARACTER_LIMIT_BY_USER:
                return (
                    'Не удалось получить ответ от TTS сервиса, к сожалению, вы превысили лимит символов на'
                    ' пользователя(('
                )

            message_text = message.text

            tts_answer = TTS(TTS_API_KEY, TTS_FOLDER_ID).ask(message_text)

            if isinstance(tts_answer, bytes):
                user_crud.update(user, characters_spent=user.characters_spent + len(message_text))

            return tts_answer

    @bot.message_handler(state=TTSStates.active)
    def process_tts_message(message: types.Message):

        message_text = message.text

        # Safety check (a user must be able to use /help and view the list of bot commands):
        if message_text == '/help':

            help_handler(message)

            return

        if len(message_text) > Settings.REQUEST_MAX_CHARACTERS:

            bot.reply_to(message, 'Сообщение слишком длинное, пожалуйста, укоротите его')

            return

        tts_answer = ask_tts_safe_handler(message)

        if isinstance(tts_answer, bytes):
            bot.send_voice(message.chat.id, tts_answer, caption=f'Символов потрачено: {len(message_text)}')

        else:
            bot.reply_to(message, tts_answer)

    @bot.message_handler(commands=['start_tts'])
    def start_tts(message: types.Message):

        bot.set_state(message.from_user.id, TTSStates.active, message.chat.id)

        bot.reply_to(message, 'Теперь все ваши сообщения (кроме команд) будут переводиться в голос!')

    @bot.message_handler(content_types=['text'])
    def unknown_messages_handler(message: types.Message):

        replies = (
            'О, круто!',
            'Верно подмечено!',
            'Как с языка снял',
            'Какой ты всё-таки умный',
            'По-любому что-то умное написал',
            'Как лаконично-то!',
        )

        help_message = (
            '\n\nЕсли ты хотел, чтобы я что-то сделал, то я не распознал твою команду, пожалуйста, сверься с /help'
        )

        bot.reply_to(message, choice(replies) + help_message, reply_markup=initial_markup)

    bot.infinity_polling()


def main():

    global BOT_TOKEN, TTS_API_KEY, TTS_FOLDER_ID

    logger = get_logger('main')

    BOT_TOKEN = set_up_env_var('BOT_TOKEN', logger.error)
    TTS_API_KEY = set_up_env_var('TTS_API_KEY', logger.error)
    TTS_FOLDER_ID = set_up_env_var('TTS_FOLDER_ID', logger.error)

    if all((BOT_TOKEN, TTS_API_KEY, TTS_FOLDER_ID)):

        create_all_tables()

        run_bot()

    else:
        logger.error('Setup cannot be completed, some errors occurred')


if __name__ == '__main__':
    main()
