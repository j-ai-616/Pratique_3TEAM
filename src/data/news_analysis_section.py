#######################################################################################################
#### 6번 탭 구현 - 뉴스 기사 분석

# 이 스크립트는 Streamlit 기반 전기차 정보 포털에서
# "뉴스 기사 분석" 화면을 구성하는 역할을 합니다.
#
# 이 스크립트의 핵심 기능은 다음과 같습니다.
#
# 1) 뉴스 키워드 분석 결과 표시
#    - 미리 정리된 뉴스 키워드 빈도 데이터(DataFrame)를 받아
#      상위 키워드 개수를 선택할 수 있게 하고,
#      해당 범위의 키워드 빈도 결과를 화면에 표시합니다.
#
# 2) 핵심 지표(metric) 출력
#    - 전체 키워드 수
#    - 현재 화면에 표시 중인 키워드 수
#    - 현재 선택 범위 안에서의 최다 빈도
#    를 숫자 카드(metric) 형태로 보여줍니다.
#
# 3) 시각화 출력
#    - 키워드별 빈도를 막대그래프로 보여줍니다.
#    - 같은 데이터를 표(DataFrame) 형태로도 함께 보여줍니다.
#
# 4) 워드클라우드 이미지 출력
#    - 프로젝트 내부에 저장된 워드클라우드 이미지 파일 경로를 받아
#      해당 이미지를 화면에 보여줍니다.
#    - 이미지 파일이 없으면 안내 문구를 대신 출력합니다.
#
# 이 스크립트는 직접 뉴스 원문을 수집하거나 키워드를 추출하지는 않습니다.
# 즉, "뉴스 분석 결과를 화면에 렌더링하는 역할"에 집중된 Streamlit 화면 스크립트입니다.
#
# 이 스크립트와 상호작용하는 주요 스크립트는 다음과 같습니다.
#
# 1) src/db/query_data.py
#    - 뉴스 키워드 분석 결과 파일을 읽어 news_keyword_data DataFrame으로 준비합니다.
#    - 또한 resolve_news_wordcloud_path() 함수를 통해
#      워드클라우드 이미지 파일의 실제 경로를 찾아 반환합니다.
#    - 이 스크립트는 query_data.py가 준비한 데이터와 이미지 경로를 받아 화면에 출력합니다.
#
# 2) src/app/main_app.py
#    - 전체 Streamlit 앱의 진입점이며 메뉴 라우팅을 담당합니다.
#    - load_dashboard_data()에서 뉴스 키워드 데이터를 미리 불러온 뒤,
#      사용자가 "뉴스 기사 분석" 메뉴를 선택하면 render_news_page()를 호출합니다.
#
# 전체 흐름은 보통 다음과 같습니다.
#
# query_data.py
#   -> 뉴스 키워드 데이터 로드
#   -> 워드클라우드 이미지 경로 확인
# main_app.py
#   -> load_dashboard_data()에 뉴스 데이터 저장
#   -> 뉴스 메뉴 선택 시 render_news_page() 호출
# news_analysis_section.py (현재 스크립트)
#   -> 키워드 지표, 차트, 표, 워드클라우드 화면 구성
#
# 정리하면,
# 이 스크립트는 "미리 분석된 뉴스 키워드 결과를 사용자에게 시각적으로 보여주는
# 뉴스 분석 결과 화면 렌더링 전담 스크립트"입니다.

from __future__ import annotations

# 파일 경로(Path 객체)를 다루기 위한 표준 라이브러리입니다.
# 워드클라우드 이미지 파일 경로를 타입 힌트로 표현하고 존재 여부를 검사할 때 사용합니다.
from pathlib import Path

# 표 형태 데이터(DataFrame)를 다루기 위한 pandas 라이브러리입니다.
# 뉴스 키워드 데이터는 DataFrame 형태로 전달되며,
# head(), copy(), set_index() 등의 처리를 위해 사용합니다.
import pandas as pd

# Streamlit 화면 구성을 위한 라이브러리입니다.
# 제목, 캡션, 슬라이더, metric, 차트, 표, 이미지 등을 출력할 때 사용합니다.
import streamlit as st

# 뉴스 워드클라우드 이미지 파일의 경로를 찾아주는 함수입니다.
# 보통 query_data.py에서 프로젝트 내부 파일 위치를 확인한 뒤 Path 객체를 반환합니다.
from src.db.query_data import resolve_news_wordcloud_path


