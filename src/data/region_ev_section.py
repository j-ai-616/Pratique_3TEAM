from pathlib import Path
import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine
import plotly.express as px
import plotly.graph_objects as go


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)


# ---------------------------------------------------
# 1) DB 연결
# ---------------------------------------------------
@st.cache_resource
def get_db_engine():
    db_user = os.getenv("MYSQL_USER")
    db_password = os.getenv("MYSQL_PASSWORD")
    db_host = os.getenv("MYSQL_HOST", "127.0.0.1")
    db_port = os.getenv("MYSQL_PORT", "3306")
    db_name = os.getenv("MYSQL_DATABASE")

    if not all([db_user, db_password, db_name]):
        raise ValueError(".env 파일의 DB 환경변수를 확인하세요.")

    db_url = (
        f"mysql+pymysql://{db_user}:{db_password}"
        f"@{db_host}:{db_port}/{db_name}?charset=utf8mb4"
    )
    return create_engine(db_url)


@st.cache_data(ttl=300)
def read_sql_df(query: str) -> pd.DataFrame:
    engine = get_db_engine()
    return pd.read_sql(query, con=engine)


# ---------------------------------------------------
# 2) 데이터 로드
# ---------------------------------------------------
@st.cache_data(ttl=300)
def load_monthly_data() -> pd.DataFrame:
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
    df = read_sql_df(query)

    df["base_ym"] = pd.to_datetime(df["base_ym"], errors="coerce")

    numeric_cols = [
        "year_num",
        "month_num",
        "region_order",
        "cumulative_count",
        "monthly_increase",
        "yoy_diff",
        "share_pct",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["base_ym", "region_name"]).copy()
    return df


# ---------------------------------------------------
# 3) 유틸 함수
# ---------------------------------------------------
def format_int(x):
    if pd.isna(x):
        return "-"
    return f"{int(x):,}"


def recent_months_filter(df: pd.DataFrame, months: int):
    if months == 0:
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
    temp["monthly_increase"] = pd.to_numeric(temp["monthly_increase"], errors="coerce")

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
    merged["latest_share_pct"] = pd.to_numeric(merged["latest_share_pct"], errors="coerce")
    merged["prev_share_pct"] = pd.to_numeric(merged["prev_share_pct"], errors="coerce")
    merged["share_change_12m"] = merged["latest_share_pct"] - merged["prev_share_pct"]
    return merged


def make_yearly_from_monthly(monthly_df: pd.DataFrame) -> pd.DataFrame:
    temp = monthly_df.copy()

    temp["year_num"] = pd.to_numeric(temp["year_num"], errors="coerce")
    temp["monthly_increase"] = pd.to_numeric(temp["monthly_increase"], errors="coerce")
    temp["region_order"] = pd.to_numeric(temp["region_order"], errors="coerce")

    temp = temp.dropna(subset=["region_name", "year_num", "monthly_increase"]).copy()

    yearly = (
        temp.groupby(["region_name", "region_order", "year_num"], as_index=False)["monthly_increase"]
        .sum(min_count=1)
        .rename(columns={"monthly_increase": "yearly_increase"})
    )

    yearly["year_num"] = pd.to_numeric(yearly["year_num"], errors="coerce")
    yearly["yearly_increase"] = pd.to_numeric(yearly["yearly_increase"], errors="coerce")

    return yearly


def build_heatmap_source(total_df: pd.DataFrame) -> pd.DataFrame:
    temp = total_df.copy()

    temp["base_ym"] = pd.to_datetime(temp["base_ym"], errors="coerce")
    temp["monthly_increase"] = pd.to_numeric(temp["monthly_increase"], errors="coerce")

    temp = temp.dropna(subset=["base_ym", "monthly_increase"]).copy()

    temp["year"] = temp["base_ym"].dt.year
    temp["month"] = temp["base_ym"].dt.month

    pivot_df = temp.pivot_table(
        index="year",
        columns="month",
        values="monthly_increase",
        aggfunc="sum"
    )

    pivot_df = pivot_df.sort_index()
    pivot_df = pivot_df.reindex(columns=list(range(1, 13)))

    return pivot_df


