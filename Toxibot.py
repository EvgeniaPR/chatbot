import telebot
import sqlite3
from transformers import pipeline
import logging
import telebot
from telebot import types
import string
from datetime import datetime, timedelta

# добавим логгирование, чтобы получать сообщения в консоль
logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)

def connection(base):
    conn = sqlite3.connect(base)
    cursor = conn.cursor()
    return conn, cursor

def decon(conn, cursor):
    cursor.close()
    conn.close()


# Создаем/вызываем базу данных SQLite
conn, cursor = connection('ban_words.db')

# Создаем таблицу для хранения списка запрещенных слов
cursor.execute('''CREATE TABLE IF NOT EXISTS chat_ban_words
                  (chat_id INTEGER PRIMARY KEY, words TEXT)''')
conn.commit()

# Создаем таблицу для хранения списка участников чата и кол-ва предупреждений
cursor.execute('''CREATE TABLE IF NOT EXISTS chat_ban_users
                  (chat_id INTEGER, user_id INTEGER PRIMARY KEY, counter_alert INTEGER )''')
conn.commit()
decon(conn, cursor)


# Инициализируем бота
bot = telebot.TeleBot("YOURTOKEN")

# Вызываем модель с сайта hugging face для определения токсичности текста
clf = pipeline(
    task='sentiment-analysis',
    model='SkolkovoInstitute/russian_toxicity_classifier')


# Функция для проверки, является ли пользователь администратором чата
def is_admin(chat_id, user_id):
    chat_member = bot.get_chat_member(chat_id, user_id)
    return chat_member.status in ['creator', 'administrator']

# приветствие
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if message.text == "/start":
        # Создаем клавиатуру
        keyboard = types.InlineKeyboardMarkup()
        # Добавляем кнопку с ссылкой на добавление бота в чат
        bot_username = "ToxBanBot"
        deep_link = f"https://t.me/{bot_username}?startgroup&admin=invite"
        key_add = types.InlineKeyboardButton(text='Добавить бота в чат', url=deep_link)
        keyboard.add(key_add)
        # Отправляем приглашение пользователю добавить бота в группу
        bot.send_message(message.chat.id, "Привет! Я бот, который может банить пользователей за токсичность.\n"
                                          "Для начала работы добавьте меня в чат и дайте права администратора.",
                                          reply_markup=keyboard)

# Обработчик команды /addbanwords для администраторов
@bot.message_handler(commands=['addbanwords'])
def add_banned_words(message):
    chat_id = message.chat.id
    if is_admin(chat_id, message.from_user.id):
        bot.send_message(chat_id, "Введите запрещенные слова через запятую (без пробелов):")
        bot.register_next_step_handler(message, save_banned_words)
    else:
        bot.send_message(chat_id, "Только администраторы могут настраивать запрещенные слова. Зайдите в группу, где вы являетесь администратором, чтобы выполнить эту команду")

# Функция для извлечения слов и преобразования из str в list
def alpha(words):
    words_alpha = [word.strip(string.punctuation) for word in words.split() if word.strip(string.punctuation).isalpha()]
    return words_alpha


# Функция для сохранения запрещенных слов
def save_banned_words(message):
    chat_id = message.chat.id
    words = message.text
    # извлекаем старый список слов
    conn, cursor = connection('ban_words.db')
    cursor.execute("SELECT words FROM chat_ban_words WHERE chat_id=?", (chat_id,))
    result = cursor.fetchone()
    if result is not None:
        old_list_str = result[0]
        old_list = alpha(old_list_str.lower())
    else:
        old_list = list()   
    decon(conn, cursor)
    words_list = words.lower().split(',')
    new_list = old_list + words_list
    new_list = str(new_list)
    # Добавляем новые слова в базу данных
    conn, cursor = connection('ban_words.db')
    cursor.execute("INSERT OR REPLACE INTO chat_ban_words (chat_id, words) VALUES (?, ?)", (chat_id, new_list))
    conn.commit()
    decon(conn, cursor)
    bot.send_message(chat_id, "Запрещенные слова обновлены.")        
        
# Обработчик команды /delbanwords для администраторов
@bot.message_handler(commands=['delbanwords'])
def del_banned_words(message):
    chat_id = message.chat.id
    if is_admin(chat_id, message.from_user.id):
        bot.send_message(chat_id, "Введите запрещенные слова, подлежащие удалению, через запятую (без пробелов):")
        bot.register_next_step_handler(message, del_words)
    else:
        bot.send_message(chat_id, "Только администраторы могут настраивать запрещенные слова. Зайдите в группу, где вы являетесь администратором, чтобы выполнить эту команду")

