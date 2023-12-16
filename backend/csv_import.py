import pandas as pd
import psycopg2
import os
import sqlite3

from dotenv import load_dotenv

load_dotenv()

DIRECTORY = './data/'
DATA = {
    'ingredients.csv': 'recipes_ingredient',
    'tags.csv': 'recipes_tag',
}
DB_FILE = 'db.sqlite3'

DB_CONFIG = {
    'dbname': os.getenv('POSTGRES_DB', 'django'),
    'user': os.getenv('POSTGRES_USER', 'django'),
    'password': os.getenv('POSTGRES_PASSWORD', ''),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', 5432),
}


def copy_data(table_name, cursor, key):
    with open(f'{DIRECTORY}{key}', 'r', encoding='utf-8') as file:
        header = file.readline().strip().split(',')
        query = (f'COPY {table_name} ({", ".join(header)}) '
                 'FROM STDIN WITH (FORMAT CSV, HEADER FALSE, DELIMITER ",")')
        try:
            cursor.copy_expert(query, file)
        except psycopg2.IntegrityError as error:
            raise psycopg2.IntegrityError(f'Данные уже загружены. log:{error}')
        except Exception as error:
            raise psycopg2.IntegrityError(f'Данные уже загружены. log:{error}')


if os.getenv('SQLITE_ACTIVATED', 'False') == 'True':
    conn = sqlite3.connect(DB_FILE)
    for key in DATA:
        csv_file = f'{DIRECTORY}{key}'
        table_name = DATA[key]
        df = pd.read_csv(csv_file)
        try:
            df.to_sql(table_name, conn, if_exists='append', index=False)
        except sqlite3.IntegrityError as error:
            raise sqlite3.IntegrityError(f'Данные уже загружены. log:{error}')
        except Exception as error:
            raise sqlite3.IntegrityError(f'Данные уже загружены. log:{error}')
    conn.close()
else:
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    for key in DATA:
        table_name = DATA[key]
        cursor = conn.cursor()
        try:
            copy_data(table_name, cursor, key)
        except psycopg2.IntegrityError as error:
            raise psycopg2.IntegrityError(f'Данные уже загружены. log:{error}')
        except Exception as error:
            raise psycopg2.IntegrityError(f'Данные уже загружены. log:{error}')
        cursor.close()
    conn.close()