# ---------------------------------------------------
# 4) 차트 함수
# ---------------------------------------------------
def line_chart(df, x, y, color=None, title="", y_title=""):
    fig = px.line(
        df,
        x=x,
        y=y,
        color=color,
        title=title,
        markers=True,
    )
    fig.update_layout(
        height=420,
        hovermode="x unified",
        xaxis_title="기준월" if x == "base_ym" else x,
        yaxis_title=y_title if y_title else y,
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return fig


def bar_chart(df, x, y, color=None, title="", y_title="", barmode="group"):
    fig = px.bar(
        df,
        x=x,
        y=y,
        color=color,
        title=title,
        barmode=barmode,
    )
    fig.update_layout(
        height=420,
        hovermode="x unified",
        xaxis_title="기준월" if x == "base_ym" else x,
        yaxis_title=y_title if y_title else y,
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return fig


def horizontal_bar(df, x, y, title="", x_title=""):
    fig = px.bar(
        df,
        x=x,
        y=y,
        orientation="h",
        title=title,
    )
    fig.update_layout(
        height=440,
        xaxis_title=x_title if x_title else x,
        yaxis_title="지역",
        margin=dict(l=20, r=20, t=60, b=20),
    )
    fig.update_yaxes(categoryorder="total ascending")
    return fig


def donut_chart(df, names, values, title=""):
    fig = px.pie(df, names=names, values=values, hole=0.45, title=title)
    fig.update_layout(
        height=440,
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return fig


def heatmap_chart(pivot_df, title="전국 월별 순증 히트맵"):
    fig = go.Figure(
        data=go.Heatmap(
            z=pivot_df.values,
            x=[f"{m}월" for m in pivot_df.columns],
            y=pivot_df.index.astype(str),
            hovertemplate="연도=%{y}<br>월=%{x}<br>순증=%{z:,}<extra></extra>",
        )
    )
    fig.update_layout(
        title=title,
        height=430,
        xaxis_title="월",
        yaxis_title="연도",
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return fig


# ---------------------------------------------------
# 5) 1번 탭 렌더링
# ---------------------------------------------------
def render_region_ev_page(ev_registration_data: pd.DataFrame) -> None:
    st.header("1. 지역 별 전기차 등록 현황")
    st.caption("DB 조회 기반으로 누적 등록보다 증가 속도와 지역별 차이를 중심으로 확인합니다.")

    st.info(
        "핵심 해석 포인트: 누적 그래프는 항상 우상향하기 쉬우므로, "
        "이 화면에서는 월별 순증, 최근 12개월, 전년 동월 대비, 연/월 히트맵을 함께 보여줍니다."
    )

    try:
        monthly_df = load_monthly_data()
        yearly_df = make_yearly_from_monthly(monthly_df)
    except Exception as e:
        st.error(f"데이터 로드 중 오류가 발생했습니다: {e}")
        return

    if monthly_df.empty:
        st.warning("데이터가 없습니다.")
        return

    all_regions = (
        monthly_df.loc[monthly_df["region_name"] != "합계", "region_name"]
        .drop_duplicates()
        .tolist()
    )

    total_df = monthly_df[monthly_df["region_name"] == "합계"].copy()
    region_df = monthly_df[monthly_df["region_name"] != "합계"].copy()

    latest_snapshot_all, latest_ym = get_latest_snapshot(monthly_df)

    latest_total_df = latest_snapshot_all[latest_snapshot_all["region_name"] == "합계"]
    if latest_total_df.empty:
        st.warning("합계 데이터가 없습니다.")
        return
    latest_total = latest_total_df.iloc[0]

    default_regions = [r for r in ["서울", "경기", "인천", "부산", "제주"] if r in all_regions]
    if not default_regions:
        default_regions = all_regions[:5]

    filter_column_1, filter_column_2 = st.columns([2, 1])

    selected_regions = filter_column_1.multiselect(
        "비교 지역 선택",
        options=all_regions,
        default=default_regions,
    )

    period_label = filter_column_2.selectbox(
        "차트 기간",
        options=["최근 12개월", "최근 24개월", "최근 36개월", "전체"],
        index=1,
    )

    period_map = {
        "최근 12개월": 12,
        "최근 24개월": 24,
        "최근 36개월": 36,
        "전체": 0,
    }
    selected_months = period_map[period_label]

    filtered_total_df = recent_months_filter(total_df, selected_months)
    filtered_region_df = recent_months_filter(region_df, selected_months)

    if selected_regions:
        filtered_region_df = filtered_region_df[
            filtered_region_df["region_name"].isin(selected_regions)
        ].copy()

    filtered_yearly_df = yearly_df.copy()
    if selected_regions:
        filtered_yearly_df = filtered_yearly_df[
            filtered_yearly_df["region_name"].isin(selected_regions + ["합계"])
        ].copy()

    filtered_yearly_df["year_num"] = pd.to_numeric(filtered_yearly_df["year_num"], errors="coerce")
    filtered_yearly_df["yearly_increase"] = pd.to_numeric(filtered_yearly_df["yearly_increase"], errors="coerce")
    filtered_yearly_df = filtered_yearly_df.dropna(subset=["year_num", "yearly_increase"]).copy()

    latest_region_snapshot = region_df[region_df["base_ym"] == latest_ym].copy()
    if selected_regions:
        latest_region_snapshot = latest_region_snapshot[
            latest_region_snapshot["region_name"].isin(selected_regions)
        ].copy()

    last12m_region_df = get_last_12m_increase(region_df)
    if selected_regions:
        last12m_region_df = last12m_region_df[
            last12m_region_df["region_name"].isin(selected_regions)
        ].copy()

    share_change_df = get_share_change_12m(region_df)
    if selected_regions:
        share_change_df = share_change_df[
            share_change_df["region_name"].isin(selected_regions)
        ].copy()

    st.subheader("📌 핵심 지표")

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        st.metric("전국 누적 등록대수", format_int(latest_total["cumulative_count"]))

    with k2:
        st.metric("전월 대비 순증", format_int(latest_total["monthly_increase"]))

    with k3:
        st.metric("전년 동월 대비 증가", format_int(latest_total["yoy_diff"]))

    with k4:
        total_last12 = get_last_12m_increase(total_df)
        total_last12 = total_last12[total_last12["region_name"] == "합계"]
        if total_last12.empty:
            st.metric("최근 12개월 순증", "-")
        else:
            st.metric("최근 12개월 순증", format_int(total_last12.iloc[0]["last_12m_increase"]))

    st.caption(f"최신 기준월: {latest_ym.strftime('%Y-%m')}")

    st.divider()
    st.subheader("🌐 전국 추세")

    c1, c2 = st.columns(2)

    with c1:
        fig_total_monthly = bar_chart(
            filtered_total_df,
            x="base_ym",
            y="monthly_increase",
            title=f"전국 월별 순증 추이 ({period_label})",
            y_title="월별 순증",
        )
        st.plotly_chart(fig_total_monthly, use_container_width=True)

    with c2:
        fig_total_yoy = line_chart(
            filtered_total_df,
            x="base_ym",
            y="yoy_diff",
            title=f"전국 전년 동월 대비 증가 ({period_label})",
            y_title="전년 동월 대비 증가",
        )
        st.plotly_chart(fig_total_yoy, use_container_width=True)

    heatmap_df = build_heatmap_source(total_df)

    if heatmap_df.empty or heatmap_df.notna().sum().sum() == 0:
        st.warning("전국 월별 순증 히트맵을 그릴 데이터가 없습니다.")
    else:
        st.plotly_chart(
            heatmap_chart(heatmap_df, "전국 월별 순증 히트맵"),
            use_container_width=True,
        )

    st.divider()
    st.subheader("🗺️ 지역 비교")

    if filtered_region_df.empty:
        st.warning("선택한 지역 데이터가 없습니다.")
    else:
        c3, c4 = st.columns(2)

        with c3:
            fig_region_monthly = line_chart(
                filtered_region_df,
                x="base_ym",
                y="monthly_increase",
                color="region_name",
                title=f"지역별 월별 순증 비교 ({period_label})",
                y_title="월별 순증",
            )
            st.plotly_chart(fig_region_monthly, use_container_width=True)

        with c4:
            fig_region_yoy = line_chart(
                filtered_region_df,
                x="base_ym",
                y="yoy_diff",
                color="region_name",
                title=f"지역별 전년 동월 대비 증가 ({period_label})",
                y_title="전년 동월 대비 증가",
            )
            st.plotly_chart(fig_region_yoy, use_container_width=True)

        c5, c6 = st.columns(2)

        with c5:
            tmp_last12 = last12m_region_df.dropna(subset=["last_12m_increase"]).sort_values(
                "last_12m_increase",
                ascending=True,
            )
            if tmp_last12.empty:
                st.warning("최근 12개월 순증 비교 데이터가 없습니다.")
            else:
                fig_last12_rank = horizontal_bar(
                    tmp_last12,
                    x="last_12m_increase",
                    y="region_name",
                    title="최근 12개월 순증 비교",
                    x_title="최근 12개월 순증",
                )
                st.plotly_chart(fig_last12_rank, use_container_width=True)

        with c6:
            tmp_share_change = share_change_df.dropna(subset=["share_change_12m"]).sort_values(
                "share_change_12m",
                ascending=True,
            )
            if tmp_share_change.empty:
                st.warning("최근 12개월 점유율 변화 데이터가 없습니다.")
            else:
                fig_share_change = horizontal_bar(
                    tmp_share_change,
                    x="share_change_12m",
                    y="region_name",
                    title="최근 12개월 점유율 변화",
                    x_title="점유율 변화(%p)",
                )
                st.plotly_chart(fig_share_change, use_container_width=True)

    st.divider()
    st.subheader("📈 연도별 분석")

    c7, c8 = st.columns(2)

    with c7:
        if filtered_yearly_df.empty:
            st.warning("연도별 순증 비교를 그릴 데이터가 없습니다.")
        else:
            fig_yearly = bar_chart(
                filtered_yearly_df,
                x="year_num",
                y="yearly_increase",
                color="region_name",
                title="연도별 순증 비교",
                y_title="연도별 순증",
                barmode="group",
            )
            st.plotly_chart(fig_yearly, use_container_width=True)

    with c8:
        donut_base = latest_region_snapshot.dropna(subset=["cumulative_count"]).sort_values(
            "cumulative_count",
            ascending=False,
        ).head(10)
        if donut_base.empty:
            st.warning("최신월 기준 비중 차트를 그릴 데이터가 없습니다.")
        else:
            fig_donut = donut_chart(
                donut_base,
                names="region_name",
                values="cumulative_count",
                title="최신월 기준 누적 등록 비중 Top 10",
            )
            st.plotly_chart(fig_donut, use_container_width=True)

    st.info("마지막 연도는 12월까지 모두 채워지지 않았을 수 있으므로 YTD 성격으로 해석해야 합니다.")

    st.divider()
    st.subheader("🏆 최신월 랭킹")

    if latest_region_snapshot.empty:
        st.warning("최신월 지역 데이터가 없습니다.")
    else:
        c9, c10 = st.columns(2)

        with c9:
            rank_cum = latest_region_snapshot.dropna(subset=["cumulative_count"]).sort_values(
                "cumulative_count",
                ascending=False,
            ).head(10)
            if rank_cum.empty:
                st.warning("누적 등록대수 랭킹 데이터가 없습니다.")
            else:
                fig_rank_cum = horizontal_bar(
                    rank_cum.sort_values("cumulative_count"),
                    x="cumulative_count",
                    y="region_name",
                    title="최신월 누적 등록대수 Top 10",
                    x_title="누적 등록대수",
                )
                st.plotly_chart(fig_rank_cum, use_container_width=True)

        with c10:
            rank_mom = latest_region_snapshot.dropna(subset=["monthly_increase"]).sort_values(
                "monthly_increase",
                ascending=False,
            ).head(10)
            if rank_mom.empty:
                st.warning("월별 순증 랭킹 데이터가 없습니다.")
            else:
                fig_rank_mom = horizontal_bar(
                    rank_mom.sort_values("monthly_increase"),
                    x="monthly_increase",
                    y="region_name",
                    title="최신월 월별 순증 Top 10",
                    x_title="월별 순증",
                )
                st.plotly_chart(fig_rank_mom, use_container_width=True)

    st.divider()
    st.subheader("📋 최신월 지역 현황")

    latest_table = latest_region_snapshot[[
        "region_name",
        "cumulative_count",
        "monthly_increase",
        "yoy_diff",
        "share_pct"
    ]].copy()

    latest_table.columns = ["지역", "누적 등록대수", "월별 순증", "전년 동월 대비 증가", "점유율(%)"]

    st.dataframe(
        latest_table.sort_values("누적 등록대수", ascending=False),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("🔎 상세 데이터 조회")

    detail_df = filtered_region_df[[
        "base_ym",
        "year_num",
        "month_num",
        "region_name",
        "cumulative_count",
        "monthly_increase",
        "yoy_diff",
        "share_pct"
    ]].copy()

    detail_df = detail_df.sort_values(["base_ym", "region_name"], ascending=[False, True])
    detail_df.columns = ["기준월", "연도", "월", "지역", "누적 등록대수", "월별 순증", "전년 동월 대비 증가", "점유율(%)"]

    st.dataframe(detail_df, use_container_width=True, hide_index=True)

    csv_data = detail_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="CSV 다운로드",
        data=csv_data,
        file_name="ev_registration_dashboard_filtered.csv",
        mime="text/csv",
    )

    st.divider()
    st.markdown(
        """
        ### 해석 팁
        - **누적 등록대수**: 해당 월 말 기준 누적 보유량
        - **월별 순증**: 당월 누적 - 전월 누적
        - **전년 동월 대비 증가**: 같은 달 기준으로 1년 전보다 얼마나 늘었는지
        - **최근 12개월 순증**: 최근 1년 동안 실제로 얼마나 늘었는지
        - **점유율 변화**: 전국 대비 해당 지역 비중이 커졌는지/줄었는지
        """
    )
