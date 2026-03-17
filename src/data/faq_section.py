# 이 스크립트는 Streamlit 기반 전기차 정보 포털에서
# "서울시 전기차 FAQ" 화면을 구성하는 역할을 합니다.
#
# 이 스크립트의 핵심 기능은 다음과 같습니다.
#
# 1) FAQ 질문 문자열 정리
#    - 질문 맨 앞에 붙은 번호(예: "1. 질문")나
#      대괄호 형태의 불필요한 접두어(예: "[보조금]")를 제거하여
#      화면에 더 깔끔한 질문 제목을 보여줍니다.
#
# 2) FAQ 목록 필터링
#    - FAQ 구분(faq_group), 세부 카테고리(category), 검색어(keyword)를 기준으로
#      FAQ 데이터를 걸러냅니다.
#    - 검색어는 질문, 답변, 태그, 원본 질문까지 함께 검색합니다.
#
# 3) FAQ 탭/아코디언(expander) 화면 구성
#    - 카테고리별 탭을 생성하고,
#      각 질문을 expander 형태로 펼쳐서 답변을 볼 수 있게 합니다.
#    - 질문 제목에는 FAQ 번호를 붙여 보여줄 수 있습니다.
#
# 4) 서울시 전기차 FAQ 페이지 렌더링
#    - render_faq_page()를 통해 실제 Streamlit 페이지 제목과 설명을 출력하고,
#      내부적으로 render_faq_section()을 호출하여 상세 FAQ 화면을 구성합니다.
#
# 이 스크립트는 직접 FAQ 원본 파일을 읽지 않습니다.
# 즉, 데이터 로딩과 화면 출력이 분리된 구조입니다.
#
# 이 스크립트와 상호작용하는 주요 스크립트는 다음과 같습니다.
#
# 1) src/db/query_data.py
#    - FAQ 원본 엑셀/CSV 데이터를 읽어서
#      faq_group, category, tag, question, question_original, answer, faq_number 등의
#      표준 컬럼 구조를 가진 DataFrame으로 가공합니다.
#    - 이 스크립트는 query_data.py가 준비한 FAQ DataFrame을 입력으로 받아 화면에 출력합니다.
#
# 2) src/app/main_app.py
#    - 전체 Streamlit 앱의 진입점이며 메뉴 라우팅을 담당합니다.
#    - load_dashboard_data()에서 load_faq_data()를 호출해 FAQ 데이터를 미리 불러온 뒤,
#      사용자가 FAQ 메뉴를 선택하면 render_faq_page()를 호출합니다.
#
# 전체 흐름은 보통 다음과 같습니다.
#
# query_data.py
#   -> FAQ 데이터 로드 및 컬럼 표준화
# main_app.py
#   -> load_dashboard_data()에 FAQ 데이터 저장
#   -> FAQ 메뉴 선택 시 render_faq_page() 호출
# faq_section.py (현재 스크립트)
#   -> FAQ 필터 UI 표시
#   -> FAQ 검색/정렬/탭/expander 화면 구성
#
# 정리하면,
# 이 스크립트는 "FAQ 데이터를 사용자가 쉽게 찾고 읽을 수 있도록 화면으로 구성하는
# Streamlit FAQ 렌더링 전담 스크립트"입니다.

# HTML 특수문자를 안전하게 변환하기 위한 표준 라이브러리입니다.
# 답변 본문에 <, >, & 같은 문자가 들어 있어도 HTML이 깨지지 않도록 처리할 때 사용합니다.
import html

# 정규표현식 처리를 위한 표준 라이브러리입니다.
# 질문 앞번호나 대괄호 접두어를 제거할 때 사용합니다.
import re

# 표 형태 데이터(DataFrame)를 다루기 위한 pandas 라이브러리입니다.
# 결측치 판별(pd.notna), 정렬, 필터링 등에 사용합니다.
import pandas as pd

# Streamlit 화면 구성을 위한 라이브러리입니다.
# 제목, 캡션, 탭, expander, text_input, selectbox 등을 출력할 때 사용합니다.
import streamlit as st


