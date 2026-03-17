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

import pandas as pd
import streamlit as st

from src.map.map_service import search_ev_chargers
from src.map.kakao_map import render_kakao_map
from src.data.charger_access_analysis import (
    build_charger_map_results,
    filter_charger_operation_data,
    summarize_charger_operation_data,
)
from src.utils.helpers import find_default_regions, format_number


def render_charger_page(charger_operation_data: pd.DataFrame) -> None:
    st.header("충전소 위치 / 충전 가능 여부 / 운영 정보")
    st.caption("기존 카카오 지역 검색 기능을 유지하면서 운영 정보 참고 데이터를 함께 표시합니다.")

    st.subheader("지역 기반 충전소 위치 검색")

    search_region = st.text_input(
        "지역 또는 장소 입력",
        value="",
        placeholder="예: 서울, 강남구, 부산역, 제주도",
    )

    st.markdown(
        """
        <div style="padding:12px 14px; background:#f6f8fb; border:1px solid #e5e7eb; border-radius:10px; margin-bottom:14px;">
            입력한 지역을 기준으로 <b>전기차 충전소</b>를 검색합니다.<br>
            예: <code>서울</code> 입력 → 내부 검색어: <code>서울 전기차 충전소</code>
        </div>
        """,
        unsafe_allow_html=True,
    )

    results = []
    debug_info = {}

    st.markdown("### 지도 검색 결과")

    if not search_region.strip():
        st.info("지역 또는 장소를 입력하면 해당 주변의 전기차 충전소를 지도에 표시합니다.")
        render_kakao_map([])
    else:
        results, debug_info = search_ev_chargers(search_region)

        if debug_info.get("error"):
            st.warning(f"검색 중 문제가 발생했습니다: {debug_info['error']}")

        query_used = debug_info.get("query_used", "")
        if query_used:
            st.write(f"검색어: `{query_used}`")

        if results:
            st.caption(f"지도 렌더링 대상: {len(results)}건")
            render_kakao_map(results)
        else:
            st.warning("전기차 충전소 검색 결과가 없습니다. 다른 지역명으로 다시 시도해보세요.")

    if results:
        st.success(f"충전소 {len(results)}건을 찾았습니다.")

        result_dataframe = pd.DataFrame(results)

        display_columns = ["name", "road_address", "address", "phone", "category"]
        existing_columns = [column_name for column_name in display_columns if column_name in result_dataframe.columns]

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

    st.divider()

    st.subheader("충전 가능 여부 / 운영 정보 참고 데이터")

    if charger_operation_data.empty:
        st.info("표시할 충전소 운영 정보 데이터가 없습니다.")
        return

    region_list = sorted(charger_operation_data["region"].dropna().unique().tolist())
    charger_type_list = sorted(charger_operation_data["charger_type"].dropna().unique().tolist())

    default_region_list = find_default_regions(search_region, region_list)

    filter_column_1, filter_column_2, filter_column_3 = st.columns(3)

    selected_regions = filter_column_1.multiselect("운영 정보 지역 선택", region_list, default=default_region_list)
    selected_charger_types = filter_column_2.multiselect("충전기 유형 선택", charger_type_list, default=charger_type_list)
    only_available = filter_column_3.checkbox("사용 가능 충전기만 보기", value=False)

    filtered_charger_operation_data = filter_charger_operation_data(
        charger_operation_data,
        selected_regions=selected_regions,
        selected_charger_types=selected_charger_types,
        only_available=only_available,
    )

    charger_operation_summary = summarize_charger_operation_data(filtered_charger_operation_data)

    metric_column_1, metric_column_2, metric_column_3 = st.columns(3)

    metric_column_1.metric("충전소 수", format_number(charger_operation_summary["charger_station_count"]))
    metric_column_2.metric("사용 가능 충전기 수", format_number(charger_operation_summary["available_charger_count"]))
    metric_column_3.metric("전체 충전기 수", format_number(charger_operation_summary["total_charger_count"]))

    if filtered_charger_operation_data.empty:
        st.warning("선택한 조건에 맞는 충전소 운영 정보가 없습니다.")
        return

    st.markdown("### 운영 정보 참고 지도")

    charger_map_results = build_charger_map_results(filtered_charger_operation_data)
    render_kakao_map(charger_map_results)

    st.markdown("### 운영 정보 테이블")

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