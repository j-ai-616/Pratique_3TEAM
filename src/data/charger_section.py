##############################################################################################################
### 2번탭 구현 - 충전소 위치 / 충전 가능 여부 / 운영 정보

# 이 스크립트는 Streamlit 기반 전기차 정보 포털에서
# "2. 충전소 위치 / 충전 가능 여부 / 운영 정보" 화면을 구성하는 역할을 합니다.
#
# 이 화면은 크게 두 부분으로 나뉘어 있습니다.
#
# 1) 지역 기반 충전소 검색
#    - 사용자가 지역명 또는 장소명을 입력하면
#      카카오 지역 검색 API를 활용하여 주변 전기차 충전소를 검색합니다.
#    - 검색 결과는 지도와 표 형태로 함께 보여줍니다.
#
# 2) 충전 가능 여부 / 운영 정보 참고 데이터
#    - 프로젝트 내부에 저장된 충전소 운영 정보 데이터를 활용하여
#      지역, 충전기 유형, 사용 가능 여부 조건으로 필터링합니다.
#    - 필터링된 결과를 바탕으로
#      충전소 수, 사용 가능 충전기 수, 전체 충전기 수를 요약 지표로 표시합니다.
#    - 또한 지도와 테이블로 운영 정보를 시각적으로 제공합니다.
#
# 즉, 이 스크립트는
# "외부 지도 검색 기능"과 "내부 운영 정보 데이터 표시 기능"을 하나의 페이지에서 연결해 주는
# 화면 렌더링 전담 스크립트입니다.

# 표 형태 데이터(DataFrame)를 다루기 위한 pandas 라이브러리입니다.
# 검색 결과를 DataFrame으로 변환하거나,
# 운영 정보 DataFrame을 화면에 출력할 때 사용합니다.
import pandas as pd

# Streamlit 화면 구성을 위한 라이브러리입니다.
# 제목, 캡션, 입력창, 체크박스, 멀티셀렉트, 지도, 표 등을 출력할 때 사용합니다.
import streamlit as st

# 카카오 지역 검색을 통해 전기차 충전소를 검색하는 함수입니다.
# 사용자가 입력한 지역명/장소명을 바탕으로 충전소 목록과 디버그 정보를 반환합니다.
from src.map.map_service import search_ev_chargers

# 카카오 지도를 화면에 렌더링하는 함수입니다.
# 검색 결과 또는 운영 정보 결과를 지도 위에 마커 형태로 표시할 때 사용합니다.
from src.map.kakao_map import render_kakao_map

# 충전소 운영 정보 데이터를 가공하는 보조 함수들입니다.
# - build_charger_map_results: 운영 정보 DataFrame을 지도용 리스트로 변환
# - filter_charger_operation_data: 지역/유형/사용 가능 여부로 필터링
# - summarize_charger_operation_data: 충전소 수, 사용 가능 수, 전체 수 요약
from src.data.charger_access_analysis import (
    build_charger_map_results,
    filter_charger_operation_data,
    summarize_charger_operation_data,
)

# 공통 유틸 함수들입니다.
# - find_default_regions: 사용자가 입력한 검색어를 바탕으로 기본 지역 선택값을 찾음
# - format_number: 숫자를 천 단위 콤마 형식 등 보기 좋게 변환
from src.utils.helpers import find_default_regions, format_number


