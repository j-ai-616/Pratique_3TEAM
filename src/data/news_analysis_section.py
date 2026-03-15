from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st


def render_news_analysis_section(
    news_keyword_data: pd.DataFrame,
    wordcloud_path: Path | None = None,
) -> None:
    st.subheader("뉴스 키워드 분석")
    st.caption("'전기차 보조금' 키워드로 정리한 뉴스 분석 결과 파일을 그대로 활용해 키워드 빈도와 워드클라우드를 함께 보여줍니다.")

    if news_keyword_data.empty:
        st.info("표시할 뉴스 키워드 데이터가 없습니다.")
        return

    max_keyword_count = min(30, len(news_keyword_data))
    top_n = st.slider(
        "상위 키워드 개수",
        min_value=5,
        max_value=max_keyword_count,
        value=min(15, max_keyword_count),
        step=1,
    )

    display_data = news_keyword_data.head(top_n).copy()

    metric_column_1, metric_column_2, metric_column_3 = st.columns(3)
    metric_column_1.metric("전체 키워드 수", f"{len(news_keyword_data):,}")
    metric_column_2.metric("표시 키워드 수", f"{len(display_data):,}")
    metric_column_3.metric("최다 빈도", f"{int(display_data['빈도수'].max()):,}")

    chart_column, table_column = st.columns([1.8, 1.1])

    with chart_column:
        st.markdown("### 키워드 별 빈도 막대그래프")
        chart_data = display_data.set_index("키워드")["빈도수"]
        st.bar_chart(chart_data, use_container_width=True)

    with table_column:
        st.markdown("### 키워드 빈도표")
        st.dataframe(display_data, use_container_width=True, hide_index=True)

    st.markdown("### 워드클라우드")
    if wordcloud_path is not None and wordcloud_path.exists():
        st.image(str(wordcloud_path), use_container_width=True)
    else:
        st.info("wordcloud.png 파일을 찾지 못해 이미지를 표시하지 못했습니다.")
