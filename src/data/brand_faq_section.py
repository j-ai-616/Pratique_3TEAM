# 이 스크립트는 Streamlit 기반 전기차 FAQ 화면을 구성하는 역할을 합니다.
# 크게 두 종류의 FAQ 화면을 담당합니다.
# 1) 서울시 전기차 FAQ 화면
#    - FAQ 그룹, 세부 카테고리, 검색어를 기준으로 질문/답변을 조회할 수 있습니다.
#    - 질문 앞 번호를 표시할 수 있도록 설계되어 있습니다.
# 2) 제조사(브랜드)별 전기차 FAQ 화면
#    - 브랜드별 탭을 만들고, 각 브랜드 안에서 세부 카테고리와 검색어로 FAQ를 조회할 수 있습니다.
#    - 브랜드 FAQ는 질문 앞 번호를 표시하지 않도록 설계되어 있습니다.
#
# 또한 이 스크립트는 다음과 같은 보조 기능도 포함합니다.
# - 질문 문자열 앞의 번호나 불필요한 접두어를 정리하는 기능
# - FAQ 답변을 HTML 안전 문자열로 변환하여 화면에 출력하는 기능
# - Streamlit 탭 스타일(CSS)을 적용하여 브랜드 탭 글자 크기를 키우는 기능


# HTML 특수문자 이스케이프 처리를 위한 표준 라이브러리입니다.
# 예: <, >, & 같은 문자가 답변 본문에 들어 있어도 화면이 깨지지 않도록 안전하게 변환할 때 사용합니다.
import html

# 정규표현식을 사용하기 위한 표준 라이브러리입니다.
# 질문 문자열 앞의 번호(예: "1. 질문")나 특정 패턴을 제거할 때 사용합니다.
import re

# 표 형태 데이터(DataFrame)를 다루기 위한 pandas 라이브러리입니다.
# FAQ 데이터가 DataFrame 형태로 전달되므로 필터링, 정렬, 결측치 처리 등에 사용합니다.
import pandas as pd

# Streamlit 화면 구성을 위한 라이브러리입니다.
# 제목, 캡션, 탭, expander, selectbox, text_input 등을 화면에 출력할 때 사용합니다.
import streamlit as st


def _clean_display_question(question: str, question_original: str = "") -> str:
    # question_original 값이 있으면 문자열로 변환한 뒤 앞뒤 공백을 제거합니다.
    original = str(question_original or "").strip()

    # 원본 질문(question_original)이 비어 있지 않으면,
    # 질문 맨 앞에 붙은 번호 패턴(예: "1. ", "23. ")을 제거한 뒤 반환합니다.
    if original:
        return re.sub(r"^\d+\.\s*", "", original).strip()

    # 원본 질문이 없으면 question 값을 기준으로 문자열 정리를 수행합니다.
    cleaned = str(question or "").strip()

    # 질문 앞에 [전기승용], [보조금] 같은 대괄호 접두어가 여러 개 붙어 있을 경우 제거합니다.
    # 예: "[전기차] [보조금] 질문내용" -> "질문내용"
    cleaned = re.sub(r"^(?:\[[^\]]+\]\s*)+", "", cleaned)

    # 질문 맨 앞의 번호 패턴(예: "1. 질문")을 제거합니다.
    cleaned = re.sub(r"^\d+\.\s*", "", cleaned)

    # 최종 정리된 질문 문자열을 반환합니다.
    return cleaned.strip()


