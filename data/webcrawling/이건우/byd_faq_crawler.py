import os
import time
from pathlib import Path
from typing import List, Dict

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


PROJECT_ROOT = Path(__file__).resolve().parents[3]

# BYD FAQ 페이지 URL
BYD_FAQ_URL = "https://www.reverautomotive.com/en/faq"

# 출력 경로 설정 (브랜드별 FAQ 형식에 맞게 엑셀 저장)
OUTPUT_DIR = PROJECT_ROOT / "data" / "raw" / "faq"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_XLSX = OUTPUT_DIR / "brand_faq_byd.xlsx"


def create_driver(headless: bool = True) -> webdriver.Chrome:
    """크롬 드라이버 생성"""
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,800")
    options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(options=options)
    return driver


def collect_byd_faq(driver: webdriver.Chrome) -> List[Dict[str, str]]:
    """
    BYD FAQ 페이지에서 Q/A 텍스트를 수집.

    주의: 이 함수는 페이지 구조가 바뀌면 동작이 달라질 수 있음.
    크롬 개발자도구로 실제 FAQ 항목의 태그/클래스를 확인한 뒤
    아래 선택자 부분을 필요에 맞게 수정해서 쓰면 된다.
    """
    driver.get(BYD_FAQ_URL)

    # 기본 로딩 대기
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    time.sleep(2)

    rows: List[Dict[str, str]] = []

    # 1) FAQ 섹션 컨테이너를 최대한 범용적으로 탐색
    #    - 실제 구조에 맞게 CSS 선택자를 조정해서 사용
    possible_sections = driver.find_elements(By.XPATH, "//section[contains(., 'FAQs') or contains(., 'FAQ')]")
    if not possible_sections:
        # 섹션을 못 찾는 경우, 페이지 전체에서 후보 요소를 찾도록 fallback
        container = driver.find_element(By.TAG_NAME, "body")
    else:
        container = possible_sections[0]

    # 2) 아코디언/FAQ 카드 단위 요소 찾기
    #    여기서는 자주 쓰이는 클래스명을 여러 개 시도해보는 방식으로 구현
    item_selectors = [
        ".accordion-item",
        ".faq-item",
        ".faq-card",
        ".accordion__item",
    ]

    faq_items = []
    for selector in item_selectors:
        faq_items = container.find_elements(By.CSS_SELECTOR, selector)
        if faq_items:
            break

    # 만약 위 선택자로도 못 찾으면, 제목에 '?' 가 들어간 요소를 기준으로 추출 시도
    if not faq_items:
        question_like = container.find_elements(By.XPATH, ".//*[contains(text(), '?')]")
        for elem in question_like:
            try:
                q = elem.text.strip()
                if not q:
                    continue

                # 답변은 질문 부모/형제 영역에서 첫 번째 블록 텍스트를 찾는 방식으로 시도
                parent = elem.find_element(By.XPATH, "./ancestor-or-self::*[position()<=3][last()]")
                answer_elem = None
                for tag in ["p", "div"]:
                    cand = parent.find_elements(By.TAG_NAME, tag)
                    # 질문 텍스트와는 다른 첫 번째 블록을 답변으로 가정
                    for c in cand:
                        text = c.text.strip()
                        if text and text != q:
                            answer_elem = c
                            break
                    if answer_elem:
                        break

                answer_text = answer_elem.text.strip() if answer_elem else ""
                rows.append(
                    {
                        "브랜드": "BYD",
                        "카테고리": "",
                        "질문": q,
                        "답": answer_text,
                    }
                )
            except Exception:
                continue

        return rows

    # 3) 카드 내부에서 질문/답변 요소 찾기
    for item in faq_items:
        try:
            # 자주 쓰이는 제목/내용 클래스들을 시도
            q = ""
            a = ""

            # 질문 후보
            question_selectors = [
                ".accordion-header",
                ".accordion-title",
                ".faq-question",
                "h2",
                "h3",
                "button",
            ]
            for qs in question_selectors:
                elems = item.find_elements(By.CSS_SELECTOR, qs)
                if elems:
                    q = elems[0].text.strip()
                    if q:
                        break

            # 답변 후보
            answer_selectors = [
                ".accordion-body",
                ".accordion-content",
                ".faq-answer",
                "p",
                "div",
            ]
            for asel in answer_selectors:
                elems = item.find_elements(By.CSS_SELECTOR, asel)
                # 질문 텍스트와 똑같지 않은 첫 번째 블록을 답변으로 사용
                for e in elems:
                    text = e.text.strip()
                    if text and text != q:
                        a = text
                        break
                if a:
                    break

            if q:
                rows.append(
                    {
                        "브랜드": "BYD",
                        "카테고리": "",
                        "질문": q,
                        "답": a,
                    }
                )
        except Exception:
            continue

    return rows


def save_to_excel(rows: List[Dict[str, str]], output_path: Path) -> pd.DataFrame:
    """기존 파일이 있으면 이어붙이고, 없으면 새로 생성"""
    new_df = pd.DataFrame(rows)
    if new_df.empty:
        return new_df

    if output_path.exists():
        old_df = pd.read_excel(output_path)
        combined = pd.concat([old_df, new_df], ignore_index=True)
    else:
        combined = new_df.copy()

    combined = combined.drop_duplicates(
        subset=["브랜드", "카테고리", "질문"], keep="first"
    ).reset_index(drop=True)

    combined.to_excel(output_path, index=False)
    return combined


def main():
    driver = create_driver(headless=True)

    try:
        rows = collect_byd_faq(driver)
        if not rows:
            print("수집된 FAQ가 없습니다. 선택자나 페이지 구조를 다시 확인하세요.")
            return

        final_df = save_to_excel(rows, OUTPUT_XLSX)
        print(f"[BYD FAQ 수집 완료]")
        print(f"- 이번 추가 건수: {len(rows)}")
        print(f"- 누적 건수: {len(final_df)}")
        print(f"- 저장 위치: {OUTPUT_XLSX}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()

