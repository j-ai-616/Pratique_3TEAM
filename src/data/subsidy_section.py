import pandas as pd
import streamlit as st


def render_subsidy_section(policy_data: pd.DataFrame) -> None:
    st.subheader("보조금 정책 정보")
    st.caption("national subsidy.xlsx 파일 기준으로 차종별 국고보조금 정보를 조회합니다.")

    if policy_data.empty:
        st.info("표시할 보조금 정책 데이터가 없습니다.")
        return

    sheet_name_list = ["전체"] + sorted(
        policy_data["sheet_name"].dropna().astype(str).unique().tolist()
    )
    vehicle_group_list = ["전체"] + sorted(
        [
            value
            for value in policy_data["vehicle_group"].dropna().astype(str).unique().tolist()
            if value.strip() != ""
        ]
    )
    manufacturer_list = ["전체"] + sorted(
        [
            value
            for value in policy_data["manufacturer"].dropna().astype(str).unique().tolist()
            if value.strip() != ""
        ]
    )

    filter_column_1, filter_column_2, filter_column_3 = st.columns(3)
    selected_sheet_name = filter_column_1.selectbox("차량 유형 시트 선택", sheet_name_list)
    selected_vehicle_group = filter_column_2.selectbox("구분 선택", vehicle_group_list)
    selected_manufacturer = filter_column_3.selectbox("제조사 선택", manufacturer_list)

    subsidy_keyword = st.text_input(
        "차종 검색",
        value="",
        placeholder="예: 넥쏘, 포터, 코나, 카운티",
    )

    filtered_policy_data = policy_data.copy()

    if selected_sheet_name != "전체":
        filtered_policy_data = filtered_policy_data[
            filtered_policy_data["sheet_name"] == selected_sheet_name
        ]

    if selected_vehicle_group != "전체":
        filtered_policy_data = filtered_policy_data[
            filtered_policy_data["vehicle_group"] == selected_vehicle_group
        ]

    if selected_manufacturer != "전체":
        filtered_policy_data = filtered_policy_data[
            filtered_policy_data["manufacturer"] == selected_manufacturer
        ]

    if subsidy_keyword.strip():
        subsidy_keyword = subsidy_keyword.strip()
        filtered_policy_data = filtered_policy_data[
            filtered_policy_data["model_name"].astype(str).str.contains(
                subsidy_keyword,
                case=False,
                na=False,
            )
        ]

    metric_column_1, metric_column_2, metric_column_3 = st.columns(3)
    metric_column_1.metric("조회 차종 수", f"{len(filtered_policy_data):,}개")

    if not filtered_policy_data.empty and "subsidy_amount" in filtered_policy_data.columns:
        max_subsidy = filtered_policy_data["subsidy_amount"].max()
        avg_subsidy = filtered_policy_data["subsidy_amount"].mean()

        metric_column_2.metric(
            "최대 보조금",
            f"{max_subsidy:,.0f} 만원" if pd.notna(max_subsidy) else "-",
        )
        metric_column_3.metric(
            "평균 보조금",
            f"{avg_subsidy:,.1f} 만원" if pd.notna(avg_subsidy) else "-",
        )
    else:
        metric_column_2.metric("최대 보조금", "-")
        metric_column_3.metric("평균 보조금", "-")

    if filtered_policy_data.empty:
        st.warning("선택한 조건에 맞는 보조금 정보가 없습니다.")
        return

    display_policy_data = filtered_policy_data.copy()

# 차량분류 공란 처리
    if "vehicle_class" in display_policy_data.columns:
        display_policy_data["vehicle_class"] = (
            display_policy_data["vehicle_class"]
            .astype(str)
            .str.strip()
            .replace(["", "nan", "None"], "미분류")
        )   

    if "subsidy_amount" in display_policy_data.columns:
        display_policy_data["subsidy_amount"] = pd.to_numeric(
            display_policy_data["subsidy_amount"],
            errors="coerce",
        )

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