def render_news_analysis_section(
    news_keyword_data: pd.DataFrame,
    wordcloud_path: Path | None = None,
) -> None:
    # 뉴스 키워드 분석 영역의 소제목을 출력합니다.
    st.subheader("뉴스 키워드 분석")

    # 이 영역이 어떤 데이터를 보여주는지 설명하는 캡션을 출력합니다.
    st.caption("'전기차 보조금' 키워드로 정리한 뉴스 분석 결과 파일을 그대로 활용해 키워드 빈도와 워드클라우드를 함께 보여줍니다.")

    # 전달받은 뉴스 키워드 데이터가 비어 있으면
    # 안내 문구를 출력하고 함수 실행을 종료합니다.
    if news_keyword_data.empty:
        st.info("표시할 뉴스 키워드 데이터가 없습니다.")
        return

    # 사용자가 슬라이더로 선택할 수 있는 최대 키워드 개수를 계산합니다.
    # 너무 많은 키워드를 한 번에 그리면 화면이 복잡해질 수 있으므로 최대 30개까지만 허용합니다.
    max_keyword_count = min(30, len(news_keyword_data))

    # 사용자가 화면에 표시할 상위 키워드 개수를 선택할 수 있도록 슬라이더를 출력합니다.
    # 최소 5개, 최대 max_keyword_count개까지 선택할 수 있습니다.
    # 기본값은 15개 또는 전체 개수 중 더 작은 값입니다.
    top_n = st.slider(
        "상위 키워드 개수",
        min_value=5,
        max_value=max_keyword_count,
        value=min(15, max_keyword_count),
        step=1,
    )

    # 선택한 상위 키워드 개수(top_n)만큼만 잘라서 화면 표시용 DataFrame을 만듭니다.
    # 원본 데이터 훼손을 막기 위해 copy()를 사용합니다.
    display_data = news_keyword_data.head(top_n).copy()

    # 상단 핵심 지표를 3개의 컬럼으로 나누어 배치합니다.
    metric_column_1, metric_column_2, metric_column_3 = st.columns(3)

    # 전체 키워드 수를 metric 형태로 출력합니다.
    metric_column_1.metric("전체 키워드 수", f"{len(news_keyword_data):,}")

    # 현재 화면에 표시 중인 키워드 수를 metric 형태로 출력합니다.
    metric_column_2.metric("표시 키워드 수", f"{len(display_data):,}")

    # 현재 표시 범위(display_data) 안에서 가장 큰 빈도수를 metric 형태로 출력합니다.
    # '빈도수' 컬럼의 최대값을 정수형으로 바꿔 보여줍니다.
    metric_column_3.metric("최다 빈도", f"{int(display_data['빈도수'].max()):,}")

    # 차트 영역과 표 영역을 좌우 2개 컬럼으로 나누어 배치합니다.
    # 왼쪽 차트 영역을 더 넓게 보여주기 위해 [1.8, 1.1] 비율을 사용합니다.
    chart_column, table_column = st.columns([1.8, 1.1])

    # 왼쪽 컬럼에는 막대그래프를 출력합니다.
    with chart_column:
        # 막대그래프 영역 제목을 출력합니다.
        st.markdown("### 키워드별 빈도 막대그래프")

        # '키워드' 컬럼을 인덱스로, '빈도수' 컬럼을 값으로 가지는 Series를 만듭니다.
        # Streamlit의 st.bar_chart()에 넣기 좋은 형태로 가공하는 과정입니다.
        chart_data = display_data.set_index("키워드")["빈도수"]

        # 키워드별 빈도 막대그래프를 출력합니다.
        # use_container_width=True 옵션으로 화면 너비에 맞춰 넓게 표시합니다.
        st.bar_chart(chart_data, use_container_width=True)

    # 오른쪽 컬럼에는 표 형태의 빈도표를 출력합니다.
    with table_column:
        # 표 영역 제목을 출력합니다.
        st.markdown("### 키워드 빈도표")

        # 선택된 상위 키워드 데이터(display_data)를 그대로 표 형태로 출력합니다.
        # hide_index=True 로 인덱스 열은 숨깁니다.
        st.dataframe(display_data, use_container_width=True, hide_index=True)

    # 워드클라우드 영역 제목을 출력합니다.
    st.markdown("### 워드클라우드")

    # 워드클라우드 이미지 경로가 None이 아니고, 실제 파일이 존재하면 이미지를 화면에 출력합니다.
    if wordcloud_path is not None and wordcloud_path.exists():
        # 워드클라우드 이미지를 화면에 출력합니다.
        # use_container_width=True 로 화면 너비에 맞게 반응형으로 표시합니다.
        st.image(str(wordcloud_path), use_container_width=True)
    else:
        # 이미지 파일을 찾지 못했을 경우 안내 문구를 출력합니다.
        st.info("wordcloud.png 파일을 찾지 못해 이미지를 표시하지 못했습니다.")


def render_news_page(news_keyword_data: pd.DataFrame) -> None:
    # 뉴스 기사 분석 페이지의 상단 제목을 출력합니다.
    st.header("뉴스 기사 분석")

    # 실제 뉴스 분석 화면을 구성하는 공통 렌더링 함수를 호출합니다.
    # 이때 news_keyword_data는 메인 앱이나 query_data.py에서 미리 준비된 DataFrame이며,
    # wordcloud_path는 resolve_news_wordcloud_path()를 통해 자동으로 확인된 이미지 파일 경로입니다.
    render_news_analysis_section(
        news_keyword_data=news_keyword_data,
        wordcloud_path=resolve_news_wordcloud_path(),
    )