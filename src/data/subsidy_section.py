# 이 스크립트는 Streamlit 기반 전기차 정보 포털에서
# "4. 보조금 정책" 화면을 구성하는 역할을 합니다.
#
# 이 스크립트의 핵심 기능은 다음과 같습니다.
#
# 1) 보조금 정책 데이터 필터링
#    - 차량 유형 시트(sheet_name), 구분(vehicle_group), 제조사(manufacturer)를 기준으로
#      사용자가 원하는 조건의 보조금 정책 데이터만 조회할 수 있게 합니다.
#    - 추가로 차종명(model_name) 검색어를 입력하여 특정 차량 모델만 빠르게 찾을 수 있게 합니다.
#
# 2) 보조금 핵심 지표(metric) 표시
#    - 현재 조회 조건에 맞는 차종 수
#    - 최대 보조금
#    - 평균 보조금
#    을 화면 상단에 요약 지표 형태로 보여줍니다.
#
# 3) 보조금 정책 테이블 표시
#    - 필터링된 정책 데이터를 한글 컬럼명으로 바꾸어 표 형태로 출력합니다.
#    - 차량분류(vehicle_class) 공란은 "미분류"로 처리하여 사용자에게 더 명확하게 보여줍니다.
#
# 4) 보조금 정책 페이지 렌더링
#    - render_subsidy_page()를 통해 페이지 제목과 설명을 출력하고,
#      내부적으로 render_subsidy_section()을 호출하여 실제 정책 조회 화면을 구성합니다.
#
# 이 스크립트는 직접 원본 엑셀 파일을 읽지 않습니다.
# 즉, "데이터 로딩"과 "화면 렌더링"이 분리된 구조입니다.
#
# 이 스크립트와 상호작용하는 주요 스크립트는 다음과 같습니다.
#
# 1) src/db/query_data.py
#    - national subsidy.xlsx 같은 원본 보조금 파일을 읽어서
#      sheet_name, vehicle_group, vehicle_class, manufacturer, model_name, subsidy_amount
#      등의 표준 컬럼 구조를 가진 DataFrame으로 가공합니다.
#    - 이 스크립트는 query_data.py가 준비한 policy_data를 입력으로 받아 화면에 출력합니다.
#
# 2) src/app/main_app.py
#    - 전체 Streamlit 앱의 진입점이며 메뉴 라우팅을 담당합니다.
#    - load_dashboard_data()에서 보조금 정책 데이터를 미리 불러온 뒤,
#      사용자가 "4. 보조금 정책" 메뉴를 선택하면 render_subsidy_page()를 호출합니다.
#
# 전체 흐름은 보통 다음과 같습니다.
#
# query_data.py
#   -> 보조금 정책 데이터 로드 및 컬럼 표준화
# main_app.py
#   -> load_dashboard_data()에 policy_data 저장
#   -> 4번 메뉴 선택 시 render_subsidy_page() 호출
# subsidy_section.py (현재 스크립트)
#   -> 필터 UI 표시
#   -> 요약 지표 및 보조금 정책 테이블 화면 구성
#
# 정리하면,
# 이 스크립트는 "보조금 정책 데이터를 사용자가 조건별로 쉽게 조회할 수 있도록
# 화면으로 구성하는 Streamlit 보조금 정책 렌더링 전담 스크립트"입니다.

import pandas as pd
import streamlit as st


