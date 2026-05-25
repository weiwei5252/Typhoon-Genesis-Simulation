import re
import requests
from bs4 import BeautifulSoup

r = requests.get("https://zh.wikipedia.org/zh-tw/Python", headers={"User-Agent": "Mozilla/5.0"})
r.encoding = 'utf-8'

soup = BeautifulSoup(r.text, 'html.parser')

p_tags = soup.find_all('p')

for p in p_tags:
    content = p.get_text().strip()
    if content:  
        print(content)
        break    