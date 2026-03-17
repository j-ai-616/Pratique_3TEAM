import pandas as pd
import streamlit as st


def _parse_subsidy_range_value(value) -> tuple[float | None, float | None]:
    """
    보조금 문자열을 최소값, 최대값으로 파싱합니다.

    예)
    280 -> (280, 280)
    200~484 -> (200, 484)
    1,000~1,250 -> (1000, 1250)
    - -> (None, None)
    """
    if pd.isna(value):
        return None, None

    text = str(value).strip().replace(",", "")

    if text in {"", "-", "없음", "미정", "nan", "None"}:
        return None, None

    if "~" in text:
        left, right = text.split("~", 1)

        try:
            min_value = float(left.strip())
        except ValueError:
            min_value = None

        try:
            max_value = float(right.strip())
        except ValueError:
            max_value = None

        return min_value, max_value

    try:
        number = float(text)
        return number, number
    except ValueError:
        return None, None


def render_local_subsidy_section(local_subsidy_data: pd.DataFrame) -> None:
    st.subheader("지자체 보조금 정책 정보")
    st.caption("무공해_지자체_보조금.xlsx 파일 기준으로 지역별 전기차/수소차 보조금을 조회합니다.")

    if local_subsidy_data.empty:
        st.info("표시할 지자체 보조금 데이터가 없습니다.")
        return

    display_local_subsidy_data = local_subsidy_data.copy()

    # ---------------------------
    # 1. 필터 UI
    # ---------------------------
    region_list = ["전체"] + sorted(
        display_local_subsidy_data["region"].dropna().astype(str).unique().tolist()
    )

    filter_col_1, filter_col_2, filter_col_3 = st.columns(3)

    selected_region = filter_col_1.selectbox(
        "시도 선택",
        region_list,
        key="local_subsidy_region",
    )

    vehicle_type = filter_col_2.selectbox(
        "차량 유형 선택",
        ["전체", "전기자동차", "수소자동차"],
        key="local_subsidy_vehicle_type",
    )

    search_keyword = filter_col_3.text_input(
        "지역 검색",
        value="",
        placeholder="예: 서울, 경기, 제주",
        key="local_subsidy_keyword",
    )

    # ---------------------------
    # 2. 데이터 필터링
    # ---------------------------
    if selected_region != "전체":
        display_local_subsidy_data = display_local_subsidy_data[
            display_local_subsidy_data["region"] == selected_region
        ]

    if search_keyword.strip():
        keyword = search_keyword.strip()
        display_local_subsidy_data = display_local_subsidy_data[
            display_local_subsidy_data["region"].astype(str).str.contains(
                keyword,
                case=False,
                na=False,
            )
        ]

    # ---------------------------
    # 3. metric 계산
    # ---------------------------
    ev_min_values = []
    ev_max_values = []
    hydrogen_min_values = []
    hydrogen_max_values = []

    for _, row in display_local_subsidy_data.iterrows():
        ev_min, ev_max = _parse_subsidy_range_value(row.get("ev_subsidy"))
        h_min, h_max = _parse_subsidy_range_value(row.get("hydrogen_subsidy"))

        if ev_min is not None:
            ev_min_values.append(ev_min)
        if ev_max is not None:
            ev_max_values.append(ev_max)

        if h_min is not None:
            hydrogen_min_values.append(h_min)
        if h_max is not None:
            hydrogen_max_values.append(h_max)

    metric_col_1, metric_col_2, metric_col_3 = st.columns(3)

    metric_col_1.metric("조회 지역 수", f"{len(display_local_subsidy_data):,}개")

    if vehicle_type == "전체":
        ev_text = f"{max(ev_max_values):,.0f} 만원" if ev_max_values else "-"
        h_text = f"{max(hydrogen_max_values):,.0f} 만원" if hydrogen_max_values else "-"
        metric_col_2.metric("전기차 최대 보조금", ev_text)
        metric_col_3.metric("수소차 최대 보조금", h_text)

    elif vehicle_type == "전기자동차":
        ev_text = f"{max(ev_max_values):,.0f} 만원" if ev_max_values else "-"
        avg_ev = f"{sum(ev_max_values) / len(ev_max_values):,.1f} 만원" if ev_max_values else "-"
        metric_col_2.metric("전기차 최대 보조금", ev_text)
        metric_col_3.metric("전기차 평균 최대치", avg_ev)

    else:
        h_text = f"{max(hydrogen_max_values):,.0f} 만원" if hydrogen_max_values else "-"
        avg_h = (
            f"{sum(hydrogen_max_values) / len(hydrogen_max_values):,.1f} 만원"
            if hydrogen_max_values else "-"
        )
        metric_col_2.metric("수소차 최대 보조금", h_text)
        metric_col_3.metric("수소차 평균 최대치", avg_h)

    if display_local_subsidy_data.empty:
        st.warning("선택한 조건에 맞는 지자체 보조금 정보가 없습니다.")
        return

    # ---------------------------
    # 4. 차량 유형별 출력 컬럼 구성
    # ---------------------------
    if vehicle_type == "전기자동차":
        result_df = display_local_subsidy_data[["region", "ev_subsidy"]].copy()
        result_df = result_df.rename(
            columns={
                "region": "시도",
                "ev_subsidy": "전기자동차 보조금(만원)",
            }
        )

    elif vehicle_type == "수소자동차":
        result_df = display_local_subsidy_data[["region", "hydrogen_subsidy"]].copy()
        result_df = result_df.rename(
            columns={
                "region": "시도",
                "hydrogen_subsidy": "수소자동차 보조금(만원)",
            }
        )

    else:
        result_df = display_local_subsidy_data[["region", "ev_subsidy", "hydrogen_subsidy"]].copy()
        result_df = result_df.rename(
            columns={
                "region": "시도",
                "ev_subsidy": "전기자동차 보조금(만원)",
                "hydrogen_subsidy": "수소자동차 보조금(만원)",
            }
        )

    st.dataframe(
        result_df,
        use_container_width=True,
        hide_index=True,
    )

    with st.expander("보조금 값 해석 안내"):
        st.markdown(
            """
            - `280` : 해당 지역의 고정 보조금입니다.
            - `200~484` : 세부 시·군·구 또는 차량 조건에 따라 달라지는 범위형 보조금입니다.
            - `-` : 지원 없음 또는 별도 확인이 필요한 항목입니다.
            """
        )


def render_local_subsidy_page(local_subsidy_data: pd.DataFrame) -> None:
    st.header("지자체 보조금 정책")
    st.caption("지역별 전기자동차 / 수소자동차 보조금 정보를 확인할 수 있습니다.")

    render_local_subsidy_section(local_subsidy_data)