def render_faq_section(
    faq_data: pd.DataFrame,
    default_group: str | None = None,
    section_title: str = "FAQ",
    section_caption: str | None = None,
    show_question_number: bool = True,
) -> None:
    # FAQ 섹션의 소제목을 출력합니다.
    st.subheader(section_title)

    # 섹션 설명 문구를 출력합니다.
    # section_caption 값이 있으면 그 값을 사용하고,
    # 없으면 기본 안내 문구를 사용합니다.
    st.caption(
        section_caption
        or "서울시 전기차 FAQ 자료를 기준으로 질문/답변을 조회합니다."
    )

    # 전달받은 FAQ 데이터가 비어 있으면 안내 문구를 출력하고 함수 실행을 종료합니다.
    if faq_data.empty:
        st.info("표시할 FAQ 데이터가 없습니다.")
        return

    # 원본 데이터 훼손을 방지하기 위해 복사본을 만들어 이후 필터링 작업에 사용합니다.
    filtered_faq_data = faq_data.copy()

    # default_group 값이 존재하고, 데이터에 faq_group 컬럼이 있을 경우
    # 해당 그룹에 해당하는 데이터만 먼저 필터링합니다.
    if default_group and "faq_group" in filtered_faq_data.columns:
        filtered_faq_data = filtered_faq_data[
            filtered_faq_data["faq_group"].astype(str).str.strip() == default_group
        ].copy()

    # 그룹 필터링 결과 데이터가 비어 있으면 경고 문구를 출력하고 종료합니다.
    if filtered_faq_data.empty:
        st.warning("선택한 그룹에 해당하는 FAQ가 없습니다.")
        return

    # faq_group 컬럼이 실제로 존재하는지 여부를 미리 저장합니다.
    # 이후 그룹 선택 UI를 보여줄지 말지 결정할 때 사용합니다.
    has_group_column = "faq_group" in filtered_faq_data.columns

    # 필터 UI를 3개의 컬럼 영역으로 나누어 배치합니다.
    # 1열: FAQ 그룹 선택
    # 2열: 세부 카테고리 선택
    # 3열: 검색어 입력
    filter_column_1, filter_column_2, filter_column_3 = st.columns([1.1, 1.1, 1.8])

    # faq_group 컬럼이 존재하면 그룹 선택 박스를 화면에 출력합니다.
    if has_group_column:
        # "전체" 항목 + 실제 faq_group 고유값 목록을 정렬하여 선택 리스트를 구성합니다.
        group_list = ["전체"] + sorted(filtered_faq_data["faq_group"].dropna().unique().tolist())

        # default_group 값이 있으면 해당 값을 선택값으로 사용하고,
        # 없으면 사용자가 selectbox에서 직접 선택하도록 합니다.
        selected_group = default_group or filter_column_1.selectbox("FAQ 구분 선택", group_list)

        # default_group 값이 주어진 경우에는
        # 선택 UI 대신 고정된 텍스트 입력창(disabled)을 보여주어 현재 그룹을 안내합니다.
        if default_group:
            filter_column_1.text_input("FAQ 구분", value=default_group, disabled=True)
    else:
        # faq_group 컬럼이 없으면 그룹 선택은 사용하지 않으므로 "전체"로 고정합니다.
        selected_group = "전체"

        # 첫 번째 필터 컬럼은 비워 둡니다.
        filter_column_1.empty()

    # 세부 카테고리 선택 목록을 생성합니다.
    # "전체" 항목 + category 컬럼의 고유값을 정렬하여 사용합니다.
    category_list = ["전체"] + sorted(filtered_faq_data["category"].dropna().unique().tolist())

    # 카테고리 선택 박스를 화면에 출력합니다.
    selected_category = filter_column_2.selectbox("세부 카테고리 선택", category_list)

    # FAQ 검색어 입력창을 화면에 출력합니다.
    faq_keyword = filter_column_3.text_input(
        "FAQ 검색",
        value="",
        placeholder="예: 충전, 보조금, 배터리, 정비",
    )

    # faq_group 컬럼이 있고, 사용자가 "전체"가 아닌 특정 그룹을 선택한 경우
    # 해당 그룹의 데이터만 남기도록 필터링합니다.
    if has_group_column and selected_group != "전체":
        filtered_faq_data = filtered_faq_data[
            filtered_faq_data["faq_group"] == selected_group
        ]

    # 사용자가 "전체"가 아닌 특정 세부 카테고리를 선택한 경우
    # 해당 카테고리의 데이터만 남기도록 필터링합니다.
    if selected_category != "전체":
        filtered_faq_data = filtered_faq_data[
            filtered_faq_data["category"] == selected_category
        ]

    # 검색어가 입력된 경우에만 검색 필터를 수행합니다.
    if faq_keyword.strip():
        # 검색어 앞뒤 공백을 제거합니다.
        faq_keyword = faq_keyword.strip()

        # 기본 검색 대상 컬럼 목록입니다.
        # 질문, 답변, 원본 질문을 검색 대상으로 사용합니다.
        search_columns = ["question", "answer", "question_original"]

        # tag 컬럼이 있으면 검색 대상에 추가합니다.
        if "tag" in filtered_faq_data.columns:
            search_columns.append("tag")

        # 검색 결과를 누적할 불리언 마스크입니다.
        # 처음에는 False로 시작하고,
        # 각 컬럼에서 검색어가 포함되는 행을 OR 연산으로 누적합니다.
        search_mask = False

        # 검색 대상 컬럼들을 순회하면서 검색어 포함 여부를 검사합니다.
        for column_name in search_columns:
            search_mask = (
                search_mask
                | filtered_faq_data[column_name].astype(str).str.contains(
                    faq_keyword, case=False, na=False
                )
            )

        # 최종 검색 마스크를 이용하여 조건에 맞는 행만 남깁니다.
        filtered_faq_data = filtered_faq_data[search_mask]

    # 현재 조건에 맞는 FAQ 검색 결과 건수를 화면에 표시합니다.
    st.caption(f"FAQ 검색 결과: {len(filtered_faq_data)}건")

    # 필터링 결과가 비어 있으면 경고 문구를 출력하고 종료합니다.
    if filtered_faq_data.empty:
        st.warning("선택한 조건에 맞는 FAQ가 없습니다.")
        return

    # 정렬에 사용할 컬럼 목록을 구성합니다.
    # faq_number, category, question 컬럼 중 실제로 존재하는 컬럼만 사용합니다.
    sort_columns = [
        column for column in ["faq_number", "category", "question"]
        if column in filtered_faq_data.columns
    ]

    # FAQ 데이터를 정렬한 뒤 인덱스를 다시 0부터 재설정합니다.
    filtered_faq_data = filtered_faq_data.sort_values(
        sort_columns,
        na_position="last",
    ).reset_index(drop=True)

    # 카테고리별 탭을 생성하기 위한 목록입니다.
    # "전체" 탭 + 실제 category 고유값을 정렬하여 사용합니다.
    category_tabs = ["전체"] + sorted(filtered_faq_data["category"].dropna().unique().tolist())

    # Streamlit 탭 UI를 생성합니다.
    tabs = st.tabs(category_tabs)

    # 각 탭 이름과 실제 탭 객체를 함께 순회합니다.
    for tab_name, tab in zip(category_tabs, tabs):
        # 각 탭 내부에 해당 카테고리의 FAQ를 출력합니다.
        with tab:
            # "전체" 탭이면 현재 필터링된 전체 데이터를 그대로 사용합니다.
            if tab_name == "전체":
                category_view_data = filtered_faq_data
            else:
                # 특정 카테고리 탭이면 해당 카테고리에 맞는 데이터만 사용합니다.
                category_view_data = filtered_faq_data[
                    filtered_faq_data["category"] == tab_name
                ].reset_index(drop=True)

            # 해당 카테고리에 표시할 데이터가 없으면 안내 문구를 출력하고 다음 탭으로 넘어갑니다.
            if category_view_data.empty:
                st.info("해당 카테고리에 표시할 FAQ가 없습니다.")
                continue

            # 카테고리 내 각 FAQ 행을 순회하며 expander 형태로 질문/답변을 출력합니다.
            for _, faq_row in category_view_data.iterrows():
                # 카테고리 값을 읽고, 비어 있으면 "기타"를 기본값으로 사용합니다.
                category = str(faq_row.get("category", "기타")).strip()

                # 질문 값을 읽고, 비어 있으면 "질문"을 기본값으로 사용합니다.
                question = str(faq_row.get("question", "질문")).strip()

                # 원본 질문 값을 읽습니다.
                question_original = str(faq_row.get("question_original", "")).strip()

                # 답변 값을 읽습니다.
                answer = str(faq_row.get("answer", "")).strip()

                # FAQ 번호 값을 읽습니다.
                faq_number = faq_row.get("faq_number")

                # FAQ 번호를 화면에 출력할 수 있는 문자열 형태로 준비합니다.
                faq_number_text = ""

                # faq_number 값이 결측치가 아닐 때만 문자열 변환을 시도합니다.
                if pd.notna(faq_number):
                    try:
                        # FAQ 번호가 숫자형이면 소수점 없는 정수 문자열로 변환합니다.
                        faq_number_text = str(int(float(faq_number)))
                    except (TypeError, ValueError):
                        # 숫자형 변환이 불가능하면 원래 값을 문자열로 사용합니다.
                        faq_number_text = str(faq_number)

                # 질문 표시용 문자열을 정리합니다.
                # 원본 질문(question_original)이 있으면 이를 우선 사용하고,
                # 앞번호나 접두어를 제거한 뒤 반환합니다.
                # 정리 결과가 비어 있으면 원래 question 값을 사용합니다.
                display_question = _clean_display_question(question, question_original) or question

                # show_question_number 옵션이 True이고 FAQ 번호 문자열이 있으면
                # "번호. 질문" 형태로 expander 제목을 만듭니다.
                if show_question_number and faq_number_text:
                    expander_title = f"{faq_number_text}. {display_question}"
                else:
                    # 번호를 표시하지 않는 경우 질문만 제목으로 사용합니다.
                    expander_title = display_question

                # 각 질문을 expander로 출력합니다.
                with st.expander(expander_title):
                    # expander 내부 상단의 메타 정보(카테고리, 번호)를 담을 리스트입니다.
                    meta_parts = [f"카테고리: {category}"]

                    # show_question_number 옵션이 True이고 FAQ 번호가 있으면 번호 정보도 함께 표시합니다.
                    if show_question_number and faq_number_text:
                        meta_parts.append(f"번호: {faq_number_text}")

                    # 메타 정보를 " / "로 이어서 캡션 형태로 출력합니다.
                    st.caption(" / ".join(meta_parts))

                    # 답변 문자열을 HTML 안전 문자열로 변환합니다.
                    # 줄바꿈은 HTML <br> 태그로 바꾸어 화면에서 줄바꿈이 유지되도록 합니다.
                    safe_answer = html.escape(answer).replace("\r\n", "\n").replace("\n", "<br>")

                    # 답변 본문을 Markdown(HTML 허용)으로 출력합니다.
                    # white-space:pre-wrap 으로 공백과 줄바꿈을 유지하고,
                    # line-height를 높여 가독성을 개선합니다.
                    st.markdown(
                        f"<div style='white-space:pre-wrap; line-height:1.7;'>{safe_answer}</div>",
                        unsafe_allow_html=True,
                    )


