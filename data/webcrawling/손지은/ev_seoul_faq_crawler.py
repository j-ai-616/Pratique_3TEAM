import os
import re
from pathlib import Path
import requests
import pandas as pd
from bs4 import BeautifulSoup

# =====================================
# 설정
# =====================================
PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_XLSX = PROJECT_ROOT / 'data' / 'raw' / 'faq' / 'seoul_ev_faq.xlsx'
OUTPUT_SHEET = "faq"

FAQ_PAGES = [
    {
        "구분": "전기승용,화물,승합 등",
        "url": "https://news.seoul.go.kr/env/archives/517115"
    },
    {
        "구분": "전기이륜",
        "url": "https://news.seoul.go.kr/env/archives/517782"
    }
]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

OUTPUT_XLSX.parent.mkdir(parents=True, exist_ok=True)


# =====================================
# 공통 텍스트 정리
# =====================================
def clean_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\xa0", " ")
    text = text.replace("\r", "\n")

    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    lines = [line for line in lines if line]

    return "\n".join(lines).strip()


def clean_question(text: str) -> str:
    text = clean_text(text)

    # 앞의 Q번호 제거 (예: Q1, Q 2)
    text = re.sub(r"^Q\s*\d+\s*", "", text).strip()

    return text


def clean_answer(text: str) -> str:
    text = clean_text(text)

    stop_words = [
        "추천하기",
        "인쇄",
        "스크랩",
        "페이지 만족도 평가",
        "댓글은 자유롭게 의견을 공유하는 공간입니다",
        "공공누리",
    ]

    for word in stop_words:
        if word in text:
            text = text.split(word)[0].strip()

    return text


# =====================================
# 기존 마지막 번호 확인
# =====================================
def get_last_number(output_path, sheet_name="faq"):
    output_path = Path(output_path)
    if not output_path.exists():
        return 0

    try:
        old_df = pd.read_excel(output_path, sheet_name=sheet_name)
        if old_df.empty or "번호" not in old_df.columns:
            return 0
        return int(old_df["번호"].max())
    except Exception:
        return 0


# =====================================
# 기존 파일과 합쳐서 저장
# =====================================
def append_to_excel(new_df, output_path, sheet_name="faq"):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        try:
            old_df = pd.read_excel(output_path, sheet_name=sheet_name)
            combined_df = pd.concat([old_df, new_df], ignore_index=True)
        except Exception:
            combined_df = new_df.copy()
    else:
        combined_df = new_df.copy()

    # 같은 구분 + 질문 중복 제거
    combined_df = combined_df.drop_duplicates(
        subset=["구분", "질문"],
        keep="first"
    ).reset_index(drop=True)

    combined_df.to_excel(output_path, index=False, sheet_name=sheet_name)
    return combined_df


# =====================================
# HTML 가져오기
# =====================================
def fetch_html(url: str) -> str:
    res = requests.get(url, headers=HEADERS, timeout=20)
    res.raise_for_status()
    return res.text


# =====================================
# qna_list 구조 파싱
# =====================================
def parse_qna_list(qna_list, category):
    rows = []

    q_items = qna_list.select(".qlist")
    a_items = qna_list.select(".alist")

    pair_count = min(len(q_items), len(a_items))

    for i in range(pair_count):
        q_text = q_items[i].get_text("\n", strip=True)
        a_text = a_items[i].get_text("\n", strip=True)

        question = clean_question(q_text)
        answer = clean_answer(a_text)

        if question and answer:
            rows.append({
                "구분": category,
                "질문": question,
                "답": answer
            })

    return rows


# =====================================
# 페이지 전체 파싱
# =====================================
def parse_faq_page(html: str, category: str) -> pd.DataFrame:
    soup = BeautifulSoup(html, "html.parser")

    rows = []

    # 1) 탭 안쪽 FAQ 우선 수집
    move_conts = soup.select(".move-cont")
    for cont in move_conts:
        qna_lists = cont.select(".qna_list")
        for qna_list in qna_lists:
            rows.extend(parse_qna_list(qna_list, category))

    # 2) 일반 FAQ 수집
    qna_lists = soup.select(".qna_list")
    for qna_list in qna_lists:
        rows.extend(parse_qna_list(qna_list, category))

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    # 페이지 내부 중복 제거
    df = df.drop_duplicates(subset=["구분", "질문"], keep="first").reset_index(drop=True)

    return df


# =====================================
# 실행
# =====================================
def main():
    all_new_rows = []

    for page in FAQ_PAGES:
        category = page["구분"]
        url = page["url"]

        print(f"[수집 시작] {category}")

        try:
            html = fetch_html(url)
            df_page = parse_faq_page(html, category)

            print(f" - 추출 개수: {len(df_page)}")
            if not df_page.empty:
                print(df_page.head(3))

            all_new_rows.append(df_page)

        except Exception as e:
            print(f" - 수집 실패: {e}")

    if not all_new_rows:
        print("추출된 데이터가 없습니다.")
        return

    new_df = pd.concat(all_new_rows, ignore_index=True)

    if new_df.empty:
        print("최종 추출 결과가 0건입니다. 저장하지 않고 종료합니다.")
        return

    last_no = get_last_number(OUTPUT_XLSX, OUTPUT_SHEET)
    new_df.insert(1, "번호", range(last_no + 1, last_no + 1 + len(new_df)))

    new_df = new_df[["구분", "번호", "질문", "답"]]

    final_df = append_to_excel(new_df, OUTPUT_XLSX, OUTPUT_SHEET)

    print("\n[저장 완료]")
    print(f"이번 추가 건수: {len(new_df)}")
    print(f"누적 건수: {len(final_df)}")
    print(f"파일 경로: {OUTPUT_XLSX}")


if __name__ == "__main__":
    main()