import requests
import pandas as pd
import sqlite3
import time

def compare_strings(s1, s2):
    try:
        s1 = pd.Series(str(s1).lower().split())
        s2 = pd.Series(str(s2).lower().split())
        correct = []
        check = []
        incorrect = []

        if len(s1) < len(s2):
            shorter_series, longer_series = s1, s2
        else:
            shorter_series, longer_series = s2, s1

        count = shorter_series.isin(longer_series).sum()

        if count == len(shorter_series):
            correct.append(shorter_series.tolist())
            return 1
        elif count >= 1:
            check.append(shorter_series.tolist())
            return 2
        else:
            incorrect.append(shorter_series.tolist())
            return 0
    except ValueError as e:
        add_error_to_database(str(e), None, None)
        return None

def add_to_database(compare_result, data):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS correct_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT,
            link_url TEXT,
            brand TEXT,
            name TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS check_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT,
            link_url TEXT,
            brand TEXT,
            name TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS incorrect_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT,
            link_url TEXT,
            brand TEXT,
            name TEXT
        )
    ''')

    if compare_result == 1:
        table_name = 'correct_table'
    elif compare_result == 2:
        table_name = 'check_table'
    else:
        table_name = 'incorrect_table'

    query = f"INSERT INTO {table_name} (query, link_url, brand, name) VALUES (?, ?, ?, ?)"
    c.execute(query, data)

    conn.commit()
    conn.close()

def add_error_to_database(error_message, url, query):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS error_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            error_message TEXT,
            url TEXT,
            query TEXT
        )
    ''')

    query = "INSERT INTO error_table (error_message, url, query) VALUES (?, ?, ?)"
    c.execute(query, (error_message, url, query))

    conn.commit()
    conn.close()

conn = sqlite3.connect('ozon_db.db')
c = conn.cursor()
c.execute("SELECT name FROM items")
search_queries = [row[0] for row in c.fetchall()]
conn.close()

api_key = "594L68C4CP"
base_url = "https://sort.diginetica.net/search"

for query in search_queries:
    url = f"{base_url}?st={query}&apiKey={api_key}&strategy=advanced,zero_queries_predictor&fullData=true&withCorrection=true&withFacets=t"

    response = requests.get(url)

    if response.status_code != 200:
        time.sleep(60)
        response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        products = data['products']

        try:
            compare_result = compare_strings(query, products[0]['name'] + ' ' + products[0]['brand'])

            if compare_result is not None:
                add_to_database(compare_result, (query, products[0]['link_url'], products[0]['brand'], products[0]['name']))
        except IndexError as e:
            add_error_to_database(str(e), url, query)

