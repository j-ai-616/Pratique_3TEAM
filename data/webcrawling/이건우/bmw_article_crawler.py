import math
from pathlib import Path
from typing import List, Dict

import pandas as pd
import requests
from bs4 import BeautifulSoup


PROJECT_ROOT = Path(__file__).resolve().parents[3]

BMW_SEARCH_URL = "https://www.bmw.co.kr/kr/s/article-search"

OUTPUT_DIR = PROJECT_ROOT / "data" / "raw" / "faq"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_XLSX = OUTPUT_DIR / "brand_article_bmw_electric.xlsx"


HEADERS = {
    "User-Agent": "Mozilla/5.0",
}


def fetch_search_page(page: int = 1) -> str:
    """
    BMW Korea 기사 검색 페이지 HTML을 가져옴.

    :param page: 페이지 번호 (1부터 시작이라고 가정)
    """
    params = {
        "language": "ko",
        "searchKey": "전기",
        "hashtags": "",
        "page": page,
    }
    res = requests.get(BMW_SEARCH_URL, headers=HEADERS, params=params, timeout=20)
    res.raise_for_status()
    return res.text


def parse_article_list(html: str) -> List[Dict[str, str]]:
    """
    검색 결과 페이지에서 기사 목록을 파싱.

    실제 DOM 구조에 따라 아래 CSS 선택자를 상황에 맞게 조정해서 사용하면 됨.
    """
    soup = BeautifulSoup(html, "html.parser")
    rows: List[Dict[str, str]] = []

    # 기사 카드 컨테이너 후보
    cards = soup.select(
        ".article-card, .article-tile, .card, .cmp-article__item"
    )
    if not cards:
        # 구조를 못 찾으면 빈 리스트 반환
        return rows

    for card in cards:
        title = ""
        summary = ""
        url = ""

        # 제목
        title_elem = (
            card.select_one(".title, .article-title, h2, h3")
            or card.find("h2")
            or card.find("h3")
        )
        if title_elem:
            title = title_elem.get_text(" ", strip=True)

        # 요약/본문 일부
        summary_elem = (
            card.select_one(".description, .summary, p")
            or card.find("p")
        )
        if summary_elem:
            summary = summary_elem.get_text(" ", strip=True)

        # 링크
        link_elem = card.find("a", href=True)
        if link_elem:
            href = link_elem["href"]
            if href.startswith("/"):
                url = f"https://www.bmw.co.kr{href}"
            else:
                url = href

        if not title and not url:
            continue

        rows.append(
            {
                "브랜드": "BMW",
                "검색어": "전기",
                "제목": title,
                "요약": summary,
                "URL": url,
            }
        )

    return rows


def collect_bmw_articles(max_pages: int = 5) -> List[Dict[str, str]]:
    """
    여러 페이지를 돌면서 전기 관련 기사 목록 수집.
    """
    all_rows: List[Dict[str, str]] = []

    for page in range(1, max_pages + 1):
        try:
            html = fetch_search_page(page=page)
        except Exception as e:
            print(f"[경고] BMW 검색 페이지 {page} 로드 실패: {e}")
            break

        rows = parse_article_list(html)
        if not rows:
            # 더 이상 결과가 없으면 중단
            break

        print(f"- 페이지 {page} 건수: {len(rows)}")
        all_rows.extend(rows)

    return all_rows


def save_to_excel(rows: List[Dict[str, str]], output_path: Path) -> pd.DataFrame:
    new_df = pd.DataFrame(rows)
    if new_df.empty:
        return new_df

    if output_path.exists():
        old_df = pd.read_excel(output_path)
        combined = pd.concat([old_df, new_df], ignore_index=True)
    else:
        combined = new_df.copy()

    combined = combined.drop_duplicates(
        subset=["브랜드", "제목", "URL"], keep="first"
    ).reset_index(drop=True)
    combined.to_excel(output_path, index=False)
    return combined


def main():
    rows = collect_bmw_articles(max_pages=5)
    if not rows:
        print("BMW 전기 관련 기사가 수집되지 않았습니다. 페이지 구조나 파라미터를 다시 확인하세요.")
        return

    final_df = save_to_excel(rows, OUTPUT_XLSX)
    print("[BMW 전기 관련 기사 수집 완료]")
    print(f"- 이번 추가 건수: {len(rows)}")
    print(f"- 누적 건수: {len(final_df)}")
    print(f"- 저장 위치: {OUTPUT_XLSX}")


if __name__ == "__main__":
    main()