def render_faq_page(faq_data: pd.DataFrame) -> None:
    # 서울시 전기차 FAQ 페이지의 상단 제목을 출력합니다.
    st.header("서울시 전기차 FAQ")

    # 페이지 설명 문구를 출력합니다.
    st.caption("보조금 정책과 분리된 서울시 전기차 FAQ 페이지입니다. 차량군 필터로 원하는 질문만 빠르게 볼 수 있습니다.")

    # 공통 FAQ 렌더링 함수를 호출하여 서울시 FAQ 전용 화면을 구성합니다.
    # 여기서는 질문 앞 번호를 표시(show_question_number=True)하도록 설정합니다.
    render_faq_section(
        faq_data,
        section_title="서울시 전기차 FAQ",
        section_caption="분류 필터에서 전체, 전기승용/화물/승합, 전기이륜 중 원하는 항목을 선택해 조회하세요.",
        show_question_number=True,
    )


def render_brand_faq_section(
    brand_faq_data: pd.DataFrame,
    section_title: str = "브랜드 FAQ",
    section_caption: str | None = None,
    show_question_number: bool = False,
) -> None:
    # 브랜드 FAQ 섹션의 소제목을 출력합니다.
    st.subheader(section_title)

    # 섹션 설명 문구를 출력합니다.
    # section_caption 값이 있으면 그 값을 사용하고,
    # 없으면 기본 안내 문구를 사용합니다.
    st.caption(
        section_caption
        or "제조사별 FAQ 데이터를 기준으로 질문과 답변을 조회합니다."
    )

    # 브랜드 FAQ 데이터가 비어 있으면 안내 문구를 출력하고 종료합니다.
    if brand_faq_data.empty:
        st.info("표시할 브랜드 FAQ 데이터가 없습니다.")
        return

    # 브랜드 FAQ 화면을 렌더링하기 위해 반드시 필요한 최소 컬럼 목록입니다.
    required_columns = {"category", "question", "answer"}

    # 필수 컬럼이 하나라도 없으면 데이터 형식이 올바르지 않다고 보고 경고 문구를 출력합니다.
    if not required_columns.issubset(set(brand_faq_data.columns)):
        st.warning("브랜드 FAQ 데이터 형식이 올바르지 않습니다.")
        return

    # 원본 데이터 훼손을 방지하기 위해 복사본을 생성합니다.
    filtered_brand_faq_data = brand_faq_data.copy()

    # 문자열로 다루어야 하는 컬럼들의 결측치를 빈 문자열로 바꾸고,
    # 문자열 타입으로 변환한 뒤, 앞뒤 공백을 제거합니다.
    for column_name in ["category", "question", "question_original", "answer"]:
        if column_name in filtered_brand_faq_data.columns:
            filtered_brand_faq_data[column_name] = (
                filtered_brand_faq_data[column_name]
                .fillna("")
                .astype(str)
                .str.strip()
            )

    # 질문 또는 답변이 비어 있는 행은 화면에 표시할 가치가 없으므로 제거합니다.
    filtered_brand_faq_data = filtered_brand_faq_data[
        (filtered_brand_faq_data["question"] != "")
        & (filtered_brand_faq_data["answer"] != "")
    ].copy()

    # 정리 후 데이터가 비어 있으면 안내 문구를 출력하고 종료합니다.
    if filtered_brand_faq_data.empty:
        st.info("표시할 브랜드 FAQ 데이터가 없습니다.")
        return

    # 필터 UI를 2개의 컬럼 영역으로 나누어 배치합니다.
    # 1열: 세부 카테고리 선택
    # 2열: 검색어 입력
    filter_column_1, filter_column_2 = st.columns([1.1, 1.8])

    # 세부 카테고리 선택 목록을 만듭니다.
    # "전체" 항목 + category 컬럼 고유값을 정렬하여 사용합니다.
    category_list = ["전체"] + sorted(filtered_brand_faq_data["category"].dropna().unique().tolist())

    # 카테고리 선택 박스를 화면에 출력합니다.
    selected_category = filter_column_1.selectbox("세부 카테고리 선택", category_list)

    # FAQ 검색어 입력창을 화면에 출력합니다.
    # key 값을 고유하게 주어 여러 브랜드 탭에서 상태 충돌이 나지 않도록 합니다.
    faq_keyword = filter_column_2.text_input(
        "FAQ 검색",
        value="",
        placeholder="예: 충전, 배터리, 보증, 정비",
        key=f"brand_faq_search_{section_title}",
    )

    # 사용자가 "전체"가 아닌 특정 세부 카테고리를 선택한 경우
    # 해당 카테고리의 데이터만 남기도록 필터링합니다.
    if selected_category != "전체":
        filtered_brand_faq_data = filtered_brand_faq_data[
            filtered_brand_faq_data["category"] == selected_category
        ]

    # 검색어가 입력된 경우에만 검색 필터를 수행합니다.
    if faq_keyword.strip():
        # 검색어 앞뒤 공백을 제거합니다.
        faq_keyword = faq_keyword.strip()

        # 브랜드 FAQ에서 검색할 기본 컬럼 목록입니다.
        search_columns = ["question", "answer", "question_original"]

        # 검색 결과 누적용 불리언 마스크입니다.
        search_mask = False

        # 각 컬럼에 검색어가 포함되는지 검사하여 OR 연산으로 누적합니다.
        for column_name in search_columns:
            if column_name in filtered_brand_faq_data.columns:
                search_mask = (
                    search_mask
                    | filtered_brand_faq_data[column_name].astype(str).str.contains(
                        faq_keyword, case=False, na=False
                    )
                )

        # 검색 조건을 만족하는 행만 남깁니다.
        filtered_brand_faq_data = filtered_brand_faq_data[search_mask]

    # 현재 조건에 맞는 FAQ 검색 결과 건수를 화면에 출력합니다.
    st.caption(f"FAQ 검색 결과: {len(filtered_brand_faq_data)}건")

    # 필터링 결과가 비어 있으면 경고 문구를 출력하고 종료합니다.
    if filtered_brand_faq_data.empty:
        st.warning("선택한 조건에 맞는 FAQ가 없습니다.")
        return

    # 정렬에 사용할 컬럼 목록을 구성합니다.
    # faq_number, category, question 컬럼 중 실제로 존재하는 것만 사용합니다.
    sort_columns = [
        column for column in ["faq_number", "category", "question"]
        if column in filtered_brand_faq_data.columns
    ]

    # 데이터를 정렬하고 인덱스를 다시 0부터 설정합니다.
    filtered_brand_faq_data = filtered_brand_faq_data.sort_values(
        sort_columns,
        na_position="last",
    ).reset_index(drop=True)

    # 카테고리별 탭을 만들기 위한 목록입니다.
    # "전체" 탭 + 실제 category 고유값을 정렬하여 사용합니다.
    category_tabs = ["전체"] + sorted(filtered_brand_faq_data["category"].dropna().unique().tolist())

    # Streamlit 탭 UI를 생성합니다.
    tabs = st.tabs(category_tabs)

    # 각 카테고리 탭을 순회하면서 해당 카테고리의 FAQ를 출력합니다.
    for tab_name, tab in zip(category_tabs, tabs):
        with tab:
            # "전체" 탭이면 전체 데이터를 사용합니다.
            if tab_name == "전체":
                category_view_data = filtered_brand_faq_data
            else:
                # 특정 카테고리 탭이면 해당 카테고리 데이터만 사용합니다.
                category_view_data = filtered_brand_faq_data[
                    filtered_brand_faq_data["category"] == tab_name
                ].reset_index(drop=True)

            # 해당 카테고리에 표시할 FAQ가 없으면 안내 문구를 출력합니다.
            if category_view_data.empty:
                st.info("해당 카테고리에 표시할 FAQ가 없습니다.")
                continue

            # 각 FAQ를 expander 형태로 출력합니다.
            for _, faq_row in category_view_data.iterrows():
                # 카테고리 값을 읽고, 비어 있으면 "기타"를 기본값으로 사용합니다.
                category = str(faq_row.get("category", "기타")).strip()

                # 질문 값을 읽고, 비어 있으면 "질문"을 기본값으로 사용합니다.
                question = str(faq_row.get("question", "질문")).strip()

                # 원본 질문 값을 읽습니다.
                question_original = str(faq_row.get("question_original", "")).strip()

                # 답변 값을 읽습니다.
                answer = str(faq_row.get("answer", "")).strip()

                # FAQ 번호 값을 읽습니다.
                faq_number = faq_row.get("faq_number")

                # FAQ 번호를 화면 표시용 문자열로 준비합니다.
                faq_number_text = ""

                # faq_number 값이 결측치가 아닐 때만 문자열 변환을 시도합니다.
                if pd.notna(faq_number):
                    try:
                        # 숫자형이면 정수 문자열로 변환합니다.
                        faq_number_text = str(int(float(faq_number)))
                    except (TypeError, ValueError):
                        # 숫자형이 아니면 원래 값을 문자열로 사용합니다.
                        faq_number_text = str(faq_number)

                # 질문 표시용 문자열을 정리합니다.
                # 앞번호나 접두어를 제거하여 화면에 더 깔끔하게 보여주기 위함입니다.
                display_question = _clean_display_question(question, question_original) or question

                # 브랜드 FAQ는 기본적으로 질문 번호를 표시하지 않지만,
                # show_question_number 값이 True이면 번호를 함께 표시할 수 있도록 설계되어 있습니다.
                if show_question_number and faq_number_text:
                    expander_title = f"{faq_number_text}. {display_question}"
                else:
                    expander_title = display_question

                # 각 질문을 expander로 출력합니다.
                with st.expander(expander_title):
                    # 상단 메타 정보(카테고리, 번호)를 담을 리스트입니다.
                    meta_parts = [f"카테고리: {category}"]

                    # 번호 표시 옵션이 켜져 있으면 번호도 함께 표시합니다.
                    if show_question_number and faq_number_text:
                        meta_parts.append(f"번호: {faq_number_text}")

                    # 메타 정보를 " / " 구분자로 묶어 캡션으로 출력합니다.
                    st.caption(" / ".join(meta_parts))

                    # 답변 문자열을 HTML 안전 문자열로 변환합니다.
                    # 줄바꿈은 HTML <br> 태그로 바꾸어 화면에서도 줄바꿈이 유지되도록 처리합니다.
                    safe_answer = html.escape(answer).replace("\r\n", "\n").replace("\n", "<br>")

                    # 답변을 Markdown(HTML 허용)으로 출력합니다.
                    st.markdown(
                        f"<div style='white-space:pre-wrap; line-height:1.7;'>{safe_answer}</div>",
                        unsafe_allow_html=True,
                    )


