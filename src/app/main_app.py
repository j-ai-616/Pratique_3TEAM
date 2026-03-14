import os
import sys

import pandas as pd
import streamlit as st

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.db.query_data import (
    get_region_names,
    get_charge_types,
    get_status_names,
    get_charger_data,
)
import src.map.kakao_map as kakao_map


# --------------------------------------------------
# 기본 설정
# --------------------------------------------------
st.set_page_config(
    page_title="전국 전기차 충전소 조회",
    page_icon="⚡",
    layout="wide",
)

st.title("전국 전기차 충전소 조회")
st.caption("MySQL에 적재된 충전소/충전기 데이터를 조회하고 카카오맵에 함께 표시합니다.")


# --------------------------------------------------
# 필터 옵션 불러오기
# --------------------------------------------------
region_options = ["전체"] + get_region_names()
charge_type_options = ["전체"] + get_charge_types()
status_options = ["전체"] + get_status_names()

col1, col2, col3 = st.columns(3)

with col1:
    selected_region = st.selectbox("지역 선택", region_options)

with col2:
    selected_charge_type = st.selectbox("충전방식", charge_type_options)

with col3:
    selected_status = st.selectbox("상태", status_options)


# --------------------------------------------------
# 데이터 조회
# --------------------------------------------------
df = get_charger_data(
    region_name=selected_region,
    charge_type=selected_charge_type,
    status_name=selected_status,
)


# --------------------------------------------------
# 요약 지표
# --------------------------------------------------
st.markdown("## 조회 결과 요약")

summary_col1, summary_col2 = st.columns(2)

with summary_col1:
    st.metric("조회 건수", len(df))

station_df = pd.DataFrame()
if not df.empty:
    station_df = df.copy()

    if "station_source_id" in station_df.columns and station_df["station_source_id"].notna().any():
        station_df = station_df.drop_duplicates(subset=["station_source_id"])
    elif "station_id" in station_df.columns and station_df["station_id"].notna().any():
        station_df = station_df.drop_duplicates(subset=["station_id"])
    else:
        station_df = station_df.drop_duplicates(subset=["station_name", "address"])

with summary_col2:
    st.metric("충전소 수", len(station_df))


# --------------------------------------------------
# 지도 데이터 생성
# --------------------------------------------------
st.markdown("## 카카오맵")

map_results = []

if not station_df.empty:
    station_df = station_df.copy()

    station_df["latitude"] = pd.to_numeric(station_df["latitude"], errors="coerce")
    station_df["longitude"] = pd.to_numeric(station_df["longitude"], errors="coerce")

    station_df = station_df.dropna(subset=["latitude", "longitude"])

    for _, row in station_df.iterrows():
        station_name = row.get("station_name") if pd.notna(row.get("station_name")) else ""
        address = row.get("address") if pd.notna(row.get("address")) else ""
        phone = row.get("phone") if pd.notna(row.get("phone")) else ""
        region_name = row.get("region_name") if pd.notna(row.get("region_name")) else ""
        operator_name = row.get("operator_name") if pd.notna(row.get("operator_name")) else ""

        map_results.append(
            {
                "name": station_name,
                "lat": float(row["latitude"]),
                "lng": float(row["longitude"]),
                "address": address,
                "road_address": address,
                "phone": phone,
                "category": f"{region_name} / {operator_name}",
                "place_url": "",
            }
        )

kakao_map.render_kakao_map(map_results)


# --------------------------------------------------
# 충전소 목록
# --------------------------------------------------
st.markdown("## 충전소 목록")

if df.empty:
    st.warning("조건에 맞는 충전소 데이터가 없습니다.")
else:
    display_df = df.copy()

    keep_cols = [
        "region_name",
        "station_name",
        "address",
        "charge_type",
        "status_name",
        "operator_name",
        "available_time",
        "phone",
    ]
    display_df = display_df[keep_cols]

    for col in display_df.columns:
        display_df = display_df[display_df[col].astype(str).str.strip() != col]

    display_df = display_df.rename(
        columns={
            "region_name": "지역명",
            "station_name": "충전소명",
            "address": "주소",
            "charge_type": "충전방식",
            "status_name": "상태명",
            "operator_name": "운영기관",
            "available_time": "이용가능시간",
            "phone": "연락처",
        }
    )

    # null / None / nan 치환
    display_df = display_df.fillna("-")
    display_df = display_df.replace("None", "-")
    display_df = display_df.replace("nan", "-")
    display_df = display_df.replace("NaN", "-")

    # 컬럼별 대체 문구
    display_df["지역명"] = display_df["지역명"].replace("-", "미분류")
    display_df["충전방식"] = display_df["충전방식"].replace("-", "정보없음")
    display_df["상태명"] = display_df["상태명"].replace("-", "정보없음")
    display_df["운영기관"] = display_df["운영기관"].replace("-", "정보없음")

    st.dataframe(display_df, use_container_width=True, hide_index=True)