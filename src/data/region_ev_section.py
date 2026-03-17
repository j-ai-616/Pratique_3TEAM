from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import create_engine

from src.config.settings import get_mysql_config


@st.cache_resource
def get_db_engine():
    mysql_config = get_mysql_config()
    db_user = mysql_config.get("user")
    db_password = mysql_config.get("password")
    db_host = mysql_config.get("host", "127.0.0.1")
    db_port = mysql_config.get("port", "3306")
    db_name = mysql_config.get("database")

    if not all([db_user, db_password, db_name]):
        raise ValueError("MySQL 접속 정보가 없습니다.")

    db_url = (
        f"mysql+pymysql://{db_user}:{db_password}"
        f"@{db_host}:{db_port}/{db_name}?charset=utf8mb4"
    )
    return create_engine(db_url)


@st.cache_data(ttl=300)
def _read_sql_df(query: str) -> pd.DataFrame:
    engine = get_db_engine()
    return pd.read_sql(query, con=engine)


@st.cache_data(ttl=300)
def _load_monthly_data_from_db() -> pd.DataFrame:
    query = """
    SELECT
        base_ym,
        year_num,
        month_num,
        region_name,
        region_order,
        cumulative_count,
        monthly_increase,
        yoy_diff,
        share_pct,
        is_latest_ym
    FROM vw_ev_registration_monthly
    ORDER BY region_order, base_ym
    """
    df = _read_sql_df(query)
    return _standardize_monthly_df(df)


