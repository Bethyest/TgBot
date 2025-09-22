import psycopg2
import configparser

#connect to bd
def add_token(db_name, login, password, tg_token):
    config = configparser.ConfigParser()
    config.add_section('info')
    config.set('info', 'db_name', db_name)
    config.set('info', 'login', login)
    config.set('info', 'password', password)
    config.set('info', 'tg_token', tg_token)
    with open('settings.ini', 'w') as config_file:
        config.write(config_file)

add_token(
    input('Enter database name: '),
    input('Enter login name: '),
    input('Enter password: '),
    input('Enter Telegram token: ')

)

config = configparser.ConfigParser()
config.read('settings.ini')
connection = psycopg2.connect(database=config['info']['db_name'], user=config['info']['login'],
                          password=config['info']['password'])
#create db
def create_db():
    with connection.cursor() as cur:
        cur.execute("""
        DROP TABLE IF EXISTS user_dictionary;
        DROP TABLE IF EXISTS users;
        DROP TABLE IF EXISTS dictionary;
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        user_id BIGINT UNIQUE NOT NULL,
        username varchar(255) NOT NULL
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS user_dictionary (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL REFERENCES users(user_id),
        target_word varchar(255) NOT NULL,
        translation varchar(255) NOT NULL
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS dictionary(
        id SERIAL PRIMARY KEY,
        target_word varchar(255) NOT NULL,
        translation varchar(255) NOT NULL
        );
        """)
        connection.commit()

#create user
def is_user_exists(user_id):
    with connection.cursor() as cur:
        cur.execute("""
        SELECT user_id FROM users
        WHERE user_id = %s""", (user_id,))
        return cur.fetchone() is not None

def create_user(user_id, username):
    with connection.cursor() as cur:
        if not is_user_exists(user_id):
            cur.execute("""
            INSERT INTO users (user_id, username)
            VALUES (%s, %s)""", (user_id, username))
            connection.commit()

        else:
            print(f'User {user_id} already exists')

#add words to main dict/user's dict
def fill_dictionary(word_list):
    with connection.cursor() as cur:
        cur.execute("""
        INSERT INTO dictionary(target_word, translation)
        VALUES (%s, %s)""", word_list)
        connection.commit()

def add_word(user_id, word, translation):
    with connection.cursor() as cur:
        if not is_word_exists(user_id, word):
            cur.execute("""
            INSERT INTO user_dictionary (user_id, target_word, translation)
            VALUES (%s, %s, %s)""",
            (user_id, word.strip().capitalize(), translation.strip().capitalize()))
            connection.commit()
        else:
            print(f'Word {word.strip().capitalize()} already exists')
            return(f'Word {word.strip().capitalize()} already exists')

#delete words from user's dict
def is_word_exists(user_id, word):
    with connection.cursor() as cur:
        cur.execute("""
        SELECT target_word FROM user_dictionary 
        WHERE user_id = %s AND target_word = %s""", (user_id, word.strip().capitalize()))
        return cur.fetchone() is not None

def delete_word(user_id, word):
    with connection.cursor() as cur:
        if is_word_exists(user_id, word):
            cur.execute("""
            DELETE FROM user_dictionary
            WHERE (user_id = %s
            AND target_word = %s)""", (user_id, word.strip().capitalize()))
            connection.commit()
            print(f'Word {word} deleted')
        else:
            print(f'Word {word} does not exist')

# get random words from dictionary
def get_random_words(user_id, limit):
    with connection.cursor() as cur:
        cur.execute("""
        SELECT target_word, translation FROM user_dictionary 
        WHERE user_id = %s 
        ORDER BY RANDOM() LIMIT %s""", (user_id, limit))
        return cur.fetchall()

def add_token(db_name, username, password, token):
    if 'database' not in config:
        config.add_section('database')
    config.set('database', 'db_name', db_name)
    config.set('database', 'username', username)
    config.set('database', 'password', password)
    if 'tg_token' not in config:
        config.add_section('tg_token')
    config.set('tg_token', 'token', token)
    with open('settings.ini', 'w') as config_file:
        config.write(config_file)

