import os
import re
from pathlib import Path
from collections import Counter

import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from konlpy.tag import Okt


# =========================
# 1. 설정
# =========================
BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "naver_news_전기차 보조금.xlsx"
TEXT_COLUMN = "요약"
TOP_N = 60

# 맥 기본 내장 한글 폰트 자동 탐색
FONT_CANDIDATES = [
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",                  # 가장 추천
    "/System/Library/Fonts/Supplemental/AppleGothic.ttf",         # 대체
]

FONT_PATH = None
for path in FONT_CANDIDATES:
    if os.path.exists(path):
        FONT_PATH = path
        break

if FONT_PATH is None:
    raise FileNotFoundError(
        "사용 가능한 맥 한글 폰트를 찾지 못했습니다.\n"
        "확인 경로:\n- " + "\n- ".join(FONT_CANDIDATES)
    )

# 제외할 불용어
STOPWORDS = {
    "정부", "지원", "기자", "뉴스", "관련", "통해", "위해",
    "대한", "이번", "올해", "지난해", "현재", "가운데", "정도", "경우", "이후",
    "때문", "기준", "이상", "이하", "지난", "최근", "모두", "해당", "있다", "없다",
    "한다", "됐다", "되는", "하며", "또한", "그리고", "에서", "으로", "이다",
    "것으로", "수", "것", "등", "더", "및",
    "전기차", "보조금"   # 핵심 키워드라 제외하지 않고 싶으면 이 두 단어 지우면 됨
}

# 저장 파일명
OUTPUT_FREQ_FILE = BASE_DIR / "keyword_frequency.xlsx"
OUTPUT_WORDCLOUD_FILE = BASE_DIR / "wordcloud.png"


# =========================
# 2. 데이터 읽기
# =========================
df = pd.read_excel(INPUT_FILE)

if TEXT_COLUMN not in df.columns:
    raise ValueError(f"'{TEXT_COLUMN}' 컬럼이 없습니다. 현재 컬럼: {list(df.columns)}")

texts = df[TEXT_COLUMN].dropna().astype(str).tolist()

if not texts:
    raise ValueError("요약 컬럼에 텍스트가 없습니다.")


# =========================
# 3. 전처리
# =========================
def clean_text(text: str) -> str:
    text = re.sub(r"<.*?>", " ", text)                    # HTML 태그 제거
    text = re.sub(r"[^가-힣0-9A-Za-z\s]", " ", text)      # 특수문자 제거
    text = re.sub(r"\s+", " ", text).strip()             # 공백 정리
    return text


cleaned_texts = [clean_text(t) for t in texts]


# =========================
# 4. 형태소 분석 후 키워드 추출
# =========================
okt = Okt()
keywords = []

for text in cleaned_texts:
    nouns = okt.nouns(text)
    filtered = [
        word for word in nouns
        if len(word) >= 2 and word not in STOPWORDS
    ]
    keywords.extend(filtered)

if not keywords:
    raise ValueError("추출된 키워드가 없습니다. 불용어나 길이 조건을 완화해봐.")

keyword_counts = Counter(keywords)
top_keywords = keyword_counts.most_common(TOP_N)


# =========================
# 5. 키워드 빈도표 저장
# =========================
keyword_df = pd.DataFrame(top_keywords, columns=["키워드", "빈도수"])
keyword_df.to_excel(OUTPUT_FREQ_FILE, index=False)

print("\n[상위 키워드 20개]")
print(keyword_df.head(20))


# =========================
# 6. 워드클라우드 생성
# =========================
# 발표용으로 좀 더 보기 좋게 옵션 조정
wc = WordCloud(
    font_path=FONT_PATH,
    width=1600,
    height=1000,
    background_color="white",
    max_words=100,
    prefer_horizontal=0.9,   # 가로 배치 위주
    collocations=False,      # 중복 조합 억제
    margin=10,               # 단어 간 여백
    relative_scaling=0.35,   # 지나친 크기 차이 완화
    min_font_size=12,
    colormap="viridis"       # 발표용으로 깔끔한 색감
).generate_from_frequencies(dict(top_keywords))


# =========================
# 7. 출력
# =========================
plt.figure(figsize=(16, 10), facecolor="white")
plt.imshow(wc, interpolation="bilinear")
plt.axis("off")
plt.title("전기차 보조금 뉴스 키워드 워드클라우드", fontsize=20, pad=20)
plt.tight_layout()
plt.savefig(OUTPUT_WORDCLOUD_FILE, dpi=300, bbox_inches="tight", facecolor="white")
plt.show()

print("\n저장 완료:")
print(f"- {OUTPUT_FREQ_FILE}")
print(f"- {OUTPUT_WORDCLOUD_FILE}")
print(f"- 사용 폰트: {FONT_PATH}")