def render_subsidy_section(policy_data: pd.DataFrame) -> None:
    # 보조금 정책 섹션의 소제목을 출력합니다.
    st.subheader("국고보조금 정책 정보")

    # 이 섹션이 어떤 데이터를 보여주는지 설명하는 캡션을 출력합니다.
    st.caption("national subsidy.xlsx 파일 기준으로 차종별 국고보조금 정보를 조회합니다.")

    # 전달받은 정책 데이터가 비어 있으면 안내 문구를 출력하고 함수 실행을 종료합니다.
    if policy_data.empty:
        st.info("표시할 보조금 정책 데이터가 없습니다.")
        return

    # 차량 유형 시트(sheet_name) 선택 목록을 생성합니다.
    # "전체" 항목을 맨 앞에 두고, 실제 시트명 고유값을 정렬하여 뒤에 붙입니다.
    sheet_name_list = ["전체"] + sorted(
        policy_data["sheet_name"].dropna().astype(str).unique().tolist()
    )

    # 구분(vehicle_group) 선택 목록을 생성합니다.
    # 결측치를 제거하고, 공백 문자열이 아닌 값만 골라 정렬한 뒤 "전체"를 앞에 붙입니다.
    vehicle_group_list = ["전체"] + sorted(
        [
            value
            for value in policy_data["vehicle_group"].dropna().astype(str).unique().tolist()
            if value.strip() != ""
        ]
    )

    # 제조사(manufacturer) 선택 목록을 생성합니다.
    # 결측치를 제거하고, 공백 문자열이 아닌 값만 골라 정렬한 뒤 "전체"를 앞에 붙입니다.
    manufacturer_list = ["전체"] + sorted(
        [
            value
            for value in policy_data["manufacturer"].dropna().astype(str).unique().tolist()
            if value.strip() != ""
        ]
    )

    # 필터 UI를 3개의 컬럼으로 나누어 배치합니다.
    # 1열: 차량 유형 시트 선택
    # 2열: 구분 선택
    # 3열: 제조사 선택
    filter_column_1, filter_column_2, filter_column_3 = st.columns(3)

    # 사용자가 조회할 차량 유형 시트를 선택할 수 있는 selectbox를 출력합니다.
    selected_sheet_name = filter_column_1.selectbox("차량 유형 시트 선택", sheet_name_list)

    # 사용자가 조회할 구분(vehicle_group)을 선택할 수 있는 selectbox를 출력합니다.
    selected_vehicle_group = filter_column_2.selectbox("구분 선택", vehicle_group_list)

    # 사용자가 조회할 제조사를 선택할 수 있는 selectbox를 출력합니다.
    selected_manufacturer = filter_column_3.selectbox("제조사 선택", manufacturer_list)

    # 차종명으로 검색할 수 있는 텍스트 입력창을 출력합니다.
    subsidy_keyword = st.text_input(
        "차종 검색",
        value="",
        placeholder="예: 넥쏘, 포터, 코나, 카운티",
    )

    # 원본 policy_data를 직접 수정하지 않기 위해 복사본을 생성합니다.
    filtered_policy_data = policy_data.copy()

    # 사용자가 "전체"가 아닌 특정 차량 유형 시트를 선택한 경우
    # 해당 sheet_name 데이터만 남기도록 필터링합니다.
    if selected_sheet_name != "전체":
        filtered_policy_data = filtered_policy_data[
            filtered_policy_data["sheet_name"] == selected_sheet_name
        ]

    # 사용자가 "전체"가 아닌 특정 구분을 선택한 경우
    # 해당 vehicle_group 데이터만 남기도록 필터링합니다.
    if selected_vehicle_group != "전체":
        filtered_policy_data = filtered_policy_data[
            filtered_policy_data["vehicle_group"] == selected_vehicle_group
        ]

    # 사용자가 "전체"가 아닌 특정 제조사를 선택한 경우
    # 해당 manufacturer 데이터만 남기도록 필터링합니다.
    if selected_manufacturer != "전체":
        filtered_policy_data = filtered_policy_data[
            filtered_policy_data["manufacturer"] == selected_manufacturer
        ]

    # 차종 검색어가 입력된 경우에만 검색 필터를 수행합니다.
    if subsidy_keyword.strip():
        # 검색어 앞뒤 공백을 제거합니다.
        subsidy_keyword = subsidy_keyword.strip()

        # model_name 컬럼에 검색어가 포함된 행만 남깁니다.
        # 대소문자 구분 없이 검색하고, 결측치는 False로 처리합니다.
        filtered_policy_data = filtered_policy_data[
            filtered_policy_data["model_name"].astype(str).str.contains(
                subsidy_keyword,
                case=False,
                na=False,
            )
        ]

    # 핵심 지표를 3개의 metric 컬럼으로 나누어 배치합니다.
    metric_column_1, metric_column_2, metric_column_3 = st.columns(3)

    # 현재 조건에 맞는 조회 차종 수를 metric으로 출력합니다.
    metric_column_1.metric("조회 차종 수", f"{len(filtered_policy_data):,}개")

    # 필터링된 데이터가 비어 있지 않고 subsidy_amount 컬럼이 존재하면
    # 최대 보조금과 평균 보조금을 계산하여 출력합니다.
    if not filtered_policy_data.empty and "subsidy_amount" in filtered_policy_data.columns:
        # 최대 보조금 값을 계산합니다.
        max_subsidy = filtered_policy_data["subsidy_amount"].max()

        # 평균 보조금 값을 계산합니다.
        avg_subsidy = filtered_policy_data["subsidy_amount"].mean()

        # 최대 보조금을 metric으로 출력합니다.
        # 값이 결측치가 아니면 "만원" 단위를 붙여서 보여줍니다.
        metric_column_2.metric(
            "최대 보조금",
            f"{max_subsidy:,.0f} 만원" if pd.notna(max_subsidy) else "-",
        )

        # 평균 보조금을 metric으로 출력합니다.
        # 값이 결측치가 아니면 소수 첫째 자리까지 표시합니다.
        metric_column_3.metric(
            "평균 보조금",
            f"{avg_subsidy:,.1f} 만원" if pd.notna(avg_subsidy) else "-",
        )
    else:
        # 데이터가 없거나 subsidy_amount 컬럼이 없으면 "-"로 표시합니다.
        metric_column_2.metric("최대 보조금", "-")
        metric_column_3.metric("평균 보조금", "-")

    # 필터링 결과가 비어 있으면 경고 문구를 출력하고 함수 실행을 종료합니다.
    if filtered_policy_data.empty:
        st.warning("선택한 조건에 맞는 보조금 정보가 없습니다.")
        return

    # 실제 화면에 출력할 DataFrame 복사본을 생성합니다.
    display_policy_data = filtered_policy_data.copy()

