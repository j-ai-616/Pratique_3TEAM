import html
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pandas as pd
import streamlit as st

from src.config.settings import KAKAO_REST_API_KEY, KAKAO_JAVASCRIPT_KEY
from src.map.map_service import search_ev_chargers
from src.map.kakao_map import render_kakao_map
from src.db.query_data import (
    load_charger_operation_data,
    load_charging_fee_data,
    load_ev_registration_data,
    load_faq_data,
    load_news_keyword_data,
    load_policy_data,
    resolve_news_wordcloud_path,
)
from src.data.charger_access_analysis import (
    build_charger_map_results,
    filter_charger_operation_data,
    summarize_charger_operation_data,
)
from src.data.region_ev_analysis import (
    build_region_ev_trend,
    filter_region_ev_data,
    summarize_region_ev_data,
)
from src.data.region_ev_section import render_region_ev_page
from src.utils.helpers import find_default_regions, format_number
from src.data.faq_section import render_faq_section
from src.data.subsidy_section import render_subsidy_section
from src.data.news_analysis_section import render_news_analysis_section


MENU_REGION_EV = "1. 지역 별 전기차 등록 현황"
MENU_CHARGER = "2. 충전소 위치 / 충전 가능 여부 / 운영 정보"
MENU_CHARGING_FEE = "3. 충전 요금 관련"
MENU_SUBSIDY = "4. 보조금 정책"
MENU_FAQ = "5. 서울시 전기차 FAQ"
MENU_NEWS = "6. 뉴스 기사 분석"


@st.cache_data(show_spinner=False)
def load_dashboard_data():
    return {
        "ev_registration_data": load_ev_registration_data(),
        "charger_operation_data": load_charger_operation_data(),
        "charging_fee_data": load_charging_fee_data(),
        "policy_data": load_policy_data(),
        "faq_data": load_faq_data(),
        "news_keyword_data": load_news_keyword_data(),
    }


def render_sidebar() -> str:
    with st.sidebar:
        st.title("⚡ EV 정보 포털")
        st.caption("메뉴를 선택하면 전기차 관련 정보를 확인할 수 있습니다.")

        selected_menu = st.radio(
            "메뉴 선택",
            [
                MENU_REGION_EV,
                MENU_CHARGER,
                MENU_CHARGING_FEE,
                MENU_SUBSIDY,
                MENU_FAQ,
                MENU_NEWS,
            ],
            label_visibility="collapsed",
        )

    return selected_menu

def render_charger_page(charger_operation_data: pd.DataFrame) -> None:
    st.header(MENU_CHARGER)
    st.caption("기존 카카오 지역 검색 기능을 유지하면서 운영 정보 참고 데이터를 함께 표시합니다.")

    st.subheader("지역 기반 충전소 검색")
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

        render_kakao_map(results)

    st.markdown("### 지도 검색 결과")
    if not results:
        st.warning("전기차 충전소 검색 결과가 없습니다. 다른 지역명으로 다시 시도해보세요.")
    else:
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


