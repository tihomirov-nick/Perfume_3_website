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
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS items_data (art, search_name, item_name, price, prev_price, nds, commerce_type, weight, width, height, length, image_url, item_type, model_name, brand, sex, add_together, volume, country, target_audience, composition, danger_class, expiration_date, okpd_code, annotation)')
         

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
    else:
        weight = None
        length = None
        width = None
        height = None
    
    return weight, length, width, height


def get_data(art, url):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    driver.get(url=url)
    try:
        using_class = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, 'product-types__list')))

        brand = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.b-header__mainTitle'))).text
        if brand in ["Antonio Banderas", "Hugo Boss", "Carolina Herrera", "Chanel", "Clarins", "Dior", "Dolce & Gabbana", "Escentric Molecules", "Armani", "Givenchy", "Lancome", "Lanvin", "Versace"]:
            return 0

        name = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.b-header__subtitle'))).text

        # Получение пола
        sex = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, "dd")))[2].text
        if sex == "Для мужчин":
            sex = "Мужской"
        elif sex == "Для женщин":
            sex = "Женский"
        elif sex == "Унисекс":
            sex = "Женский;Мужской"

        country = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, "dd")))[-1].text

        line_list = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 's-productType__main')))
        for line in line_list:
            try:
                image_url = WebDriverWait(line, 3).until(EC.presence_of_element_located((By.CLASS_NAME, 's-productType__imgPicture'))).get_attribute('src')
            except:
                image_url = None
            main_volume = WebDriverWait(line, 3).until(EC.presence_of_element_located((By.CLASS_NAME, 's-productType__titleText'))).text
            try:
                price = WebDriverWait(line, 3).until(EC.presence_of_element_located((By.CLASS_NAME, 's-productType__priceNewValue'))).text
            except:
                price = WebDriverWait(line, 3).until(EC.presence_of_element_located((By.CLASS_NAME, 's-productType__lastPriceCount'))).text

            if "уценка" in (main_volume.lower()):
                continue

            match = re.search(r'(\d+([.,]\d+)?)мл', main_volume)
            if match:
                volume = match.group(1)
                
            match = re.search(r'(\d+\*\d+)', main_volume)
            if match:
                continue
            
            if int((eval(volume.replace(',', '.')))) < 14 and int((eval(volume.replace(',', '.')))) > 200:
                continue

            if str(volume) != str(sqlite3.connect("ozon_db.db").cursor().execute(f"SELECT volume FROM items WHERE art == '{art}'").fetchone()[0]):
                continue

            if "одеколон" in str(main_volume.lower()):
                main_item_type = "Одеколон"
            if "туалетная вода" in str(main_volume.lower()):
                main_item_type = "Туалетная вода"
            elif "духи" in str(main_volume.lower()):
                main_item_type = "Духи"
            elif "парфюмерная вода" in str(main_volume.lower()):
                main_item_type = "Парфюмерная вода"
            else:
                continue

            if sex == "Мужской":
                item_type = main_item_type + " мужские"
            elif sex == "Женский":
                item_type = main_item_type + " женские"
            elif sex == "Женский;Мужской":
                item_type = main_item_type + " унисекс"
            else:
                continue

            search_name = f'{brand} {name} {volume}ml'
            item_name = f'{brand}, {name}, {volume}мл., {item_type}'
            prev_price = int(price) * np.random.uniform(1.2, 1.5)
            nds = "Не облагается"
            commerce_type = item_type
            weight, length, width, height = get_dimensions(float(eval(volume.replace(',', '.'))))

            model_name = name
            brand = brand
            volume = volume
            add_together = True
            target_audience = "Взрослая"
            composition = 'Alcohol Denat., Parfum ( Fragrance ), Aqua ( Water ), Ethylhexyl Methoxycinnamate, Butyl Methoxydibenzoylmethane, Ethylhexyl Salicylate, BHT, Limonene, Linatool, Benzyl Salicylate, Butylphenyl Methylpropional, Benzyl Benzoate, Citral, Citronellol, Geranio'
            danger_class = 'Не опасен'
            expiration_date = random.randint(550, 987)

            if "одеколон" in str(main_volume.lower()):
                okpd_code = "ОКПД - 20.42.11.130 - Одеколоны"
            if "туалетная вода" in str(main_volume.lower()):
                okpd_code = "ТН ВЭД - 3303 00 900 0 - Вода туалетная; ОКПД - 20.42.11.120 - Вода туалетная"
            elif "духи" in str(main_volume.lower()):
                okpd_code = "ТН ВЭД - 3303 00 100 0 - Духи; ОКПД - 20.42.11.110 - Духи"
            elif "парфюмерная вода" in str(main_volume.lower()):
                okpd_code = "ТН ВЭД - 3303 00 - Духи и туалетная вода; ОКПД - 20.42.11 - Духи и туалетная вода"
            else:
                continue

            annotation = ""
            elements = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.collapsable p')))
            for element in elements:
                annotation += element.text + " "

            c.execute("INSERT INTO items_data (art, search_name, item_name, price, prev_price, nds, commerce_type, weight, width, height, length, image_url, item_type, model_name, brand, sex, add_together, volume, country, target_audience, composition, danger_class, expiration_date, okpd_code, annotation) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                            (art, search_name, item_name, price, prev_price, nds, commerce_type, weight, width, height, length, image_url, item_type, model_name, brand, sex, add_together, volume, country, target_audience, composition, danger_class, expiration_date, okpd_code, annotation))
            conn.commit()

    except TimeoutException:
        image_url = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.js-main-product-image'))).get_attribute('src')

        brand = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.b-header__mainTitle'))).text
        if brand in ["Antonio Banderas", "Hugo Boss", "Carolina Herrera", "Chanel", "Clarins", "Dior", "Dolce & Gabbana", "Escentric Molecules", "Armani", "Givenchy", "Lancome", "Lanvin", "Versace", 'Антонио Бандерас', 'Хуго Босс', 'Каролина Херрера', 'Шанел', 'Кларинс', 'Диор', 'Дольче & Габанна', 'Ескентрик Молекулес', 'Армани', 'Дживанши', 'Ланкоме', 'Ланвин', 'Версаче', 'Хьюго Босс', 'Клэринс', 'Клеринс', 'Дольче Габана', 'Дольче Габбана', 'Живанши', 'Ланком']:
            return 0

        name = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.b-header__subtitle'))).text
        main_volume = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.p-productCard__shortDescriptionText'))).text
        try:
            price = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'b-productSummary__priceNew'))).text
        except:
            price = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'b-productSummary__lastPriceCount'))).text

        sex = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, "dd")))[2].text
        if sex == "Для мужчин":
            sex = "Мужской"
        elif sex == "Для женщин":
            sex = "Женский"
        elif sex == "Унисекс":
            sex = "Женский;Мужской"

        country = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, "dd")))[-1].text

        match = re.search(r'(\d+([.,]\d+)?)МЛ', main_volume)
        if match:
            volume = match.group(1)

        if str(volume) != str(sqlite3.connect("ozon_db.db").cursor().execute(f"SELECT volume FROM items WHERE art == '{art}'").fetchone()[0]):
            return 0

        if int((eval(volume.replace(',', '.')))) < 14 and int((eval(volume.replace(',', '.')))) > 200:
            return 0

        match = re.search(r'(\d+\*\d+)', main_volume)
        if match:
            return 0

        if "одеколон" in str(main_volume.lower()):
            main_item_type = "Одеколон"
        if "туалетная вода" in str(main_volume.lower()):
            main_item_type = "Туалетная вода"
        elif "духи" in str(main_volume.lower()):
            main_item_type = "Духи"
        elif "парфюмерная вода" in str(main_volume.lower()):
            main_item_type = "Парфюмерная вода"
        else:
            return 0

        if sex == "Мужской":
            item_type = main_item_type + " мужские"
        elif sex == "Женский":
            item_type = main_item_type + " женские"
        elif sex == "Женский;Мужской":
            item_type = main_item_type + " унисекс"
        else:
            return 0
            
        search_name = f'{brand} {name} {volume}ml'
        item_name = f'{brand}, {name}, {volume}мл., {item_type}'
        price = price
        prev_price = int(price) * np.random.uniform(1.2, 1.5)
        nds = "Не облагается"
        commerce_type = item_type
        weight, length, width, height = get_dimensions(float(eval(volume.replace(',', '.'))))
        item_type = main_item_type
        model_name = name
        brand = brand
        add_together = False
        volume = volume
        target_audience = "Взрослая"
        composition = 'Alcohol Denat., Parfum ( Fragrance ), Aqua ( Water ), Ethylhexyl Methoxycinnamate, Butyl Methoxydibenzoylmethane, Ethylhexyl Salicylate, BHT, Limonene, Linatool, Benzyl Salicylate, Butylphenyl Methylpropional, Benzyl Benzoate, Citral, Citronellol, Geranio'
        danger_class = 'Не опасен'
        expiration_date = random.randint(550, 987)

        if "одеколон" in str(main_volume.lower()):
            okpd_code = "ОКПД - 20.42.11.130 - Одеколоны"
        if "туалетная вода" in str(main_volume.lower()):
            okpd_code = "ТН ВЭД - 3303 00 900 0 - Вода туалетная; ОКПД - 20.42.11.120 - Вода туалетная"
        elif "духи" in str(main_volume.lower()):
            okpd_code = "ТН ВЭД - 3303 00 100 0 - Духи; ОКПД - 20.42.11.110 - Духи"
        elif "парфюмерная вода" in str(main_volume.lower()):
            okpd_code = "ТН ВЭД - 3303 00 - Духи и туалетная вода; ОКПД - 20.42.11 - Духи и туалетная вода"
        else:
            return 0

        annotation = ""
        elements = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.collapsable p')))
        for element in elements:
            annotation += element.text + " "
        
        c.execute("INSERT INTO items_data (art, search_name, item_name, price, prev_price, nds, commerce_type, weight, width, height, length, image_url, item_type, model_name, brand, sex, add_together, volume, country, target_audience, composition, danger_class, expiration_date, okpd_code, annotation) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                            (art, search_name, item_name, price, prev_price, nds, commerce_type, weight, width, height, length, image_url, item_type, model_name, brand, sex, add_together, volume, country, target_audience, composition, danger_class, expiration_date, okpd_code, annotation))
        conn.commit()


if __name__ == "__main__":
    db_start()
    urls = c.execute("SELECT art, link_url FROM correct_table").fetchall()
    arts, urls = zip(*urls)

    # for art, url in zip(arts, urls):
    #     get_data(art, url)

    with Pool(4) as p:
        for art, url in zip(arts, urls):
            p.apply_async(get_data, args=(art, url))
        p.close()
        p.join()
