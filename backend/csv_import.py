import pandas as pd
import psycopg2
import os
import sqlite3
import sys

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


def check(table_name, cursor):
    cursor.execute(f'SELECT COUNT(*) FROM {table_name};')
    if cursor.fetchone()[0] > 0:
        print('База данных уже заполнена')
        return True
    return False


def copy_data(table_name, cursor, key):
    with open(f'{DIRECTORY}{key}', 'r', encoding='utf-8') as file:
        header = file.readline().strip().split(',')
        query = (f'COPY {table_name} ({", ".join(header)}) '
                 'FROM STDIN WITH (FORMAT CSV, HEADER FALSE, DELIMITER ",")')
        cursor.copy_expert(query, file)


def main():
    if os.getenv('SQLITE_ACTIVATED', 'False') == 'True':
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        for key in DATA:
            csv_file = f'{DIRECTORY}{key}'
            table_name = DATA[key]
            if check(table_name, cursor):
                sys.exit()
            df = pd.read_csv(csv_file)
            df.to_sql(table_name, conn, if_exists='append', index=False)
        conn.close()
    else:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        for key in DATA:
            table_name = DATA[key]
            cursor = conn.cursor()
            if check(table_name, cursor):
                sys.exit()
            copy_data(table_name, cursor, key)
        conn.close()
        print('done')


if __name__ == "__main__":
    main()
