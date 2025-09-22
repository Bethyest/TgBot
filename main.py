import configparser
import random
from telebot import types, TeleBot, custom_filters
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage
from Db import (create_db, create_user, get_random_words, fill_dictionary, add_word, delete_word, is_user_exists)

print('Starting bot...')

config = configparser.ConfigParser()
config.read('settings.ini')

create_db()

state_storage = StateMemoryStorage()
token_bot = config['info']['tg_token']
bot = TeleBot(token_bot, state_storage=state_storage)

def show_hint(*lines):
    return '\n'.join(lines)

def show_target(data):
    return f"{data['target_word']} -> {data['translate_word']}"

class Command:
    ADD_WORD = 'Add word ➕'
    DELETE_WORD = 'Delete word🔙'
    NEXT = 'Next word ⏭'

class MyStates(StatesGroup):
    target_word = State()
    translate_word = State()
    another_words = State()

buttons = []
mmarkup = types.ReplyKeyboardMarkup(row_width=2)
next_btn = types.KeyboardButton(Command.NEXT)
add_word_btn = types.KeyboardButton(Command.ADD_WORD)
delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
buttons.extend([next_btn, add_word_btn, delete_word_btn])

mmarkup.add(*buttons)


@bot.message_handler(commands=['cards', 'start'])
def create_cards(message):
    cid = message.chat.id
    username = message.chat.username

    word_list = [('Cat', 'Кошка'), ('Dog', 'Собака'), ('House', 'Дом'), ('Fox', 'Лиса'), ('Pussy', 'Киска'),
                 ('Cup', 'Чашка'), ('Coffee', 'Кофе'), ('Tea', 'Чай'), ('She', 'Она'), ('Love', 'Любовь')]

    for word in word_list:
        fill_dictionary(word)

    if not is_user_exists(cid):
        create_user(cid, username)
        print(f'New user {username} created.')
        bot.send_message(cid, "Hello, stranger, let's study English...", reply_markup=mmarkup)

        for word in word_list:
            add_word(cid, word[0], word[1])

    words = get_random_words(cid, 4)
    if not words or len(words) < 4:
        bot.send_message(cid, "No words available\nAdd new ones using 'Add word ➕' button.", reply_markup=mmarkup)
        print("Слов недостаточно для создания карточек.")
        return

    markup = types.ReplyKeyboardMarkup(row_width=2)

    global buttons
    buttons = []
    target_word, translate_word = words[0]
    target_word_btn = types.KeyboardButton(target_word)
    buttons.append(target_word_btn)
    others = [w[0] for w in words[1:]]
    other_words_btns = [types.KeyboardButton(word) for word in others]
    buttons.extend(other_words_btns)
    random.shuffle(buttons)
    next_btn = types.KeyboardButton(Command.NEXT)
    add_word_btn = types.KeyboardButton(Command.ADD_WORD)
    delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
    buttons.extend([next_btn, add_word_btn, delete_word_btn])

    markup.add(*buttons)

    greeting = f"Choose the translation or the word:\n🇷🇺 {translate_word}"
    bot.send_message(message.chat.id, greeting, reply_markup=markup)
    bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['target_word'] = target_word
        data['translate_word'] = translate_word
        data['other_words'] = others

@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_cards(message):
    create_cards(message)

@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def send_delete_word(message):
    def del_word(msg):
        delete_word(msg.chat.id, msg.text)
        bot.send_message(cid, f'Word "{msg.text}" successfully deleted\nUse button "Next word ⏭" to continue', reply_markup=mmarkup)

    cid = message.chat.id
    msg = bot.send_message(cid, 'Enter English word you want to delete: ', reply_markup=mmarkup)
    bot.register_next_step_handler(msg, del_word)

@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def send_add_word(message):
    def ad_word(msg):
        if msg.text.count(',') == 1:
            add_word(msg.chat.id, msg.text.split(',')[0], msg.text.split(',')[1])
            bot.send_message(cid, f'Word "{msg.text.split(',')[0]}" successfully added\nUse button "Next word ⏭" to continue', reply_markup=mmarkup)
            print(f'Word "{msg.text.split(',')[0]}" successfully added')
        else:
            bot.send_message(cid,'Error! Use one comma (,) to separate words!', reply_markup=mmarkup)
            msg = bot.send_message(cid,'Enter English word and translation you want to add separated by comma (word, translation): ', reply_markup=mmarkup)
            bot.register_next_step_handler(msg, ad_word)

    cid = message.chat.id
    msg = bot.send_message(cid, 'Enter English word and translation you want to add separated by comma (word, translation): ', reply_markup=mmarkup)
    bot.register_next_step_handler(msg, ad_word)

@bot.message_handler(func=lambda message: True, content_types=['text'])
def message_reply(message):
    text = message.text
    markup = types.ReplyKeyboardMarkup(row_width=2)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        target_word = data['target_word']
        if text == target_word:
            hint = show_target(data)
            hint_text = ["Good job!❤", hint]
            hint = show_hint(*hint_text)
            bot.send_message(message.chat.id, hint, reply_markup=mmarkup)
        else:
            hint = show_hint("Wrong answer!❌ Try again!",
                             f"🇷🇺{data['translate_word']}")
            bot.send_message(message.chat.id, hint, reply_markup=markup)

bot.add_custom_filter(custom_filters.StateFilter(bot))

bot.infinity_polling(skip_pending=True)
