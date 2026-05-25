import re
import requests
from bs4 import BeautifulSoup

# 建議將 URL 改為 Python (大寫 P)，維基百科的詞條規範通常是大寫開頭
r = requests.get("https://zh.wikipedia.org/zh-tw/Python", headers={"User-Agent": "Mozilla/5.0"})
r.encoding = 'utf-8'

soup = BeautifulSoup(r.text, 'html.parser')

# 原本你是 print(soup.p.get_text())，現在我們改用 find_all 找到第一個「有內容」的 p
# 這樣既能保持簡潔，又不會抓到空的標籤
p_tags = soup.find_all('p')

for p in p_tags:
    content = p.get_text().strip()
    if content:  # 如果這個 p 裡面真的有文字
        print(content)
        break    # 抓到第一個就結束，效果就跟原圖的 soup.p 一樣