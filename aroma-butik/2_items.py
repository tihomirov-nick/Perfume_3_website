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

options = uc.ChromeOptions()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument("--disable-blink-features=AutomationControlled")

driver = uc.Chrome(options=options)

stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
        )

url_error_arr = []


def db_start():
    global c, conn
    conn = sqlite3.connect('aroma.db')
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

def get_dimensions(volume):
    if 3 <= volume <= 14:
        weight = random.randint(42, 60)
        length = random.randint(44, 64)
        width = random.randint(44, 44)
        height = random.randint(55, 69)
    elif 15 <= volume <= 45:
        weight = random.randint(60, 150)
        length = random.randint(60, 100)
        width = random.randint(50, 100)
        height = random.randint(60, 140)
    elif 45 <= volume <= 99:
        weight = random.randint(150, 250)
        length = random.randint(120, 150)
        width = random.randint(50, 100)
        height = random.randint(80, 170)
    elif 99 <= volume <= 200:
        weight = random.randint(220, 360)
        length = random.randint(100, 200)
        width = random.randint(50, 100)
        height = random.randint(160, 360)
    # Объем более 200 мл
    else:
        weight = None
        length = None
        width = None
        height = None
    
    return weight, length, width, height


def get_data(art, url):
    conn = sqlite3.connect('aroma.db')
    c = conn.cursor()
    driver.get(url=url)

    try:
        line_list = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="main"]/div/div[2]/div/div[2]/div[1]/div[1]/table/tbody/tr')))
        for line in line_list:

            if WebDriverWait(line, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, 'td')))[0].text == 'Торговый дом:':
                brand = WebDriverWait(line, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, 'td')))[1].text

            if WebDriverWait(line, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, 'td')))[0].text == 'Производство:':
                country = WebDriverWait(line, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, 'td')))[1].text

            if WebDriverWait(line, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, 'td')))[0].text == 'Назначение:':
                sex = WebDriverWait(line, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, 'td')))[1].text
                if sex == "женский":
                    sex = "Женский"
                elif sex == "мужской":
                    sex = "Мужской"
                elif sex == "унисекс":
                    sex = "Женский;Мужской"

        name = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main"]/div/div[2]/div/div[1]/div[2]/div[1]/h1'))).text.replace(brand, '')
        if any(x.lower() in brand.lower() for x in ["Antonio Banderas", "Hugo Boss", "Carolina Herrera", "Chanel", "Clarins", "Dior", "Dolce & Gabbana", "Escentric Molecules", "Armani", "Givenchy", "Lancome", "Lanvin", "Versace"]):
            return 0

        line_list = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="main"]/div/div[2]/div/div[1]/div[2]/div[3]/div/table/tbody/tr')))
        for line in line_list:
            if 'набор' in WebDriverWait(line, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'ex_pr_name'))).text:
                volume = WebDriverWait(line, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'ex_pr_name'))).text
            else:
                continue

            try:
                image_url = WebDriverWait(line, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'ex_lazy_img'))).get_attribute('src')
            except:
                image_url = None
            volume = WebDriverWait(line, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'ex_pr_name'))).text
            price = str(WebDriverWait(line, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'ex_pr_price'))).text).split()[0].replace(".", "")

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
            weight, length, width, height = 1, 2, 3, 4 # get_dimensions(volume)

            add_together = c.execute('SELECT id FROM LINKS WHERE link=?', (url,)).fetchone()
            target_audience = "Взрослая"
            composition = 'Alcohol Denat., Parfum ( Fragrance ), Aqua ( Water ), Ethylhexyl Methoxycinnamate, Butyl Methoxydibenzoylmethane, Ethylhexyl Salicylate, BHT, Limonene, Linatool, Benzyl Salicylate, Butylphenyl Methylpropional, Benzyl Benzoate, Citral, Citronellol, Geranio'
            danger_class = 'Не опасен'
            expiration_date = random.randint(550, 987)

            okpd_code = "ТН ВЭД - 3303 00 - Духи и туалетная вода; ОКПД - 20.42.11 - Духи и туалетная вода"

            annotation = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'ex_long_text'))).text

            c.execute('''
                INSERT INTO items (
                    art, item_name, price, prev_price, nds, ozon_id, commerce_type, barcode, weight, width, height, length, image_url, second_image_url, photo_360, photo_id, brand, item_type, add_together, volume, sex, expiration_date, rich_content, min_kid, max_kid, plan, annotation, key_words, serie, in_one_item, classification, country, weight_else, package, target_audience, composition, other_comp, parf_type, okpd_code
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? ,? ,?, ?, ?, ?)
            ''', (art, item_name, price, prev_price, nds, None, commerce_type, None, weight, width, height, length, image_url, None, None, None, brand, item_type, art, volume, sex, expiration_date, None, None, None, None, annotation, None, None, 1, None, country, None, None, target_audience, composition, None, 'Люкс', okpd_code))

            conn.commit()

    except TimeoutException:

        line_list = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="main"]/div/div[2]/div/div[2]/div[1]/div[1]/table/tbody/tr')))
        for line in line_list:

            if WebDriverWait(line, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, 'td')))[0].text == 'Торговый дом:':
                brand = WebDriverWait(line, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, 'td')))[1].text

            if WebDriverWait(line, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, 'td')))[0].text == 'Производство:':
                country = WebDriverWait(line, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, 'td')))[1].text

            if WebDriverWait(line, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, 'td')))[0].text == 'Назначение:':
                sex = WebDriverWait(line, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, 'td')))[1].text
                if sex == "женский":
                    sex = "Женский"
                elif sex == "мужской":
                    sex = "Мужской"
                elif sex == "унисекс":
                    sex = "Женский;Мужской"

        name = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main"]/div/div[2]/div/div[1]/div[2]/div[1]/h1'))).text.replace(brand, '')
        if any(x.lower() in brand.lower() for x in ["Antonio Banderas", "Hugo Boss", "Carolina Herrera", "Chanel", "Clarins", "Dior", "Dolce & Gabbana", "Escentric Molecules", "Armani", "Givenchy", "Lancome", "Lanvin", "Versace"]):
            return 0

        line_list = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="main"]/div/div[2]/div/div[1]/div[2]/div[4]/div[2]/div[2]/label')))
        for line in line_list:
            line.click()
            image_url = WebDriverWait(line, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="main"]/div/div[2]/div/div[1]/div[1]/div[1]/div[2]/div/div/div/div[1]/div/a/img'))).get_attribute('src')
            volume = WebDriverWait(line, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'ex_set_radio_name'))).text

            elements = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//div[@class="ex_product_buy--price-block now"]')))
            prices = [element.text for element in elements]
            prices = [element for element in prices if element]
            price = prices[0].split()[0].replace('.', '')

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
            weight, length, width, height = 1, 2, 3, 4 # get_dimensions(volume)

            add_together = c.execute('SELECT id FROM LINKS WHERE link=?', (url,)).fetchone()
            target_audience = "Взрослая"
            composition = 'Alcohol Denat., Parfum ( Fragrance ), Aqua ( Water ), Ethylhexyl Methoxycinnamate, Butyl Methoxydibenzoylmethane, Ethylhexyl Salicylate, BHT, Limonene, Linatool, Benzyl Salicylate, Butylphenyl Methylpropional, Benzyl Benzoate, Citral, Citronellol, Geranio'
            danger_class = 'Не опасен'
            expiration_date = random.randint(550, 987)

            okpd_code = "ТН ВЭД - 3303 00 - Духи и туалетная вода; ОКПД - 20.42.11 - Духи и туалетная вода"

            annotation = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'ex_long_text'))).text

            c.execute('''
                INSERT INTO items (
                    art, item_name, price, prev_price, nds, ozon_id, commerce_type, barcode, weight, width, height, length, image_url, second_image_url, photo_360, photo_id, brand, item_type, add_together, volume, sex, expiration_date, rich_content, min_kid, max_kid, plan, annotation, key_words, serie, in_one_item, classification, country, weight_else, package, target_audience, composition, other_comp, parf_type, okpd_code
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? ,? ,?, ?, ?, ?)
            ''', (art, item_name, price, prev_price, nds, None, commerce_type, None, weight, width, height, length, image_url, None, None, None, brand, item_type, art, volume, sex, expiration_date, None, None, None, None, annotation, None, None, 1, None, country, None, None, target_audience, composition, None, 'Люкс', okpd_code))

            conn.commit()


if __name__ == "__main__":
    db_start()
    urls = c.execute("SELECT id, link FROM links").fetchall()
    arts, urls = zip(*urls)

    with Pool(4) as p:
        for art, url in zip(arts, urls):
            p.apply_async(get_data, args=(art, url))
        p.close()
        p.join()
