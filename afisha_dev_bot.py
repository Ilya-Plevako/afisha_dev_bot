import os.path
import helpers
import telebot
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Костыль: перейти на getenv
token = helpers.get_bot_token()
bot: TeleBot = telebot.TeleBot(token)


# Ответ на команду /start
@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.username is not None:
        user = message.from_user.username
    else:
        user = message.from_user.first_name

    bot.send_message(message.chat.id, f'Привет, @{user}!\n'
                                      f'Доступные команды: \n'
                                      f'/status - статусы тестовых сред\n'
                                      f'take dev - забронировать dev\n'
                                      f'free dev - освободить dev\n')


# Получить статусы по всем dev в одном сообщении командой /status
@bot.message_handler(commands=['status'])
def status(message):
    answer = helpers.get_all_status()
    bot.reply_to(message, answer)


# Занять dev по сообщению 'take dev(номер)'разбирается регуляркой
@bot.message_handler(regexp='[Tt]ake [Dd]ev[0-9]')
def take_dev(message):
    dev = message.text[5:].lower()
    candidate_username = message.from_user.username
    candidate_chat_id = message.chat.id
    dev_username, dev_user_chat_id = helpers.get_dev_user(dev)

    # Проверяем, что dev существует
    if helpers.get_dev_status(dev) is False:
        bot.reply_to(message, f'{dev} не существует!')

    # Проверяем, что dev занят
    # Если False, то записываем запрашивающего хозяином и возвращаем ему ответ с успешным статусом
    elif helpers.check_dev_busy(dev) is False:
        answer = helpers.set_dev_user(dev, candidate_username, candidate_chat_id)
        bot.reply_to(message, answer)

    # Если True и там кто-то уже есть.
    else:
        # Пишем запрашивающему сообщение о том, что dev занят и кем
        bot.reply_to(message, f'{dev} занят @{dev_username}. Запрашиваю разрешение...')

        # Создаем объект Inline-клавиатуры

        def gen_markup():
            markup = InlineKeyboardMarkup()
            markup.row_width = 2
            # В данные колбеков передаем команду и данные кандидата
            markup.add(InlineKeyboardButton("Yes", callback_data=f'yes_{dev}_{candidate_username}_{candidate_chat_id}'),
                       InlineKeyboardButton("No", callback_data=f'no_{dev}_{candidate_username}_{candidate_chat_id}'))
            markup.one_time_keyboard = True
            return markup

        # Создаем обработчик колбеков нажатий и логику
        @bot.callback_query_handler(func=lambda call: True)
        def callback_query(call):
            # Прокидываем данные из колбека внутрь функции
            action, dev, candidate_username, candidate_chat_id = call.data.split("_")

            if action == 'yes':
                bot.answer_callback_query(call.id, "Спасибо :)")
                helpers.free_dev(dev)
                answer = helpers.set_dev_user(dev, candidate_username, candidate_chat_id)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text=f'Отдал {dev} -> @{candidate_username}')
                bot.send_message(candidate_chat_id, answer)
            else:
                bot.answer_callback_query(call.id, "Ну ладно :)")
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text=f'Оставил {dev}')
                # bot.edit_message_reply_markup(call.from_user.id, call.message.message_id, reply_markup=())
                bot.send_message(candidate_chat_id, f'Подожди, {dev} еще нужен!')

        # Отправляем запрос хозяину dev и пушим инлайн-клавиатуру
        bot.send_message(dev_user_chat_id, f'@{candidate_username} хочет отобрать у тебя {dev}!',
                         reply_markup=gen_markup())


# Освободить dev по сообщению 'free dev(номер)' разбирается регуляркой
@bot.message_handler(regexp='[Ff]ree [Dd]ev[0-9]')
def free_dev(message):
    dev = message.text[5:].lower()
    answer = helpers.free_dev(dev)
    bot.reply_to(message, answer)


# Возвращает пользователя на dev (для отладки)
@bot.message_handler(regexp='[Uu]ser [Dd]ev[0-9]')
def user_dev(message):
    dev = message.text[5:].lower()
    dev_username, dev_user_chat_id = helpers.get_dev_user(dev)
    answer = f'@{dev_username} -> {dev_user_chat_id}'
    bot.reply_to(message, answer)


# Устанавливает дефолтные настройки в файл data
@bot.message_handler(commands=['reset'])
def setup_default(message):
    helpers.setup()
    bot.reply_to(message, 'Установлены дефолтные настройки')


# Запускаем бота
# Можно использовать try/except с бесконечным циклом, но есть риск попасть в infinityloop
# Возможно, решается таской, которая будет перезапускать бота при падении

# Проверяем, есть ли файл 'data', в котором хранится текущий стейт devs
# Если такого нет, создаем файл с дефолтными настройками
if __name__ == '__main__':
    if os.path.isfile('data') is False:
        helpers.setup()
    bot.infinity_polling()