def render_charging_fee_page(charging_fee_data: pd.DataFrame) -> None:
    st.header(MENU_CHARGING_FEE)
    st.caption("운영사와 충전기 유형별 참고 단가를 확인하고 예상 충전 비용을 계산합니다.")

    if charging_fee_data.empty:
        st.info("표시할 충전 요금 데이터가 없습니다.")
        return

    operator_list = sorted(charging_fee_data["operator"].dropna().unique().tolist())
    charger_type_list = sorted(charging_fee_data["charger_type"].dropna().unique().tolist())

    filter_column_1, filter_column_2 = st.columns(2)
    selected_operator = filter_column_1.selectbox("운영사 선택", operator_list)
    selected_charger_type = filter_column_2.selectbox("충전기 유형 선택", charger_type_list)

    filtered_charging_fee_data = charging_fee_data[
        (charging_fee_data["operator"] == selected_operator)
        & (charging_fee_data["charger_type"] == selected_charger_type)
    ].copy()

    st.subheader("충전 요금 기준표")
    st.dataframe(
        charging_fee_data.rename(
            columns={
                "operator": "운영사",
                "charger_type": "충전기 유형",
                "base_price_per_kwh": "기본 단가(원/kWh)",
                "member_price_per_kwh": "회원 단가(원/kWh)",
                "non_member_price_per_kwh": "비회원 단가(원/kWh)",
                "note": "비고",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("예상 충전 비용 계산기")
    charging_kwh = st.slider("충전량(kWh)", min_value=5, max_value=100, value=40, step=5)
    price_type = st.radio("요금 유형", ["기본 요금", "회원 요금", "비회원 요금"], horizontal=True)

    if filtered_charging_fee_data.empty:
        st.warning("선택한 조건에 맞는 요금 데이터가 없습니다.")
        return

    selected_fee_row = filtered_charging_fee_data.iloc[0]
    if price_type == "회원 요금":
        selected_unit_price = float(selected_fee_row["member_price_per_kwh"])
    elif price_type == "비회원 요금":
        selected_unit_price = float(selected_fee_row["non_member_price_per_kwh"])
    else:
        selected_unit_price = float(selected_fee_row["base_price_per_kwh"])

    expected_charging_fee = round(charging_kwh * selected_unit_price)

    metric_column_1, metric_column_2, metric_column_3 = st.columns(3)
    metric_column_1.metric("선택 단가", f"{selected_unit_price:,.1f} 원/kWh")
    metric_column_2.metric("충전량", f"{charging_kwh} kWh")
    metric_column_3.metric("예상 비용", f"{expected_charging_fee:,.0f} 원")

    if pd.notna(selected_fee_row.get("note")) and str(selected_fee_row.get("note")).strip():
        st.caption(f"참고: {selected_fee_row['note']}")

    st.info("실제 충전 요금은 운영사 정책, 시간대, 제휴 할인, 결제 수단 등에 따라 달라질 수 있습니다.")


def render_subsidy_page(policy_data: pd.DataFrame) -> None:
    st.header(MENU_SUBSIDY)
    st.caption("보조금 기준표를 별도 페이지로 분리해 더 짧고 명확하게 확인할 수 있습니다.")
    render_subsidy_section(policy_data)


def render_faq_page(faq_data: pd.DataFrame) -> None:
    st.header(MENU_FAQ)
    st.caption("보조금 정책과 분리된 서울시 전기차 FAQ 페이지입니다. 차량군 필터로 원하는 질문만 빠르게 볼 수 있습니다.")
    render_faq_section(
        faq_data,
        section_title="서울시 전기차 FAQ",
        section_caption="분류 필터에서 전체, 전기승용/화물/승합, 전기이륜 중 원하는 항목을 선택해 조회하세요.",
    )


def render_news_page(news_keyword_data: pd.DataFrame) -> None:
    st.header(MENU_NEWS)
    render_news_analysis_section(
        news_keyword_data=news_keyword_data,
        wordcloud_path=resolve_news_wordcloud_path(),
    )


def main() -> None:
    st.set_page_config(page_title="전기차 정보 포털", page_icon="⚡", layout="wide")

    st.title("전기차 정보 포털")
    
    selected_menu = render_sidebar()
    dashboard_data = load_dashboard_data()

    if selected_menu == MENU_REGION_EV:
        render_region_ev_page(dashboard_data["ev_registration_data"])
    elif selected_menu == MENU_CHARGER:
        render_charger_page(dashboard_data["charger_operation_data"])
    elif selected_menu == MENU_CHARGING_FEE:
        render_charging_fee_page(dashboard_data["charging_fee_data"])
    elif selected_menu == MENU_SUBSIDY:
        render_subsidy_page(dashboard_data["policy_data"])
    elif selected_menu == MENU_FAQ:
        render_faq_page(dashboard_data["faq_data"])
    else:
        render_news_page(dashboard_data["news_keyword_data"])


if __name__ == "__main__":
    main()
