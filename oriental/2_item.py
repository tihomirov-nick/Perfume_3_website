import sqlite3
from selenium.webdriver import Chrome
from selenium_stealth import stealth
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import random
import re

from itertools import zip_longest

import time
import numpy as np

from multiprocessing import Pool
from tqdm import tqdm
from fake_useragent import UserAgent

ua = UserAgent()


def db_start():
    global c, conn
    conn = sqlite3.connect('orental.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS items (
            art TEXT,
            item_name TEXT,
            price REAL,
            prev_price REAL,
            nds REAL,
            ozon_id INTEGER,
            commerce_type TEXT,
            barcode INTEGER,
            weight REAL,
            width REAL,
            height REAL,
            length REAL,
            image_url TEXT,
            second_image_url TEXT,
            photo_360 TEXT,
            photo_id TEXT,
            brand TEXT,
            item_type TEXT,
            add_together INTEGER,
            volume REAL,
            sex TEXT,
            expiration_date TEXT,
            rich_content TEXT,
            min_kid INTEGER,
            max_kid INTEGER,
            plan TEXT,
            annotation TEXT,
            key_words TEXT,
            serie TEXT,
            in_one_item INTEGER,
            classification TEXT,
            country TEXT,
            weight_else TEXT,
            package TEXT,
            target_audience TEXT,
            composition TEXT,
            other_comp TEXT,
            parf_type TEXT, 
        okpd_code INTEGER
        )
    ''')


def get_data(art, url, proxies):
    proxy = random.choice(proxies)
    
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f'--proxy-server={proxy}')
    
    driver = uc.Chrome(options=options)
    
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            )
    
    try:
        driver.get(url=url)

        line_list = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="prod-description"]/div/div[1]/p')))
        for line in line_list:
            if str(line.text).split(': ')[0] == 'Страна производитель':
                country = str(line.text).split(': ')[1]

            if str(line.text).split(': ')[0] == 'Пол':
                sex = str(line.text).split(': ')[1]
                if sex == "Женский":
                    sex = "Женский"
                elif sex == "Мужской":
                    sex = "Мужской"
                elif sex == "Унисекс":
                    sex = "Женский;Мужской"

        brand_elements = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '/html/body/div[2]/div/div/div[1]/div/div/div/div[2]/div/div/div/div/div[1]/div/div/div[2]/div/div[1]/h1/span[1]')))
        brand = brand_elements[0].text

        name = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div/div/div[1]/div/div/div/div[2]/div/div/div/div/div[1]/div/div/div[2]/div/div[1]/h1/span[2]'))).text

        if any(x.lower() in brand.lower() for x in ["Antonio Banderas", "Hugo Boss", "Carolina Herrera", "Chanel", "Clarins", "Dior", "Dolce & Gabbana", "Escentric Molecules", "Armani", "Givenchy", "Lancome", "Lanvin", "Versace"]):
            return 0

        line_list = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="prod-types"]/div/div/div[2]/div/div/div/div[1]/div')))
        for line in line_list:
            if '+' in WebDriverWait(line, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'prod-line__info'))).text:
                volume = WebDriverWait(line, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'prod-line__info'))).text
            else:
                continue

            try:
                image_url = WebDriverWait(line, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'prod-line__cover'))).get_attribute('href')
            except:
                image_url = None
            volume = WebDriverWait(line, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'prod-line__info'))).text
            price = WebDriverWait(line, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'prod-line__new-price'))).text.replace(' ', '').replace('₽', '')

            if sex == "Женский":
                commerce_type = "Парфюмерный набор женский"
            elif sex == "Мужской":
                commerce_type = "Парфюмерный набор мужской"
            elif sex == "Женский;Мужской":
                commerce_type = "Парфюмерный набор женский"

            item_type = "Парфюмерный набор"

            item_name = f'{brand}, {name}, {volume}'
            prev_price = int(int(price) * np.random.uniform(1.2, 1.5))
            nds = "Не облагается"
            weight, length, width, height = 1, 2, 3, 4

            add_together = c.execute('SELECT id FROM LINKS WHERE link=?', (url,)).fetchone()
            target_audience = "Взрослая"
            composition = 'Alcohol Denat., Parfum ( Fragrance ), Aqua ( Water ), Ethylhexyl Methoxycinnamate, Butyl Methoxydibenzoylmethane, Ethylhexyl Salicylate, BHT, Limonene, Linatool, Benzyl Salicylate, Butylphenyl Methylpropional, Benzyl Benzoate, Citral, Citronellol, Geranio'
            danger_class = 'Не опасен'
            expiration_date = random.randint(550, 987)

            okpd_code = "ТН ВЭД - 3303 00 - Духи и туалетная вода; ОКПД - 20.42.11 - Духи и туалетная вода"

            annotation = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'prod-tabs__description'))).text

            c.execute('''
                INSERT INTO items (
                    art, item_name, price, prev_price, nds, ozon_id, commerce_type, barcode, weight, width, height, length, image_url, second_image_url, photo_360, photo_id, brand, item_type, add_together, volume, sex, expiration_date, rich_content, min_kid, max_kid, plan, annotation, key_words, serie, in_one_item, classification, country, weight_else, package, target_audience, composition, other_comp, parf_type, okpd_code
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? ,? ,?, ?, ?, ?)
            ''', (art, item_name, price, prev_price, nds, None, commerce_type, None, weight, width, height, length, image_url, None, None, None, brand, item_type, art, volume, sex, expiration_date, None, None, None, None, annotation, None, None, 1, None, country, None, None, target_audience, composition, None, 'Люкс', okpd_code))

            conn.commit()
    except:
        driver.quit()
        get_data(art, url, proxies)


proxies = ["PROXY1", "PROXY2", "PROXY3", ...]

with Pool(4) as p:
    for art, url in zip(arts, urls):
        p.apply_async(get_data, args=(art, url, proxies))
    p.close()
    p.join()
