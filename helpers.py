import pickle
from datetime import datetime
from datetime import timedelta




# Функция преобразования datetime в удобочитаемый формат
def timedelta_format(duration):
    days, seconds = duration.days, duration.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = (seconds % 60)
    return days, hours, minutes, seconds


# Сохранем devs в файл
def save_state(devs):
    with open('data', 'wb') as f:
        pickle.dump(devs, f)


# Загружаем devs из файла
def load_state():
    devs = {}
    with open('data', 'rb') as f:
        devs = pickle.load(f)
    return devs


# дефолтные devs в файл data
def setup():
    devs = {
        'dev2': {'user': 'free', 'chat_id:': 0, 'time': datetime.now()},
        'dev3': {'user': 'free', 'chat_id:': 0, 'time': datetime.now()},
        'dev4': {'user': 'free', 'chat_id:': 0, 'time': datetime.now()},
        'dev5': {'user': 'free', 'chat_id:': 0, 'time': datetime.now()},
        'dev6': {'user': 'free', 'chat_id:': 0, 'time': datetime.now()},
        'dev7': {'user': 'free', 'chat_id:': 0, 'time': datetime.now()},
        'dev8': {'user': 'free', 'chat_id:': 0, 'time': datetime.now()},
        'dev9': {'user': 'free', 'chat_id:': 0, 'time': datetime.now()},
        'dev10': {'user': 'free', 'chat_id:': 0, 'time': datetime.now()},
        'dev11': {'user': 'free', 'chat_id:': 0, 'time': datetime.now()},
        'dev12': {'user': 'free', 'chat_id:': 0, 'time': datetime.now()}
    }
    save_state(devs)


# Get tg_bot token
# Костыль: заменить на os.getenv и библиотеку dotenv, и передавать в нее токен
# def get_bot_token():
#     f = open('setup', mode='r', encoding='UTF-8')
#     token = f.read()
#     f.close()
#     return token

def get_bot_token():

    token = '5446452718:AAEzA4YucWKS2468I6EumCEjUH3lqj2UZhw'

    return token


# Get <user_name>, <chat_id> by <dev>
def get_dev_user(dev):
    devs = load_state()
    current_dev = devs.get(dev)
    if current_dev is not None:
        user = current_dev.get('user')
        chat_id = current_dev.get('chat_id')
        return user, chat_id
    else:
        return None


# Get <dev> status
def get_dev_status(dev):
    devs = load_state()
    current_dev = devs.get(dev)
    if current_dev is not None:
        d, h, m, s = timedelta_format(datetime.now() - current_dev.get('time'))
        user = current_dev.get('user')
        chat_id = current_dev.get('chat_id')
        time = f'(+{h}h {m}m)'
        return user, time, chat_id
    else:
        return False


# Returns all <dev> status
def get_all_status():
    devs = load_state()
    result = ''
    for dev in devs:
        user, time, chat_id = get_dev_status(dev)
        result += f'{dev} | @{user} {time}\n'
    return result


# Check <dev> for existing <user>: returns True if <user> is not 'free'
def check_dev_busy(dev):
    devs = load_state()
    current_dev = devs.get(dev)
    if current_dev is not None:
        if current_dev['user'] != 'free':
            return True
        else:
            return False


# Set <user> to <dev>: returns <dev> status if <dev> have existing <user>
def set_dev_user(dev, user, chat_id):
    devs = load_state()
    current_dev = devs.get(dev)
    if current_dev is not None:
        current_dev['user'] = user
        current_dev['time'] = datetime.now()
        current_dev['chat_id'] = chat_id
        save_state(devs)
        return f'{dev} занял @{user}'
    else:
        return f'{dev} не существует!'


# Reset <dev> status to "Free"
def free_dev(dev):
    devs = load_state()
    current_dev = devs.get(dev)
    if current_dev is not None:
        current_dev['user'] = 'free'
        current_dev['time'] = datetime.now()
        current_dev['chat_id'] = None
        save_state(devs)
        return f'{dev} теперь свободен!'
    else:
        return f'{dev} не существует!'