def _clean_display_question(question: str, question_original: str = "") -> str:
    # question_original 값이 있으면 문자열로 변환하고 앞뒤 공백을 제거합니다.
    original = str(question_original or "").strip()

    # 원본 질문 문자열이 존재하면,
    # 맨 앞에 붙은 번호 패턴(예: "1. ", "23. ")을 제거한 뒤 반환합니다.
    if original:
        return re.sub(r"^\d+\.\s*", "", original).strip()

    # 원본 질문이 없으면 question 값을 기준으로 문자열을 정리합니다.
    cleaned = str(question or "").strip()

    # 질문 앞에 대괄호 접두어가 여러 개 붙어 있을 경우 제거합니다.
    # 예: "[보조금] [신청] 질문내용" -> "질문내용"
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
) -> None:
    # FAQ 섹션의 소제목을 출력합니다.
    st.subheader(section_title)

    # 섹션 설명 문구를 출력합니다.
    # section_caption 값이 있으면 그 값을 사용하고,
    # 없으면 기본 설명 문구를 사용합니다.
    st.caption(
        section_caption
        or "서울시 전기차 FAQ 자료를 기준으로 질문/답변을 조회합니다."
    )

    # 전달받은 FAQ 데이터가 비어 있으면 안내 문구를 출력하고 함수 실행을 종료합니다.
    if faq_data.empty:
        st.info("표시할 FAQ 데이터가 없습니다.")
        return

    # 원본 DataFrame을 직접 수정하지 않기 위해 복사본을 생성합니다.
    filtered_faq_data = faq_data.copy()

    # default_group 값이 있으면,
    # faq_group 컬럼이 해당 값과 일치하는 데이터만 남기도록 필터링합니다.
    if default_group:
        filtered_faq_data = filtered_faq_data[
            filtered_faq_data["faq_group"].astype(str).str.strip() == default_group
        ].copy()

    # 그룹 필터링 이후 데이터가 비어 있으면 경고 문구를 출력하고 종료합니다.
    if filtered_faq_data.empty:
        st.warning("선택한 그룹에 해당하는 FAQ가 없습니다.")
        return

    # FAQ 구분 선택용 목록입니다.
    # "전체" 항목 + faq_group 고유값 목록을 정렬해서 사용합니다.
    group_list = ["전체"] + sorted(filtered_faq_data["faq_group"].dropna().unique().tolist())

    # 세부 카테고리 선택용 목록입니다.
    # "전체" 항목 + category 고유값 목록을 정렬해서 사용합니다.
    category_list = ["전체"] + sorted(filtered_faq_data["category"].dropna().unique().tolist())

    # tag 컬럼에서 비어 있지 않은 값만 추출하여 태그 목록을 만듭니다.
    # dropna()로 결측치를 제거하고, 문자열로 변환 후 공백 문자열은 제외합니다.
    tag_list = sorted(
        [value for value in filtered_faq_data["tag"].dropna().astype(str).unique().tolist() if value.strip()]
    )

    # 필터 UI를 3개의 컬럼으로 나누어 배치합니다.
    # 1열: FAQ 구분 선택
    # 2열: 세부 카테고리 선택
    # 3열: 검색어 입력
    filter_column_1, filter_column_2, filter_column_3 = st.columns([1.1, 1.1, 1.8])

    # FAQ 구분 선택값입니다.
    # default_group 값이 있으면 그 값을 우선 사용하고,
    # 없으면 사용자가 직접 selectbox에서 선택합니다.
    selected_group = default_group or filter_column_1.selectbox("FAQ 구분 선택", group_list)

    # default_group 값이 주어진 경우에는
    # 해당 그룹이 고정되어 있다는 점을 보여주기 위해 비활성화된 text_input을 함께 표시합니다.
    if default_group:
        filter_column_1.text_input("FAQ 구분", value=default_group, disabled=True)

    # 세부 카테고리 선택 박스를 출력합니다.
    selected_category = filter_column_2.selectbox("세부 카테고리 선택", category_list)

    # FAQ 검색어 입력창을 출력합니다.
    faq_keyword = filter_column_3.text_input(
        "FAQ 검색",
        value="",
        placeholder="예: 보조금, 신청, 자격, 환수, 공동명의",
    )

    # 사용자가 "전체"가 아닌 특정 FAQ 구분을 선택한 경우
    # 해당 faq_group 데이터만 남기도록 필터링합니다.
    if selected_group != "전체":
        filtered_faq_data = filtered_faq_data[
            filtered_faq_data["faq_group"] == selected_group
        ]

    # 사용자가 "전체"가 아닌 특정 세부 카테고리를 선택한 경우
    # 해당 category 데이터만 남기도록 필터링합니다.
    if selected_category != "전체":
        filtered_faq_data = filtered_faq_data[
            filtered_faq_data["category"] == selected_category
        ]

    # 검색어가 입력된 경우에만 검색 필터를 수행합니다.
    if faq_keyword.strip():
        # 검색어 앞뒤 공백을 제거합니다.
        faq_keyword = faq_keyword.strip()

        # 질문, 답변, 태그, 원본 질문 중 하나라도 검색어를 포함하는 행만 남깁니다.
        filtered_faq_data = filtered_faq_data[
            filtered_faq_data["question"].astype(str).str.contains(faq_keyword, case=False, na=False)
            | filtered_faq_data["answer"].astype(str).str.contains(faq_keyword, case=False, na=False)
            | filtered_faq_data["tag"].astype(str).str.contains(faq_keyword, case=False, na=False)
            | filtered_faq_data["question_original"].astype(str).str.contains(faq_keyword, case=False, na=False)
        ]

    # 현재 필터 조건에 맞는 FAQ 검색 결과 건수를 화면에 출력합니다.
    st.caption(f"FAQ 검색 결과: {len(filtered_faq_data)}건")

    # 태그 목록이 존재하면, 화면에 전체 태그 목록을 캡션으로 보여줍니다.
    if tag_list:
        st.caption("태그 목록: " + ", ".join(tag_list))

    # 필터링 결과가 비어 있으면 경고 문구를 출력하고 함수 실행을 종료합니다.
    if filtered_faq_data.empty:
        st.warning("선택한 조건에 맞는 FAQ가 없습니다.")
        return

    # FAQ 데이터를 faq_number, category, question 순으로 정렬합니다.
    # faq_number가 비어 있는 경우는 뒤로 보내도록 설정합니다.
    filtered_faq_data = filtered_faq_data.sort_values(
        ["faq_number", "category", "question"],
        na_position="last",
    ).reset_index(drop=True)

    # 카테고리별 탭을 만들기 위한 목록입니다.
    # "전체" 탭 + 현재 필터링된 데이터의 category 고유값을 정렬하여 사용합니다.
    category_tabs = ["전체"] + sorted(filtered_faq_data["category"].dropna().unique().tolist())

    # Streamlit 탭 UI를 생성합니다.
    tabs = st.tabs(category_tabs)

    # 각 탭 이름과 실제 탭 객체를 함께 순회합니다.
    for tab_name, tab in zip(category_tabs, tabs):
        # 각 탭 내부에 해당 카테고리의 FAQ를 출력합니다.
        with tab:
            # "전체" 탭이면 현재 필터링된 전체 데이터를 사용합니다.
            if tab_name == "전체":
                category_view_data = filtered_faq_data
            else:
                # 특정 카테고리 탭이면 해당 카테고리 데이터만 사용합니다.
                category_view_data = filtered_faq_data[
                    filtered_faq_data["category"] == tab_name
                ].reset_index(drop=True)

            # 해당 카테고리에 표시할 FAQ가 없으면 안내 문구를 출력하고 다음 탭으로 넘어갑니다.
            if category_view_data.empty:
                st.info("해당 카테고리에 표시할 FAQ가 없습니다.")
                continue

            # 카테고리 내 각 FAQ 행을 순회하며 expander 형태로 출력합니다.
            for _, faq_row in category_view_data.iterrows():
                # FAQ 구분(faq_group) 값을 읽습니다.
                # 값이 없으면 기본값 "기타"를 사용합니다.
                group_name = str(faq_row.get("faq_group", "기타")).strip()

                # 카테고리 값을 읽습니다.
                # 값이 없으면 기본값 "기타"를 사용합니다.
                category = str(faq_row.get("category", "기타")).strip()

                # 태그 값을 읽습니다.
                tag = str(faq_row.get("tag", "")).strip()

                # 질문 값을 읽습니다.
                # 값이 없으면 기본값 "질문"을 사용합니다.
                question = str(faq_row.get("question", "질문")).strip()

                # 원본 질문 값을 읽습니다.
                question_original = str(faq_row.get("question_original", "")).strip()

                # 답변 값을 읽습니다.
                answer = str(faq_row.get("answer", "")).strip()

                # FAQ 번호 값을 읽습니다.
                faq_number = faq_row.get("faq_number")

                # FAQ 번호를 문자열 형태로 준비할 변수입니다.
                faq_number_text = ""

                # faq_number가 결측치가 아니면 문자열 변환을 시도합니다.
                if pd.notna(faq_number):
                    try:
                        # 숫자형이면 소수점 없는 정수 문자열로 변환합니다.
                        faq_number_text = str(int(float(faq_number)))
                    except (TypeError, ValueError):
                        # 숫자형 변환이 불가능하면 원래 값을 문자열로 사용합니다.
                        faq_number_text = str(faq_number)

                # 화면에 표시할 질문 문자열을 정리합니다.
                # 앞 번호나 대괄호 접두어를 제거한 질문을 사용하고,
                # 정리 결과가 비어 있으면 원래 question 값을 사용합니다.
                display_question = _clean_display_question(question, question_original) or question

                # FAQ 번호 문자열이 있으면 "번호. 질문" 형태로 제목을 만듭니다.
                if faq_number_text:
                    expander_title = f"{faq_number_text}. {display_question}"
                else:
                    # 번호가 없으면 질문만 제목으로 사용합니다.
                    expander_title = display_question

                # 각 질문을 expander 형태로 출력합니다.
                with st.expander(expander_title):
                    # expander 상단에 보여줄 메타 정보 목록입니다.
                    # FAQ 구분과 카테고리는 항상 표시합니다.
                    meta_parts = [f"구분: {group_name}", f"카테고리: {category}"]

                    # 태그가 있으면 메타 정보에 추가합니다.
                    if tag:
                        meta_parts.append(f"태그: {tag}")

                    # FAQ 번호가 있으면 메타 정보에 추가합니다.
                    if faq_number_text:
                        meta_parts.append(f"번호: {faq_number_text}")

                    # 메타 정보를 " / " 구분자로 이어서 캡션 형태로 출력합니다.
                    st.caption(" / ".join(meta_parts))

                    # 답변 문자열을 HTML 안전 문자열로 변환합니다.
                    # 줄바꿈 문자는 <br> 태그로 바꾸어 화면에서도 줄바꿈이 유지되도록 처리합니다.
                    safe_answer = html.escape(answer).replace("\r\n", "\n").replace("\n", "<br>")

                    # 답변 본문을 Markdown(HTML 허용)으로 출력합니다.
                    # white-space:pre-wrap 으로 공백과 줄바꿈을 유지하고,
                    # line-height를 높여 가독성을 높입니다.
                    st.markdown(
                        f"<div style='white-space:pre-wrap; line-height:1.7;'>{safe_answer}</div>",
                        unsafe_allow_html=True,
                    )

def render_faq_page(faq_data: pd.DataFrame) -> None:
    # 페이지 상단 제목을 출력합니다.
    st.header("서울시 전기차 FAQ")

    # 페이지 설명 문구를 출력합니다.
    st.caption("보조금 정책과 분리된 서울시 전기차 FAQ 페이지입니다. 차량군 필터로 원하는 질문만 빠르게 볼 수 있습니다.")

    # 공통 FAQ 렌더링 함수를 호출하여
    # 서울시 전기차 FAQ 화면을 구성합니다.
    render_faq_section(
        faq_data,
        section_title="서울시 전기차 FAQ",
        section_caption="분류 필터에서 전체, 전기승용/화물/승합, 전기이륜 중 원하는 항목을 선택해 조회하세요.",
    )