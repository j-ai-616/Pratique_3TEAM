import requests
import csv
import os
import html #추가
import re   #추가
from datetime import datetime   #추가
from dotenv import load_dotenv

load_dotenv()

NAVER_CLIENT_ID = os.getenv('NAVER_CLIENT_ID')
NAVER_CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET')

url = 'https://openapi.naver.com/v1/search/news.json'

headers = {
    "X-Naver-Client-Id" : NAVER_CLIENT_ID,
    "X-Naver-Client-Secret" : NAVER_CLIENT_SECRET
}

params = {
    'query' : '전기차',
    'display' : 10, 
    'start' : 1,
    'sort' : 'sim'
}

def clean_text(text):
    text = html.unescape(text) # &quot; 같은 엔티티 변환
    return re.sub(r'<[^>]+>', '', text) # <b> 등 HTML 태그 제거

def format_date(date_str): # 날짜 변환
    try:
        dt = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')
        return dt.strftime('%Y-%m-%d %H:%M')
    except ValueError:
        return date_str
    
# 요청
response = requests.get(url, headers=headers, params=params)
print(f"HTTP Status Code: {response.status_code}")

if response.status_code == 200:
    car_news_data = response.json()
    items = car_news_data.get('items', [])
    
    processed_data = []
    for item in items:
        clean_title = clean_text(item['title'])
        clean_desc = clean_text(item['description'])
        clean_date = format_date(item['pubDate']) # 날짜 변환 함수 사용
        news_url = item['link'] 
        
        processed_data.append({
            '제목': clean_title,
            '내용': clean_desc,
            '날짜': clean_date,
            'URL': news_url
        })
        
    # csv 파일로 저장
    with open('naver_news_result.csv', 'w', encoding='utf-8-sig', newline='') as f:
        fieldnames = ['제목', '내용', '날짜', 'URL'] 
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        writer.writeheader()        
        writer.writerows(processed_data)
        
        print("✅ '제목', '내용', '날짜', 'URL' 순으로 CSV 파일이 성공적으로 저장되었습니다!")
else:
    print(f"Error Code: {response.status_code}")