# Функция для удаления запрещенных слов
def del_words(message):
    chat_id = message.chat.id
    words = message.text
    # извлекаем старый список слов
    conn, cursor = connection('ban_words.db')
    cursor.execute("SELECT words FROM chat_ban_words WHERE chat_id=?", (chat_id,))
    old_list_str = cursor.fetchone()[0]
    old_list = alpha(old_list_str.lower())
    decon(conn, cursor)
    words_list = list(words.lower().split(','))
    new_list = [item for item in old_list if item not in words_list]
    # Преобразуем новый список в строку
    new_list_str = ','.join(new_list)
    # обновляем список
    conn, cursor = connection('ban_words.db')
    cursor.execute("INSERT OR REPLACE INTO chat_ban_words (chat_id, words) VALUES (?, ?)", (chat_id, new_list_str))
    conn.commit()
    decon(conn, cursor)
    bot.send_message(chat_id, "Запрещенные слова обновлены.")
    
# Обработчик команды /delallbanwords для администраторов
@bot.message_handler(commands=['delallbanwords'])
def del_all_banned_words(message):
    chat_id = message.chat.id
    if is_admin(chat_id, message.from_user.id):
        conn = sqlite3.connect('ban_words.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_ban_words WHERE chat_id=?", (chat_id, ))
        conn.commit()
        cursor.close()
        conn.close()
        bot.send_message(chat_id, "Запрещенные слова удалены.") 
    else:
        bot.send_message(chat_id, "Только администраторы могут настраивать запрещенные слова. Зайдите в группу, где вы являетесь администратором, чтобы выполнить эту команду")
        
        
# Обработчик команды /showbanwords для администраторов
@bot.message_handler(commands=['showbanwords'])
def show_banned_words(message):
    chat_id = message.chat.id
    if is_admin(chat_id, message.from_user.id):
        conn = sqlite3.connect('ban_words.db')
        cursor = conn.cursor()
        cursor.execute("SELECT words FROM chat_ban_words WHERE chat_id=?", (chat_id,))
        old_list_str = cursor.fetchone()[0]
        # old_list = old_list_str.lower().split(',')
        old_list = alpha(old_list_str)
        show_list = ','.join(old_list)
        cursor.close()
        conn.close()
        bot.send_message(chat_id, f"Запрещенные слова : {old_list_str}.") 
    else:
        bot.send_message(chat_id, "Только администраторы могут настраивать запрещенные слова. Зайдите в группу, где вы являетесь администратором, чтобы выполнить эту команду")
     
        
# Метод для обработки токсичных пользователей
# Эта функция запускается, если получено токичное сообщение или использовано запрещенное слово
def users_alerts(message):

    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Для данного пользователя извлекаем его историю
    conn, cursor = connection('ban_words.db')
    cursor.execute("SELECT counter_alert FROM chat_ban_users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    
    # Добавка штрафного балла пользователю
    if result is not None:
        counter_alert = result[0]
    else:
        counter_alert = 0
    counter_alert += 1
    decon(conn, cursor)

    conn, cursor = connection('ban_words.db')
    cursor.execute("INSERT OR REPLACE INTO chat_ban_users (chat_id, user_id, counter_alert) VALUES (?,?,?)",
                   (chat_id, user_id, counter_alert))
    conn.commit()
    decon(conn, cursor)
    
    # Отправка предупреждения в зависимости от счетчика пользователя + блокировка
    if counter_alert == 1:
        bot.reply_to(message, "⚠️ Внимание! Ваше сообщение содержит токсичный контент. Первое предупреждение")
    elif counter_alert == 2:
        bot.reply_to(message, "⚠️ Внимание! Ваше сообщение содержит токсичный контент. Последнее предупреждение перед блокировкой")
    elif counter_alert == 3:
        bot.reply_to(message, "⛔ Вы были заблокированы за сообщения, не соблюдающие правила чата")
        # Устанавливаем срок бана на 3 дня
        ban_duration = datetime.now() + timedelta(days=3)
        # Заблокировать участника на определенный срок
        bot.ban_chat_member(message.chat.id, message.from_user.id, until_date=ban_duration)
        

@bot.message_handler(func=lambda m: True)
def filter_toxic(message):
    # Проверка текстовых сообщений на токсичность используя модель
    results = clf(message.text)
    
    # Проверка текстовых сообщений на токсичность используя запрещенные слова
    chat_id = message.chat.id
    words = message.text.lower()
    # извлекаем список запрещенных слов
    conn, cursor = connection('ban_words.db')
    cursor.execute("SELECT words FROM chat_ban_words WHERE chat_id=?", (chat_id,))
    old_list_str = cursor.fetchone()[0]
    old_list = alpha(old_list_str.lower())
    decon(conn, cursor)
    
    # Обработка токсичных пользователей
    if results[0].get('label') == 'toxic' or any(item in words for item in old_list):
        users_alerts(message)
        

# Запуск бота
bot.polling(none_stop=True)
