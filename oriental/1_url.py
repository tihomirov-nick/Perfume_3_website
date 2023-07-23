from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sqlite3

conn = sqlite3.connect('products.db')
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS products (id TEXT, link TEXT)')

driver = webdriver.Firefox()

page_num = 1

while True:
    driver.get(f"https://www.orental.ru/perfume/?types=809116&page={page_num}")

    wait = WebDriverWait(driver, 10)
    product_links = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//a[@class="prod-teas__head"]')))

    if not product_links:
        break

    id_num = 10000 + (page_num - 1) * len(product_links)
    for link in product_links:
        id = f"SET{id_num:05}"
        c.execute('INSERT INTO products VALUES (?, ?)', (id, link.get_attribute('href')))
        conn.commit()

        id_num += 1

    page_num += 1

conn.close()
driver.quit()