@st.cache_data(show_spinner=False)
def _build_monthly_data_from_file(ev_registration_data: pd.DataFrame) -> pd.DataFrame:
    df = ev_registration_data.copy()
    if df.empty:
        return pd.DataFrame(columns=[
            "base_ym", "year_num", "month_num", "region_name", "region_order",
            "cumulative_count", "monthly_increase", "yoy_diff", "share_pct", "is_latest_ym"
        ])

    df = df.rename(columns={"year_month": "base_ym", "region": "region_name", "ev_count": "cumulative_count"})
    df["base_ym"] = pd.to_datetime(df["base_ym"], errors="coerce")
    df["cumulative_count"] = pd.to_numeric(df["cumulative_count"], errors="coerce")
    df = df.dropna(subset=["base_ym", "region_name", "cumulative_count"]).copy()
    df = df.sort_values(["region_name", "base_ym"]).reset_index(drop=True)

    order = ["합계", "서울", "경기", "인천", "부산", "대구", "광주", "대전", "울산", "세종", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"]
    region_order_map = {name: idx for idx, name in enumerate(order, start=1)}

    df["year_num"] = df["base_ym"].dt.year
    df["month_num"] = df["base_ym"].dt.month
    df["region_order"] = df["region_name"].map(region_order_map).fillna(999)
    df["monthly_increase"] = df.groupby("region_name")["cumulative_count"].diff()
    df.loc[df.groupby("region_name").head(1).index, "monthly_increase"] = pd.NA
    df["yoy_diff"] = df.groupby("region_name")["cumulative_count"].diff(12)

    totals = df.groupby("base_ym", as_index=False)["cumulative_count"].sum()
    totals["region_name"] = "합계"
    totals["year_num"] = totals["base_ym"].dt.year
    totals["month_num"] = totals["base_ym"].dt.month
    totals["region_order"] = 1
    totals = totals.sort_values("base_ym").reset_index(drop=True)
    totals["monthly_increase"] = totals["cumulative_count"].diff()
    totals["yoy_diff"] = totals["cumulative_count"].diff(12)

    combined = pd.concat([totals, df], ignore_index=True, sort=False)
    combined["share_pct"] = combined.groupby("base_ym")["cumulative_count"].transform(
        lambda s: (s / s[s.index[s.eq(s.max())][0]] * 100) if len(s) else pd.NA
    )
    # recompute share against total only
    total_map = totals.set_index("base_ym")["cumulative_count"]
    combined["share_pct"] = (combined["cumulative_count"] / combined["base_ym"].map(total_map) * 100)
    combined.loc[combined["region_name"] == "합계", "share_pct"] = 100.0
    latest_ym = combined["base_ym"].max()
    combined["is_latest_ym"] = (combined["base_ym"] == latest_ym).astype(int)
    return _standardize_monthly_df(combined)


def _standardize_monthly_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    df["base_ym"] = pd.to_datetime(df["base_ym"], errors="coerce")
    numeric_cols = [
        "year_num", "month_num", "region_order", "cumulative_count",
        "monthly_increase", "yoy_diff", "share_pct"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["base_ym", "region_name"]).copy()
    return df.sort_values(["region_order", "region_name", "base_ym"]).reset_index(drop=True)


def format_int(x):
    if pd.isna(x):
        return "-"
    return f"{int(x):,}"


def recent_months_filter(df: pd.DataFrame, months: int):
    if months == 0 or df.empty:
        return df.copy()
    max_date = df["base_ym"].max()
    min_date = max_date - pd.DateOffset(months=months - 1)
    return df[df["base_ym"] >= min_date].copy()


def get_latest_snapshot(monthly_df: pd.DataFrame):
    latest_ym = monthly_df["base_ym"].max()
    return monthly_df[monthly_df["base_ym"] == latest_ym].copy(), latest_ym


def get_last_12m_increase(df: pd.DataFrame):
    max_date = df["base_ym"].max()
    min_date = max_date - pd.DateOffset(months=11)
    temp = df[df["base_ym"] >= min_date].copy()
    result = (
        temp.groupby("region_name", as_index=False)["monthly_increase"]
        .sum(min_count=1)
        .rename(columns={"monthly_increase": "last_12m_increase"})
    )
    return result


def get_share_change_12m(df_non_total: pd.DataFrame):
    latest_date = df_non_total["base_ym"].max()
    prev_12m_date = latest_date - pd.DateOffset(months=12)
    latest_df = df_non_total[df_non_total["base_ym"] == latest_date][["region_name", "share_pct"]].copy()
    latest_df = latest_df.rename(columns={"share_pct": "latest_share_pct"})
    prev_df = df_non_total[df_non_total["base_ym"] == prev_12m_date][["region_name", "share_pct"]].copy()
    prev_df = prev_df.rename(columns={"share_pct": "prev_share_pct"})
    merged = latest_df.merge(prev_df, on="region_name", how="left")
    merged["share_change_12m"] = merged["latest_share_pct"] - merged["prev_share_pct"]
    return merged


def make_yearly_from_monthly(monthly_df: pd.DataFrame) -> pd.DataFrame:
    temp = monthly_df.copy()
    temp = temp.dropna(subset=["region_name", "year_num", "monthly_increase"]).copy()
    yearly = (
        temp.groupby(["region_name", "region_order", "year_num"], as_index=False)["monthly_increase"]
        .sum(min_count=1)
        .rename(columns={"monthly_increase": "yearly_increase"})
    )
    return yearly


def build_heatmap_source(total_df: pd.DataFrame) -> pd.DataFrame:
    temp = total_df.copy()
    temp = temp.dropna(subset=["base_ym", "monthly_increase"]).copy()
    temp["year"] = temp["base_ym"].dt.year
    temp["month"] = temp["base_ym"].dt.month
    pivot_df = temp.pivot_table(index="year", columns="month", values="monthly_increase", aggfunc="sum")
    pivot_df = pivot_df.sort_index().reindex(columns=list(range(1, 13)))
    return pivot_df


def line_chart(df, x, y, color=None, title="", y_title=""):
    fig = px.line(df, x=x, y=y, color=color, title=title, markers=True)
    fig.update_layout(height=420, hovermode="x unified", xaxis_title="기준월" if x == "base_ym" else x, yaxis_title=y_title or y, margin=dict(l=20, r=20, t=60, b=20))
    return fig


def bar_chart(df, x, y, color=None, title="", y_title="", barmode="group"):
    fig = px.bar(df, x=x, y=y, color=color, title=title, barmode=barmode)
    fig.update_layout(height=420, hovermode="x unified", xaxis_title="기준월" if x == "base_ym" else x, yaxis_title=y_title or y, margin=dict(l=20, r=20, t=60, b=20))
    return fig


def horizontal_bar(df, x, y, title="", x_title=""):
    fig = px.bar(df, x=x, y=y, orientation="h", title=title)
    fig.update_layout(height=440, xaxis_title=x_title or x, yaxis_title="지역", margin=dict(l=20, r=20, t=60, b=20))
    fig.update_yaxes(categoryorder="total ascending")
    return fig


def donut_chart(df, names, values, title=""):
    fig = px.pie(df, names=names, values=values, hole=0.45, title=title)
    fig.update_layout(height=440, margin=dict(l=20, r=20, t=60, b=20))
    return fig


def heatmap_chart(pivot_df, title="전국 월별 순증 히트맵"):
    fig = go.Figure(data=go.Heatmap(z=pivot_df.values, x=[f"{m}월" for m in pivot_df.columns], y=pivot_df.index.astype(str), hovertemplate="연도=%{y}<br>월=%{x}<br>순증=%{z:,}<extra></extra>"))
    fig.update_layout(title=title, height=430, xaxis_title="월", yaxis_title="연도", margin=dict(l=20, r=20, t=60, b=20))
    return fig


def render_region_ev_page(ev_registration_data: pd.DataFrame) -> None:
    st.header("지역별 전기차 등록 현황")
    st.caption("원격 DB가 연결되면 DB 데이터를 사용하고, 연결되지 않으면 프로젝트 파일 데이터를 사용합니다.")

    monthly_df = pd.DataFrame()
    source_label = None
    db_error = None

    try:
        monthly_df = _load_monthly_data_from_db()
        source_label = "MySQL DB"
    except Exception as e:
        db_error = str(e)
        monthly_df = _build_monthly_data_from_file(ev_registration_data)
        source_label = "프로젝트 파일"

    if monthly_df.empty:
        st.warning("지역별 전기차 등록 현황 데이터가 없습니다.")
        if db_error:
            st.error(f"DB 연결 실패: {db_error}")
        return

    if db_error:
        st.info("Cloud에서는 localhost(127.0.0.1) MySQL에 접속할 수 없어 파일 데이터로 표시 중입니다.")
    st.caption(f"현재 데이터 소스: {source_label}")

    yearly_df = make_yearly_from_monthly(monthly_df)
    all_regions = monthly_df.loc[monthly_df["region_name"] != "합계", "region_name"].drop_duplicates().tolist()
    total_df = monthly_df[monthly_df["region_name"] == "합계"].copy()
    region_df = monthly_df[monthly_df["region_name"] != "합계"].copy()
    latest_snapshot_all, latest_ym = get_latest_snapshot(monthly_df)
    latest_total_df = latest_snapshot_all[latest_snapshot_all["region_name"] == "합계"]
    if latest_total_df.empty:
        st.warning("합계 데이터가 없습니다.")
        return
    latest_total = latest_total_df.iloc[0]

    default_regions = [r for r in ["서울", "경기", "인천", "부산", "제주"] if r in all_regions] or all_regions[:5]
    col1, col2 = st.columns([2,1])
    selected_regions = col1.multiselect("비교 지역 선택", options=all_regions, default=default_regions)
    period_label = col2.selectbox("차트 기간", options=["최근 12개월", "최근 24개월", "최근 36개월", "전체"], index=1)
    period_map = {"최근 12개월": 12, "최근 24개월": 24, "최근 36개월": 36, "전체": 0}
    selected_months = period_map[period_label]

    filtered_total_df = recent_months_filter(total_df, selected_months)
    filtered_region_df = recent_months_filter(region_df, selected_months)
    if selected_regions:
        filtered_region_df = filtered_region_df[filtered_region_df["region_name"].isin(selected_regions)].copy()
    filtered_yearly_df = yearly_df[yearly_df["region_name"].isin((selected_regions or all_regions) + ["합계"])].copy()
    latest_region_snapshot = region_df[region_df["base_ym"] == latest_ym].copy()
    if selected_regions:
        latest_region_snapshot = latest_region_snapshot[latest_region_snapshot["region_name"].isin(selected_regions)].copy()
    last12m_region_df = get_last_12m_increase(region_df)
    share_change_df = get_share_change_12m(region_df)
    if selected_regions:
        last12m_region_df = last12m_region_df[last12m_region_df["region_name"].isin(selected_regions)].copy()
        share_change_df = share_change_df[share_change_df["region_name"].isin(selected_regions)].copy()

    st.subheader("📌 핵심 지표")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("전국 누적 등록대수", format_int(latest_total["cumulative_count"]))
    k2.metric("전월 대비 순증", format_int(latest_total["monthly_increase"]))
    k3.metric("전년 동월 대비 증가", format_int(latest_total["yoy_diff"]))
    total_last12 = get_last_12m_increase(total_df)
    total_last12 = total_last12[total_last12["region_name"] == "합계"]
    k4.metric("최근 12개월 순증", "-" if total_last12.empty else format_int(total_last12.iloc[0]["last_12m_increase"]))
    st.caption(f"최신 기준월: {latest_ym.strftime('%Y-%m')}")

    st.divider()
    st.subheader("🌐 전국 추세")
    c1, c2 = st.columns(2)
    c1.plotly_chart(bar_chart(filtered_total_df, x="base_ym", y="monthly_increase", title=f"전국 월별 순증 추이 ({period_label})", y_title="월별 순증"), use_container_width=True)
    c2.plotly_chart(line_chart(filtered_total_df, x="base_ym", y="yoy_diff", title=f"전국 전년 동월 대비 증가 ({period_label})", y_title="전년 동월 대비 증가"), use_container_width=True)
    heatmap_df = build_heatmap_source(total_df)
    if heatmap_df.empty or heatmap_df.notna().sum().sum() == 0:
        st.warning("전국 월별 순증 히트맵을 그릴 데이터가 없습니다.")
    else:
        st.plotly_chart(heatmap_chart(heatmap_df), use_container_width=True)

    st.divider()
    st.subheader("🗺️ 지역 비교")
    if filtered_region_df.empty:
        st.warning("선택한 지역 데이터가 없습니다.")
    else:
        c3, c4 = st.columns(2)
        c3.plotly_chart(line_chart(filtered_region_df, x="base_ym", y="monthly_increase", color="region_name", title=f"지역별 월별 순증 비교 ({period_label})", y_title="월별 순증"), use_container_width=True)
        c4.plotly_chart(line_chart(filtered_region_df, x="base_ym", y="yoy_diff", color="region_name", title=f"지역별 전년 동월 대비 증가 ({period_label})", y_title="전년 동월 대비 증가"), use_container_width=True)
        c5, c6 = st.columns(2)
        tmp_last12 = last12m_region_df.dropna(subset=["last_12m_increase"]).sort_values("last_12m_increase", ascending=True)
        if tmp_last12.empty:
            c5.warning("최근 12개월 순증 비교 데이터가 없습니다.")
        else:
            c5.plotly_chart(horizontal_bar(tmp_last12, x="last_12m_increase", y="region_name", title="최근 12개월 순증 비교", x_title="최근 12개월 순증"), use_container_width=True)
        tmp_share = share_change_df.dropna(subset=["share_change_12m"]).sort_values("share_change_12m", ascending=True)
        if tmp_share.empty:
            c6.warning("최근 12개월 점유율 변화 데이터가 없습니다.")
        else:
            c6.plotly_chart(horizontal_bar(tmp_share, x="share_change_12m", y="region_name", title="최근 12개월 점유율 변화", x_title="점유율 변화(%p)"), use_container_width=True)

    st.divider()
    st.subheader("📈 연도별 분석")
    c7, c8 = st.columns(2)
    if filtered_yearly_df.empty:
        c7.warning("연도별 순증 비교를 그릴 데이터가 없습니다.")
    else:
        c7.plotly_chart(bar_chart(filtered_yearly_df, x="year_num", y="yearly_increase", color="region_name", title="연도별 순증 비교", y_title="연도별 순증", barmode="group"), use_container_width=True)
    donut_base = latest_region_snapshot.dropna(subset=["cumulative_count"]).sort_values("cumulative_count", ascending=False).head(10)
    if donut_base.empty:
        c8.warning("최신월 기준 비중 차트를 그릴 데이터가 없습니다.")
    else:
        c8.plotly_chart(donut_chart(donut_base, names="region_name", values="cumulative_count", title="최신월 기준 누적 등록 비중 Top 10"), use_container_width=True)

    st.divider()
    st.subheader("📋 최신월 지역 현황")
    display_df = latest_region_snapshot[["region_name", "cumulative_count", "monthly_increase", "yoy_diff", "share_pct"]].copy()
    display_df = display_df.sort_values("cumulative_count", ascending=False)
    display_df.columns = ["지역", "누적 등록대수", "전월 대비 순증", "전년 동월 대비 증가", "점유율(%)"]
    st.dataframe(display_df, use_container_width=True, hide_index=True)
