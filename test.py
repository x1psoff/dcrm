import requests
from bs4 import BeautifulSoup

url = "https://www.mdm-complect.ru/catalog/nozhki-rezbovye/47840/"
headers = {"User-Agent": "Mozilla/5.0"}

try:
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "lxml")
    
    title = soup.find("h1")
    price = soup.find("div", class_="price-main")
    
    print(f"Название: {title.text.strip()}" if title else "Название не найдено")
    print(f"Цена: {price.text.replace('руб.', '').strip()} руб." if price else "Цена не найдена")

except Exception as e:
    print(f"Ошибка: {e}")