# flake8: noqa
import psycopg2
import pandas as pd
import os

from dotenv import load_dotenv

load_dotenv()

DIRECTORY = './data/'
DATA = {
    'ingredients.csv': 'recipes_ingredient',
    'tags.csv': 'recipes_tag',
}

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
        query = f"COPY {table_name} ({', '.join(header)}) FROM STDIN WITH (FORMAT CSV, HEADER FALSE, DELIMITER ',')"
        cursor.copy_expert(query, file)


conn = psycopg2.connect(**DB_CONFIG)
conn.autocommit = True

for key in DATA:
    table_name = DATA[key]
    cursor = conn.cursor()
    copy_data(table_name, cursor, key)
    cursor.close()

conn.close()