def render_brand_faq_page(brand_faq_data: pd.DataFrame) -> None:
    # 브랜드 FAQ 페이지 상단 제목을 출력합니다.
    st.header("전기차 브랜드 별 FAQ")

    # 페이지 설명 문구를 출력합니다.
    st.caption("제조사별 FAQ 엑셀의 시트 기준으로 브랜드를 선택해 질문과 답변을 조회합니다.")

    # 브랜드 FAQ 데이터가 비어 있으면 안내 문구를 출력하고 종료합니다.
    if brand_faq_data.empty:
        st.info("표시할 브랜드 FAQ 데이터가 없습니다.")
        return

    # 브랜드 FAQ 페이지를 구성하기 위해 반드시 필요한 최소 컬럼 목록입니다.
    required_columns = {"brand", "category", "question", "answer"}

    # 필수 컬럼이 누락되어 있으면 데이터 형식 오류로 간주하고 경고를 표시합니다.
    if not required_columns.issubset(set(brand_faq_data.columns)):
        st.warning("브랜드 FAQ 데이터 형식이 올바르지 않습니다.")
        return

    # 원본 데이터 훼손을 방지하기 위해 복사본을 생성합니다.
    cleaned_brand_faq_data = brand_faq_data.copy()

    # 문자열로 다루는 주요 컬럼들의 결측치를 빈 문자열로 바꾸고,
    # 문자열 타입으로 변환한 뒤, 앞뒤 공백을 제거합니다.
    for column_name in ["brand", "category", "question", "question_original", "answer"]:
        if column_name in cleaned_brand_faq_data.columns:
            cleaned_brand_faq_data[column_name] = (
                cleaned_brand_faq_data[column_name]
                .fillna("")
                .astype(str)
                .str.strip()
            )

    # 브랜드명, 질문, 답변이 모두 존재하는 행만 남깁니다.
    # 이 세 값 중 하나라도 비어 있으면 화면 표시에 적합하지 않으므로 제거합니다.
    cleaned_brand_faq_data = cleaned_brand_faq_data[
        (cleaned_brand_faq_data["brand"] != "")
        & (cleaned_brand_faq_data["question"] != "")
        & (cleaned_brand_faq_data["answer"] != "")
    ].copy()

    # 정리 후 데이터가 비어 있으면 안내 문구를 출력하고 종료합니다.
    if cleaned_brand_faq_data.empty:
        st.info("표시할 브랜드 FAQ 데이터가 없습니다.")
        return

    # 브랜드명 목록을 추출합니다.
    # dropna()로 결측치를 제거하고, 문자열로 변환한 뒤 고유값만 리스트로 가져옵니다.
    brand_list = cleaned_brand_faq_data["brand"].dropna().astype(str).unique().tolist()

    # 브랜드 탭의 글자 크기와 높이를 키우기 위한 CSS를 주입합니다.
    # Streamlit의 st.tabs()가 생성하는 탭 UI에 스타일을 적용합니다.
    st.markdown("""
<style>
/* 탭 전체 버튼 */
.stTabs [role="tab"] {
    height: 56px;
    padding-left: 18px !important;
    padding-right: 18px !important;
}

/* 탭 안의 실제 글자 */
.stTabs [role="tab"] p {
    font-size: 24px !important;
    font-weight: 700 !important;
}
</style>
""", unsafe_allow_html=True)

    # 브랜드별 상단 탭을 생성합니다.
    brand_tabs = st.tabs(brand_list)

    # 각 브랜드 탭을 순회하면서 해당 브랜드의 FAQ를 출력합니다.
    for brand_name, brand_tab in zip(brand_list, brand_tabs):
        with brand_tab:
            # 현재 탭에 해당하는 브랜드의 데이터만 필터링합니다.
            brand_view_data = cleaned_brand_faq_data[
                cleaned_brand_faq_data["brand"] == brand_name
            ].copy()

            # 브랜드별 FAQ 섹션 렌더링 함수를 호출합니다.
            # 브랜드 FAQ는 질문 앞 번호를 표시하지 않도록 설정합니다.
            render_brand_faq_section(
                brand_view_data,
                section_title=f"{brand_name} FAQ",
                section_caption=f"{brand_name} 시트 기준 FAQ입니다.",
                show_question_number=False,
            )