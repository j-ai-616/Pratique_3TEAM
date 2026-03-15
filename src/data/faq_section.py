import html
import re

import pandas as pd
import streamlit as st


def _clean_display_question(question: str, question_original: str = "") -> str:
    original = str(question_original or "").strip()
    if original:
        return re.sub(r"^\d+\.\s*", "", original).strip()

    cleaned = str(question or "").strip()
    cleaned = re.sub(r"^(?:\[[^\]]+\]\s*)+", "", cleaned)
    cleaned = re.sub(r"^\d+\.\s*", "", cleaned)
    return cleaned.strip()


def render_faq_section(
    faq_data: pd.DataFrame,
    default_group: str | None = None,
    section_title: str = "FAQ",
    section_caption: str | None = None,
) -> None:
    st.subheader(section_title)
    st.caption(
        section_caption
        or "손지은님이 카테고리화한 서울시 전기차 FAQ 자료를 기준으로 질문/답변을 조회합니다."
    )

    if faq_data.empty:
        st.info("표시할 FAQ 데이터가 없습니다.")
        return

    filtered_faq_data = faq_data.copy()

    if default_group:
        filtered_faq_data = filtered_faq_data[
            filtered_faq_data["faq_group"].astype(str).str.strip() == default_group
        ].copy()

    if filtered_faq_data.empty:
        st.warning("선택한 그룹에 해당하는 FAQ가 없습니다.")
        return

    group_list = ["전체"] + sorted(filtered_faq_data["faq_group"].dropna().unique().tolist())
    category_list = ["전체"] + sorted(filtered_faq_data["category"].dropna().unique().tolist())
    tag_list = sorted(
        [value for value in filtered_faq_data["tag"].dropna().astype(str).unique().tolist() if value.strip()]
    )

    filter_column_1, filter_column_2, filter_column_3 = st.columns([1.1, 1.1, 1.8])

    selected_group = default_group or filter_column_1.selectbox("FAQ 구분 선택", group_list)
    if default_group:
        filter_column_1.text_input("FAQ 구분", value=default_group, disabled=True)

    selected_category = filter_column_2.selectbox("세부 카테고리 선택", category_list)
    faq_keyword = filter_column_3.text_input(
        "FAQ 검색",
        value="",
        placeholder="예: 보조금, 신청, 자격, 환수, 공동명의",
    )

    if selected_group != "전체":
        filtered_faq_data = filtered_faq_data[
            filtered_faq_data["faq_group"] == selected_group
        ]

    if selected_category != "전체":
        filtered_faq_data = filtered_faq_data[
            filtered_faq_data["category"] == selected_category
        ]

    if faq_keyword.strip():
        faq_keyword = faq_keyword.strip()
        filtered_faq_data = filtered_faq_data[
            filtered_faq_data["question"].astype(str).str.contains(faq_keyword, case=False, na=False)
            | filtered_faq_data["answer"].astype(str).str.contains(faq_keyword, case=False, na=False)
            | filtered_faq_data["tag"].astype(str).str.contains(faq_keyword, case=False, na=False)
            | filtered_faq_data["question_original"].astype(str).str.contains(faq_keyword, case=False, na=False)
        ]

    st.caption(f"FAQ 검색 결과: {len(filtered_faq_data)}건")

    if tag_list:
        st.caption("태그 목록: " + ", ".join(tag_list))

    if filtered_faq_data.empty:
        st.warning("선택한 조건에 맞는 FAQ가 없습니다.")
        return

    filtered_faq_data = filtered_faq_data.sort_values(
        ["faq_number", "category", "question"],
        na_position="last",
    ).reset_index(drop=True)

    category_tabs = ["전체"] + sorted(filtered_faq_data["category"].dropna().unique().tolist())
    tabs = st.tabs(category_tabs)

    for tab_name, tab in zip(category_tabs, tabs):
        with tab:
            if tab_name == "전체":
                category_view_data = filtered_faq_data
            else:
                category_view_data = filtered_faq_data[
                    filtered_faq_data["category"] == tab_name
                ].reset_index(drop=True)

            if category_view_data.empty:
                st.info("해당 카테고리에 표시할 FAQ가 없습니다.")
                continue

            for _, faq_row in category_view_data.iterrows():
                group_name = str(faq_row.get("faq_group", "기타")).strip()
                category = str(faq_row.get("category", "기타")).strip()
                tag = str(faq_row.get("tag", "")).strip()
                question = str(faq_row.get("question", "질문")).strip()
                question_original = str(faq_row.get("question_original", "")).strip()
                answer = str(faq_row.get("answer", "")).strip()
                faq_number = faq_row.get("faq_number")

                faq_number_text = ""
                if pd.notna(faq_number):
                    try:
                        faq_number_text = str(int(float(faq_number)))
                    except (TypeError, ValueError):
                        faq_number_text = str(faq_number)

                display_question = _clean_display_question(question, question_original) or question

                if faq_number_text:
                    expander_title = f"{faq_number_text}. {display_question}"
                else:
                    expander_title = display_question

                with st.expander(expander_title):
                    meta_parts = [f"구분: {group_name}", f"카테고리: {category}"]
                    if tag:
                        meta_parts.append(f"태그: {tag}")
                    if faq_number_text:
                        meta_parts.append(f"번호: {faq_number_text}")
                    st.caption(" / ".join(meta_parts))

                    safe_answer = html.escape(answer).replace("\r\n", "\n").replace("\n", "<br>")
                    st.markdown(
                        f"<div style='white-space:pre-wrap; line-height:1.7;'>{safe_answer}</div>",
                        unsafe_allow_html=True,
                    )