# 차량분류 공란 처리
    # vehicle_class 컬럼이 존재하면 공란/문자열 nan/문자열 None 값을 "미분류"로 바꿉니다.
    if "vehicle_class" in display_policy_data.columns:
        display_policy_data["vehicle_class"] = (
            display_policy_data["vehicle_class"]
            .astype(str)
            .str.strip()
            .replace(["", "nan", "None"], "미분류")
        )   

    # subsidy_amount 컬럼이 존재하면 숫자형으로 변환합니다.
    # 변환이 안 되는 값은 NaN으로 처리합니다.
    if "subsidy_amount" in display_policy_data.columns:
        display_policy_data["subsidy_amount"] = pd.to_numeric(
            display_policy_data["subsidy_amount"],
            errors="coerce",
        )

    # 최종 보조금 정책 데이터를 한글 컬럼명으로 바꿔 표 형태로 출력합니다.
    st.dataframe(
        display_policy_data.rename(
            columns={
                "sheet_name": "차량 유형",
                "vehicle_group": "구분",
                "vehicle_class": "차량분류",
                "manufacturer": "제조사",
                "model_name": "차종",
                "subsidy_amount": "국고보조금(만원)",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

def render_subsidy_page(policy_data: pd.DataFrame) -> None:
    # 보조금 정책 페이지의 상단 제목을 출력합니다.
    st.header("보조금 정책")

    # 페이지 설명 문구를 출력합니다.
    st.caption("보조금 기준표를 별도 페이지로 분리해 더 짧고 명확하게 확인할 수 있습니다.")

    # 실제 보조금 정책 조회 화면을 구성하는 공통 렌더링 함수를 호출합니다.
    render_subsidy_section(policy_data)