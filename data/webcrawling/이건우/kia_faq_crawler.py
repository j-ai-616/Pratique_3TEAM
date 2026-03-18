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

KIA_FAQ_URL = "https://www.kia.com/kr/customer-service/center/faq"

OUTPUT_DIR = PROJECT_ROOT / "data" / "raw" / "faq"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_XLSX = OUTPUT_DIR / "brand_faq_kia.xlsx"


def create_driver(headless: bool = True) -> webdriver.Chrome:
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,900")
    options.add_argument("--disable-gpu")

    return webdriver.Chrome(options=options)


def collect_kia_faq(driver: webdriver.Chrome) -> List[Dict[str, str]]:
    """
    기아 FAQ 페이지에서 FAQ를 수집.

    - 기본 구조: 카테고리 탭/셀렉트 + 질문/답변 리스트
    - 실제 DOM 구조에 따라 아래 선택자를 상황에 맞게 조정하면서 사용하면 됨.
    """
    driver.get(KIA_FAQ_URL)

    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    time.sleep(2)

    rows: List[Dict[str, str]] = []

    # 1) 카테고리 탭/버튼이 있다면 전부 클릭해보면서 수집
    # (예: "전체, 차량, 구매, 정비, 기타" 등)
    # 실제 HTML 구조를 보고 아래 selector를 맞춰줘야 한다.
    try:
        category_buttons = driver.find_elements(
            By.CSS_SELECTOR,
            ".tab-list button, .tab-list a, .faq-category button, .faq-category a",
        )
    except Exception:
        category_buttons = []

    if not category_buttons:
        # 카테고리를 못 찾으면 전체 페이지에서 FAQ만 긁어온다.
        category_buttons = [None]

    seen_pairs = set()

    for btn in category_buttons:
        category_name = ""

        # 카테고리 버튼이 있는 경우 클릭해서 해당 탭의 FAQ를 로딩
        if btn is not None:
            try:
                category_name = btn.text.strip()
                if not category_name:
                    category_name = "기타"
                btn.click()
                time.sleep(1.5)
            except Exception:
                # 클릭 실패 시 그냥 넘어감
                pass

        # 2) 현재 화면에 보이는 FAQ 블록을 수집
        # 기아 사이트는 DOM 구조가 복잡할 수 있으므로, 최대한 범용적인 선택자를 사용
        faq_items = driver.find_elements(
            By.CSS_SELECTOR,
            ".faq-list li, .faq-item, .accordion-item",
        )

        for item in faq_items:
            try:
                q = ""
                a = ""

                # 질문 후보
                q_elems = item.find_elements(
                    By.CSS_SELECTOR,
                    ".tit, .question, .faq-question, button, h3, h4",
                )
                for qe in q_elems:
                    text = qe.text.strip()
                    if text:
                        q = text
                        break

                # 답변 후보
                a_elems = item.find_elements(
                    By.CSS_SELECTOR,
                    ".txt, .answer, .faq-answer, .cont, p, div",
                )
                for ae in a_elems:
                    text = ae.text.strip()
                    if text and text != q:
                        a = text
                        break

                if not q:
                    continue

                key = (category_name, q)
                if key in seen_pairs:
                    continue
                seen_pairs.add(key)

                rows.append(
                    {
                        "브랜드": "KIA",
                        "카테고리": category_name,
                        "질문": q,
                        "답": a,
                    }
                )
            except Exception:
                continue

    return rows


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
        subset=["브랜드", "카테고리", "질문"], keep="first"
    ).reset_index(drop=True)
    combined.to_excel(output_path, index=False)
    return combined


def main():
    driver = create_driver(headless=True)
    try:
        rows = collect_kia_faq(driver)
        if not rows:
            print("기아 FAQ가 수집되지 않았습니다. 선택자나 페이지 구조를 다시 확인하세요.")
            return

        final_df = save_to_excel(rows, OUTPUT_XLSX)
        print("[KIA FAQ 수집 완료]")
        print(f"- 이번 추가 건수: {len(rows)}")
        print(f"- 누적 건수: {len(final_df)}")
        print(f"- 저장 위치: {OUTPUT_XLSX}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()

