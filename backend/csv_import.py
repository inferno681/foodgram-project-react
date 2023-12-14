import pandas as pd
import sqlite3

DIRECTORY = '../data/'
DATA = {
    'ingredients.csv': 'recipes_ingredient',
    'tags.csv': 'recipes_tag',
}
DB_FILE = 'db.sqlite3'

conn = sqlite3.connect(DB_FILE)
for key in DATA:
    csv_file = f'{DIRECTORY}{key}'
    table_name = DATA[key]
    df = pd.read_csv(csv_file)
    df.to_sql(table_name, conn, if_exists='append', index=False)
conn.close()