def render_charger_page(charger_operation_data: pd.DataFrame) -> None:
    # 페이지 상단의 큰 제목을 출력합니다.
    st.header("충전소 위치 / 충전 가능 여부 / 운영 정보")

    # 페이지에 대한 간단한 설명 문구를 출력합니다.
    st.caption("기존 카카오 지역 검색 기능을 유지하면서 운영 정보 참고 데이터를 함께 표시합니다.")

    # 첫 번째 영역의 소제목을 출력합니다.
    st.subheader("지역 기반 충전소 위치 검색")

    # 사용자가 지역명 또는 장소명을 입력할 수 있는 텍스트 입력창을 생성합니다.
    # 예: 서울, 강남구, 부산역, 제주도 등
    search_region = st.text_input(
        "지역 또는 장소 입력",
        value="",
        placeholder="예: 서울, 강남구, 부산역, 제주도",
    )

    # 검색 방식에 대한 안내 박스를 HTML/CSS 스타일과 함께 화면에 출력합니다.
    # 사용자가 입력한 지역명이 내부적으로 "전기차 충전소" 검색어와 결합된다는 점을 설명합니다.
    st.markdown(
        """
        <div style="padding:12px 14px; background:#f6f8fb; border:1px solid #e5e7eb; border-radius:10px; margin-bottom:14px;">
            입력한 지역을 기준으로 <b>전기차 충전소</b>를 검색합니다.<br>
            예: <code>서울</code> 입력 → 내부 검색어: <code>서울 전기차 충전소</code>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 지도 검색 결과를 담을 리스트를 초기화합니다.
    # search_ev_chargers() 호출 결과가 여기에 저장됩니다.
    results = []

    # 검색 과정에서 사용된 디버그 정보를 담을 딕셔너리를 초기화합니다.
    # 예: 실제 사용된 검색어, 에러 메시지 등
    debug_info = {}

    # 사용자가 지역/장소를 입력하지 않은 경우의 처리입니다.
    if not search_region.strip():
        # 안내 문구를 출력합니다.
        st.info("지역 또는 장소를 입력하면 해당 주변의 전기차 충전소를 지도에 표시합니다.")

        # 빈 결과 리스트를 지도에 전달하여 초기 상태의 지도를 렌더링합니다.
        render_kakao_map([])
    else:
        # 사용자가 검색어를 입력한 경우,
        # 카카오 검색 API를 호출하여 충전소 검색 결과와 디버그 정보를 받아옵니다.
        results, debug_info = search_ev_chargers(search_region)

        # 검색 과정에서 에러가 있었다면 경고 문구로 사용자에게 알려줍니다.
        if debug_info.get("error"):
            st.warning(f"검색 중 문제가 발생했습니다: {debug_info['error']}")

        # 실제로 내부에서 사용된 검색어(query_used)가 있으면 화면에 출력합니다.
        # 예: "서울" -> "서울 전기차 충전소"
        query_used = debug_info.get("query_used", "")
        if query_used:
            st.write(f"검색어: `{query_used}`")

        # 검색 결과를 지도에 렌더링합니다.
        render_kakao_map(results)

    # 지도 검색 결과 영역의 제목을 Markdown으로 출력합니다.
    st.markdown("### 지도 검색 결과")

    # 검색 결과가 없으면 경고 문구를 출력합니다.
    if not results:
        st.warning("전기차 충전소 검색 결과가 없습니다. 다른 지역명으로 다시 시도해보세요.")
    else:
        # 검색 결과가 있으면 성공 문구와 함께 검색 건수를 보여줍니다.
        st.success(f"충전소 {len(results)}건을 찾았습니다.")

        # 검색 결과 리스트를 DataFrame으로 변환합니다.
        result_dataframe = pd.DataFrame(results)

        # 화면에 보여줄 컬럼 순서를 정의합니다.
        display_columns = ["name", "road_address", "address", "phone", "category"]

        # 실제로 존재하는 컬럼만 골라서 표시하도록 합니다.
        # 검색 결과에 따라 일부 컬럼이 없을 수도 있기 때문에 안전하게 처리합니다.
        existing_columns = [column_name for column_name in display_columns if column_name in result_dataframe.columns]

        # 검색 결과 DataFrame을 한글 컬럼명으로 바꾸어 화면에 표 형태로 출력합니다.
        st.dataframe(
            result_dataframe[existing_columns].rename(
                columns={
                    "name": "충전소명",
                    "road_address": "도로명주소",
                    "address": "지번주소",
                    "phone": "전화번호",
                    "category": "카테고리",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

    # 첫 번째 영역(지도 검색)과 두 번째 영역(운영 정보 참고 데이터) 사이를 구분하는 구분선을 출력합니다.
    st.divider()

    # 두 번째 영역의 소제목을 출력합니다.
    st.subheader("충전 가능 여부 / 운영 정보 참고 데이터")

    # 전달받은 충전소 운영 정보 DataFrame이 비어 있으면
    # 안내 문구를 출력하고 함수 실행을 종료합니다.
    if charger_operation_data.empty:
        st.info("표시할 충전소 운영 정보 데이터가 없습니다.")
        return

    # 운영 정보 데이터에서 지역 목록(region)을 추출하여 정렬합니다.
    region_list = sorted(charger_operation_data["region"].dropna().unique().tolist())

    # 운영 정보 데이터에서 충전기 유형 목록(charger_type)을 추출하여 정렬합니다.
    charger_type_list = sorted(charger_operation_data["charger_type"].dropna().unique().tolist())

    # 사용자가 위에서 입력한 search_region 값을 기준으로
    # 운영 정보 필터의 기본 선택 지역 목록을 자동으로 찾아냅니다.
    default_region_list = find_default_regions(search_region, region_list)

    # 운영 정보 필터 UI를 3개의 컬럼으로 나누어 배치합니다.
    # 1열: 지역 선택
    # 2열: 충전기 유형 선택
    # 3열: 사용 가능 충전기만 보기 체크박스
    filter_column_1, filter_column_2, filter_column_3 = st.columns(3)

    # 운영 정보 지역 멀티셀렉트를 생성합니다.
    # 기본값으로는 search_region과 유사한 지역들이 자동 선택됩니다.
    selected_regions = filter_column_1.multiselect("운영 정보 지역 선택", region_list, default=default_region_list)

    # 충전기 유형 멀티셀렉트를 생성합니다.
    # 기본값으로는 전체 충전기 유형이 모두 선택된 상태로 시작합니다.
    selected_charger_types = filter_column_2.multiselect("충전기 유형 선택", charger_type_list, default=charger_type_list)

    # 사용 가능 충전기만 표시할지 여부를 체크박스로 받습니다.
    only_available = filter_column_3.checkbox("사용 가능 충전기만 보기", value=False)

    # 위에서 선택한 조건을 바탕으로 충전소 운영 정보 데이터를 필터링합니다.
    filtered_charger_operation_data = filter_charger_operation_data(
        charger_operation_data,
        selected_regions=selected_regions,
        selected_charger_types=selected_charger_types,
        only_available=only_available,
    )

    # 필터링된 운영 정보 데이터를 바탕으로 요약 통계 정보를 계산합니다.
    charger_operation_summary = summarize_charger_operation_data(filtered_charger_operation_data)

    # 상단 핵심 지표를 3개의 컬럼(metric)으로 나누어 배치합니다.
    metric_column_1, metric_column_2, metric_column_3 = st.columns(3)

    # 충전소 수를 metric으로 출력합니다.
    metric_column_1.metric("충전소 수", format_number(charger_operation_summary["charger_station_count"]))

    # 사용 가능 충전기 수를 metric으로 출력합니다.
    metric_column_2.metric("사용 가능 충전기 수", format_number(charger_operation_summary["available_charger_count"]))

    # 전체 충전기 수를 metric으로 출력합니다.
    metric_column_3.metric("전체 충전기 수", format_number(charger_operation_summary["total_charger_count"]))

    # 필터링 결과가 비어 있으면 경고 문구를 출력하고 함수 실행을 종료합니다.
    if filtered_charger_operation_data.empty:
        st.warning("선택한 조건에 맞는 충전소 운영 정보가 없습니다.")
        return

    # 운영 정보 참고 지도 영역의 제목을 출력합니다.
    st.markdown("### 운영 정보 참고 지도")

    # 필터링된 운영 정보 데이터를 지도 표시용 리스트 형태로 변환합니다.
    charger_map_results = build_charger_map_results(filtered_charger_operation_data)

    # 운영 정보 참고 지도를 렌더링합니다.
    render_kakao_map(charger_map_results)

    # 운영 정보 테이블 영역의 제목을 출력합니다.
    st.markdown("### 운영 정보 테이블")

    # 필터링된 운영 정보 DataFrame을 한글 컬럼명으로 바꾸어 표 형태로 출력합니다.
    st.dataframe(
        filtered_charger_operation_data.rename(
            columns={
                "region": "지역",
                "charger_name": "충전소명",
                "charger_type": "충전기 유형",
                "operator": "운영사",
                "status": "운영상태",
                "available_count": "사용 가능 수",
                "total_count": "전체 수",
                "operating_hours": "운영시간",
                "address": "주소",
                "road_address": "상세 위치",
                "phone": "전화번호",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )