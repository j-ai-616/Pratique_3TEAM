import os
import re
import html
from pathlib import Path
import requests
import pandas as pd
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")

CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

if not CLIENT_ID or not CLIENT_SECRET:
    raise ValueError("NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 을 .env 파일에 설정하세요.")


def clean_html_text(text: str) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<.*?>", "", text)
    return text.strip()


def search_naver_news(query: str, display: int = 100, start: int = 1, sort: str = "date"):
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET,
    }
    params = {
        "query": query,
        "display": display,
        "start": start,
        "sort": sort,   # sim=정확도순, date=최신순
    }

    response = requests.get(url, headers=headers, params=params, timeout=15)
    response.raise_for_status()
    return response.json()


def collect_news(query: str, max_items: int = 100):
    rows = []
    start = 1

    while len(rows) < max_items and start <= 1000:
        display = min(100, max_items - len(rows))
        data = search_naver_news(query=query, display=display, start=start, sort="date")

        items = data.get("items", [])
        if not items:
            break

        for item in items:
            rows.append({
                "검색어": query,
                "제목": clean_html_text(item.get("title", "")),
                "원문URL": item.get("originallink", ""),
                "네이버뉴스URL": item.get("link", ""),
                "작성일": item.get("pubDate", ""),
                "요약": clean_html_text(item.get("description", "")),
            })

        start += display

    df = pd.DataFrame(rows)

    if not df.empty:
        df = df.drop_duplicates(subset=["제목", "원문URL"]).reset_index(drop=True)

    return df


if __name__ == "__main__":
    query = input("검색어를 입력하세요: ").strip()
    if not query:
        raise ValueError("검색어가 비어 있습니다. 다시 실행해서 검색어를 입력하세요.")

    max_items_input = input("수집할 기사 수를 입력하세요(기본 100): ").strip()
    max_items = int(max_items_input) if max_items_input else 100

    df = collect_news(query=query, max_items=max_items)

    print(df.head())
    print(f"수집 건수: {len(df)}")

    safe_query = re.sub(r'[\\/*?:"<>|]', "_", query)
    output_file = f"naver_news_{safe_query}.xlsx"
    df.to_excel(output_file, index=False)

    print(f"저장 완료: {output_file}")