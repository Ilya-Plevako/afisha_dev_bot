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
                                      f'take devX - забронировать dev №X\n'
                                      f'free devX - освободить dev №X\n')


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

    elif str(candidate_chat_id) == str(dev_user_chat_id):
        bot.reply_to(message, f"{dev} и так твой!")

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
            markup.add(InlineKeyboardButton("Отдать", callback_data=f'yes_{dev}_{candidate_chat_id}_{candidate_username}'),
                       InlineKeyboardButton("Оставить себе", callback_data=f'no_{dev}_{candidate_chat_id}_{candidate_username}'))
            markup.one_time_keyboard = True
            return markup

        # Создаем обработчик колбеков нажатий и логику
        @bot.callback_query_handler(func=lambda call: call.data[:3] == 'yes' or call.data[:2] == 'no')
        def callback_query(call):
            # Прокидываем данные из колбека внутрь функции

            action, dev, candidate_chat_id, candidate_username = call.data.split("_", 3)

            if action == 'yes':
                bot.answer_callback_query(call.id, "Спасибо :)")
                helpers.free_dev(dev)
                helpers.set_dev_user(dev, candidate_username, candidate_chat_id)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text=f'Спасибо, что отдал {dev} коллеге @{candidate_username}')
                bot.send_message(candidate_chat_id, f'Ура, {dev} теперь в твоём распоряжении!')
            else:
                bot.answer_callback_query(call.id, "Ну ладно :)")

                markup_refuse_time = InlineKeyboardMarkup()
                markup_refuse_time.add(InlineKeyboardButton("15 минут", callback_data=f'min15'),
                                       InlineKeyboardButton("1 час", callback_data=f'min60'),
                                       InlineKeyboardButton("Не скоро", callback_data=f'min999'))
                markup_refuse_time.one_time_keyboard = True
                bot.send_message(call.message.chat.id, text='Через сколько сможешь освободить?', reply_markup=markup_refuse_time)

                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text=f'{dev} остался твоим')
                # bot.send_message(candidate_chat_id, f'Подожди, {dev} еще нужен!')

        # Отправляем запрос хозяину dev и пушим инлайн-клавиатуру
        bot.send_message(dev_user_chat_id, f'@{candidate_username} хочет взять у тебя {dev}!',
                         reply_markup=gen_markup())

        @bot.callback_query_handler(func=lambda call: call.data[:3] == 'min')
        def callback_query(call):
            if call.message:
                if call.data == "min15":
                    bot.send_message(candidate_chat_id, text=f'{dev} еще нужен, подожди 15 минут, пожалуйста')
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                          text=f'Спасибо!')
                if call.data == "min60":
                    bot.send_message(candidate_chat_id, text=f'{dev} еще нужен, подожди 1 час, пожалуйста')
                if call.data == "min999":
                    bot.send_message(candidate_chat_id, text=f'{dev} нужен на целый день, можешь взять другой dev, пожалуйста?')


# Освободить dev по сообщению 'free dev(номер)' только владельцем dev
@bot.message_handler(regexp='^[Ff]ree [Dd]ev[0-9]')
def free_dev(message):
    dev = message.text[5:].lower()
    user, time, chat_id = helpers.get_dev_status(dev)
    if user == 'free':
        bot.reply_to(message, f'{dev} не был занят.')
    elif message.chat.id == chat_id:
        answer = helpers.free_dev(dev)
        bot.reply_to(message, answer)
    else:
        bot.reply_to(message, f'{dev} занят не тобой.\nИспользуй take {dev}, чтобы запросить его использование')


# Освободить dev по сообщению 'hard free dev(номер)' (для отладки)
@bot.message_handler(regexp='^[Hh]ard [Ff]ree [Dd]ev[0-9]')
def hard_free_dev(message):
    dev = message.text[10:].lower()
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
