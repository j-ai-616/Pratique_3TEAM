# 이 스크립트는 Streamlit 기반 전기차 정보 포털에서
# "1. 지역 별 전기차 등록 현황" 화면을 구성하는 역할을 합니다.
#
# 이 스크립트의 핵심 역할은 다음과 같습니다.
#
# 1) MySQL DB 연결 및 조회
#    - .env 파일에 저장된 MySQL 접속 정보를 읽어 DB 엔진을 생성합니다.
#    - 뷰(View) 테이블인 vw_ev_registration_monthly에서 월별 전기차 등록 현황 데이터를 조회합니다.
#
# 2) 조회 데이터 정리 및 분석용 가공
#    - 날짜형(base_ym), 숫자형 컬럼들을 정리합니다.
#    - 최근 N개월 필터, 최신월 스냅샷, 최근 12개월 순증, 점유율 변화,
#      연도별 순증, 히트맵용 피벗 데이터 등을 계산합니다.
#
# 3) 차트 생성
#    - Plotly를 이용해 선그래프, 막대그래프, 가로 막대그래프,
#      도넛 차트, 히트맵을 생성합니다.
#
# 4) 지역별 전기차 등록 현황 화면 렌더링
#    - 전국 추세
#    - 지역 비교
#    - 연도별 분석
#    - 최신월 랭킹
#    - 최신월 지역 현황
#    - 상세 데이터 조회 및 CSV 다운로드
#    를 하나의 Streamlit 페이지에서 제공합니다.
#
# 이 스크립트는 프로젝트 구조상 "1번 탭 전용 화면 렌더링 + 데이터 조회/분석"을 한 파일 안에서 담당합니다.
# 다른 탭들과 달리, query_data.py를 거치지 않고 직접 DB View를 조회하는 구조라는 점이 특징입니다.
#
# 이 스크립트와 상호작용하는 주요 스크립트는 다음과 같습니다.
#
# 1) src/app/main_app.py
#    - 전체 Streamlit 앱의 진입점이며 메뉴 라우팅을 담당합니다.
#    - 사용자가 "지역 별 전기차 등록 현황" 메뉴를 선택하면
#      render_region_ev_page()를 호출합니다.
#    - 즉, 현재 스크립트는 main_app.py와 직접 연결됩니다.
#
# 2) .env 파일
#    - MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE
#      환경변수를 제공하여 DB 연결 정보를 이 스크립트에 전달합니다.
#
# 3) MySQL DB의 vw_ev_registration_monthly View
#    - 이 스크립트가 실제 데이터를 읽어오는 데이터 소스입니다.
#    - 월별 지역별 누적 등록 대수, 월별 순증, 전년 동월 대비 증가, 점유율 등을 제공합니다.
#
# 정리하면,
# 이 스크립트는 "DB에서 지역별 전기차 등록 현황을 직접 조회해,
# 다양한 분석 지표와 시각화 차트를 한 화면에 렌더링하는 1번 탭 전용 스크립트"입니다.

from __future__ import annotations

# 파일 및 디렉터리 경로를 객체 형태로 다루기 위한 표준 라이브러리입니다.
# .env 파일 경로를 안전하게 계산할 때 사용합니다.
from pathlib import Path

# 운영체제 환경변수에 접근하기 위한 표준 라이브러리입니다.
# MySQL 접속 정보(MYSQL_USER 등)를 읽을 때 사용합니다.
import os

# 표 형태 데이터(DataFrame)를 다루기 위한 pandas 라이브러리입니다.
# DB 조회 결과를 DataFrame으로 받고, 전처리, 집계, 피벗, 날짜/숫자 변환 등에 사용합니다.
import pandas as pd

# Streamlit 화면 구성을 위한 라이브러리입니다.
# 제목, 캡션, 알림, 필터 UI, 차트 표시, 표 표시, 다운로드 버튼 등에 사용합니다.
import streamlit as st

# .env 파일을 읽어 환경변수로 로드하는 라이브러리입니다.
# DB 접속 정보가 코드에 직접 노출되지 않도록 하기 위해 사용합니다.
from dotenv import load_dotenv

# SQLAlchemy의 create_engine 함수입니다.
# MySQL DB에 연결할 엔진 객체를 만들 때 사용합니다.
from sqlalchemy import create_engine

# Plotly Express는 간단하게 선그래프, 막대그래프, 원형 차트 등을 만들기 위한 라이브러리입니다.
import plotly.express as px

# Plotly Graph Objects는 히트맵처럼 좀 더 세밀한 차트를 구성할 때 사용합니다.
import plotly.graph_objects as go


# 현재 파일이 위치한 경로를 기준으로 프로젝트 루트(BASE_DIR)를 계산합니다.
# 예: src/data/이파일.py -> 두 단계 위 폴더를 프로젝트 루트로 간주합니다.
BASE_DIR = Path(__file__).resolve().parents[2]

# 프로젝트 루트 바로 아래의 .env 파일 경로를 계산합니다.
ENV_PATH = BASE_DIR / ".env"

# .env 파일을 읽어 환경변수로 로드합니다.
load_dotenv(ENV_PATH)


# ---------------------------------------------------
# 1) DB 연결
# ---------------------------------------------------
@st.cache_resource
def get_db_engine():
    # 환경변수에서 MySQL 사용자명을 읽습니다.
    db_user = os.getenv("MYSQL_USER")

    # 환경변수에서 MySQL 비밀번호를 읽습니다.
    db_password = os.getenv("MYSQL_PASSWORD")

    # 환경변수에서 MySQL 호스트를 읽습니다.
    # 값이 없으면 기본값으로 127.0.0.1(localhost)을 사용합니다.
    db_host = os.getenv("MYSQL_HOST", "127.0.0.1")

    # 환경변수에서 MySQL 포트를 읽습니다.
    # 값이 없으면 기본값 3306을 사용합니다.
    db_port = os.getenv("MYSQL_PORT", "3306")

    # 환경변수에서 사용할 데이터베이스 이름을 읽습니다.
    db_name = os.getenv("MYSQL_DATABASE")

    # 필수 접속 정보(user, password, db_name)가 하나라도 없으면 예외를 발생시킵니다.
    if not all([db_user, db_password, db_name]):
        raise ValueError(".env 파일의 DB 환경변수를 확인하세요.")

    # SQLAlchemy용 MySQL 접속 URL 문자열을 생성합니다.
    # 문자셋은 utf8mb4로 설정해 한글 등 멀티바이트 문자를 안전하게 처리합니다.
    db_url = (
        f"mysql+pymysql://{db_user}:{db_password}"
        f"@{db_host}:{db_port}/{db_name}?charset=utf8mb4"
    )

    # create_engine()으로 DB 엔진 객체를 생성해 반환합니다.
    return create_engine(db_url)


@st.cache_data(ttl=300)
def read_sql_df(query: str) -> pd.DataFrame:
    # DB 엔진을 가져옵니다.
    engine = get_db_engine()

    # 주어진 SQL 쿼리를 실행하여 결과를 pandas DataFrame으로 읽어옵니다.
    return pd.read_sql(query, con=engine)


# ---------------------------------------------------
# 2) 데이터 로드
# ---------------------------------------------------
@st.cache_data(ttl=300)
def load_monthly_data() -> pd.DataFrame:
    # 월별 전기차 등록 현황 View에서 필요한 컬럼만 조회하는 SQL 쿼리입니다.
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

    # SQL 결과를 DataFrame으로 읽어옵니다.
    df = read_sql_df(query)

    # base_ym 컬럼을 날짜형(datetime)으로 변환합니다.
    # 변환 실패 시 NaT로 처리합니다.
    df["base_ym"] = pd.to_datetime(df["base_ym"], errors="coerce")

    # 숫자형으로 다뤄야 하는 컬럼 목록입니다.
    numeric_cols = [
        "year_num",
        "month_num",
        "region_order",
        "cumulative_count",
        "monthly_increase",
        "yoy_diff",
        "share_pct",
    ]

    # 각 숫자형 컬럼을 숫자 타입으로 변환합니다.
    # 변환 실패 값은 NaN으로 처리합니다.
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # base_ym 또는 region_name이 없는 행은 분석에 부적합하므로 제거합니다.
    df = df.dropna(subset=["base_ym", "region_name"]).copy()

    # 정리된 월별 데이터를 반환합니다.
    return df


# ---------------------------------------------------
# 3) 유틸 함수
# ---------------------------------------------------
def format_int(x):
    # 값이 결측치이면 "-"를 반환합니다.
    if pd.isna(x):
        return "-"

    # 정수형으로 변환한 뒤 천 단위 콤마 형식 문자열로 반환합니다.
    return f"{int(x):,}"


def recent_months_filter(df: pd.DataFrame, months: int):
    # months가 0이면 전체 기간을 의미하므로 원본 복사본을 그대로 반환합니다.
    if months == 0:
        return df.copy()

    # 데이터에서 가장 최신 날짜를 구합니다.
    max_date = df["base_ym"].max()

    # 최신 날짜 기준으로 months 개월 전의 시작 날짜를 계산합니다.
    # 예: 최근 12개월이면 max_date 포함 12개월치가 남도록 min_date를 계산합니다.
    min_date = max_date - pd.DateOffset(months=months - 1)

    # 시작 날짜 이상인 데이터만 남겨 반환합니다.
    return df[df["base_ym"] >= min_date].copy()


def get_latest_snapshot(monthly_df: pd.DataFrame):
    # 전체 월별 데이터에서 가장 최신 기준월을 구합니다.
    latest_ym = monthly_df["base_ym"].max()

    # 최신 기준월에 해당하는 데이터만 추출하여 반환합니다.
    return monthly_df[monthly_df["base_ym"] == latest_ym].copy(), latest_ym


def get_last_12m_increase(df: pd.DataFrame):
    # 데이터에서 가장 최신 날짜를 구합니다.
    max_date = df["base_ym"].max()

    # 최신 날짜를 포함하여 최근 12개월 범위의 시작 날짜를 계산합니다.
    min_date = max_date - pd.DateOffset(months=11)

    # 최근 12개월 데이터만 추출합니다.
    temp = df[df["base_ym"] >= min_date].copy()

    # monthly_increase 컬럼을 숫자형으로 변환합니다.
    temp["monthly_increase"] = pd.to_numeric(temp["monthly_increase"], errors="coerce")

    # 지역별로 최근 12개월 monthly_increase를 합산합니다.
    # min_count=1 설정으로 전부 NaN인 경우도 올바르게 처리합니다.
    result = (
        temp.groupby("region_name", as_index=False)["monthly_increase"]
        .sum(min_count=1)
        .rename(columns={"monthly_increase": "last_12m_increase"})
    )

    # 최근 12개월 순증 집계 결과를 반환합니다.
    return result


def get_share_change_12m(df_non_total: pd.DataFrame):
    # 입력 데이터(합계 제외 지역 데이터)에서 최신 날짜를 구합니다.
    latest_date = df_non_total["base_ym"].max()

    # 최신 날짜 기준 12개월 전 날짜를 계산합니다.
    prev_12m_date = latest_date - pd.DateOffset(months=12)

    # 최신 시점의 지역별 점유율 데이터를 추출합니다.
    latest_df = df_non_total[df_non_total["base_ym"] == latest_date][["region_name", "share_pct"]].copy()
    latest_df = latest_df.rename(columns={"share_pct": "latest_share_pct"})

    # 12개월 전 시점의 지역별 점유율 데이터를 추출합니다.
    prev_df = df_non_total[df_non_total["base_ym"] == prev_12m_date][["region_name", "share_pct"]].copy()
    prev_df = prev_df.rename(columns={"share_pct": "prev_share_pct"})

    # 최신 점유율과 12개월 전 점유율을 지역명 기준으로 병합합니다.
    merged = latest_df.merge(prev_df, on="region_name", how="left")

    # 두 점유율 컬럼을 숫자형으로 변환합니다.
    merged["latest_share_pct"] = pd.to_numeric(merged["latest_share_pct"], errors="coerce")
    merged["prev_share_pct"] = pd.to_numeric(merged["prev_share_pct"], errors="coerce")

    # 최근 12개월 점유율 변화를 계산합니다.
    merged["share_change_12m"] = merged["latest_share_pct"] - merged["prev_share_pct"]

    # 계산 결과를 반환합니다.
    return merged


def make_yearly_from_monthly(monthly_df: pd.DataFrame) -> pd.DataFrame:
    # 원본 DataFrame 훼손 방지를 위해 복사본을 생성합니다.
    temp = monthly_df.copy()

    # 연도, 월별 순증, 지역 정렬 순서를 숫자형으로 변환합니다.
    temp["year_num"] = pd.to_numeric(temp["year_num"], errors="coerce")
    temp["monthly_increase"] = pd.to_numeric(temp["monthly_increase"], errors="coerce")
    temp["region_order"] = pd.to_numeric(temp["region_order"], errors="coerce")

    # 연도, 지역명, 월별 순증이 없는 행은 제거합니다.
    temp = temp.dropna(subset=["region_name", "year_num", "monthly_increase"]).copy()

    # 지역별, 연도별로 월별 순증을 합산하여 연도별 순증을 계산합니다.
    yearly = (
        temp.groupby(["region_name", "region_order", "year_num"], as_index=False)["monthly_increase"]
        .sum(min_count=1)
        .rename(columns={"monthly_increase": "yearly_increase"})
    )

    # 생성된 연도 컬럼과 연도별 순증 컬럼을 숫자형으로 다시 명시적으로 변환합니다.
    yearly["year_num"] = pd.to_numeric(yearly["year_num"], errors="coerce")
    yearly["yearly_increase"] = pd.to_numeric(yearly["yearly_increase"], errors="coerce")

    # 연도별 집계 결과를 반환합니다.
    return yearly


def build_heatmap_source(total_df: pd.DataFrame) -> pd.DataFrame:
    # 원본 DataFrame 훼손 방지를 위해 복사본을 생성합니다.
    temp = total_df.copy()

    # 날짜형, 숫자형으로 변환합니다.
    temp["base_ym"] = pd.to_datetime(temp["base_ym"], errors="coerce")
    temp["monthly_increase"] = pd.to_numeric(temp["monthly_increase"], errors="coerce")

    # 날짜나 월별 순증이 없는 행은 제거합니다.
    temp = temp.dropna(subset=["base_ym", "monthly_increase"]).copy()

    # 히트맵의 행/열을 만들기 위해 연도와 월 컬럼을 분리합니다.
    temp["year"] = temp["base_ym"].dt.year
    temp["month"] = temp["base_ym"].dt.month

    # 연도를 행(index), 월을 열(columns), monthly_increase를 값으로 하는 피벗 테이블을 생성합니다.
    pivot_df = temp.pivot_table(
        index="year",
        columns="month",
        values="monthly_increase",
        aggfunc="sum"
    )

    # 연도 순으로 정렬합니다.
    pivot_df = pivot_df.sort_index()

    # 월 컬럼을 1월~12월 순서로 강제 맞춥니다.
    # 일부 월이 비어 있어도 1~12월 형태가 유지되도록 합니다.
    pivot_df = pivot_df.reindex(columns=list(range(1, 13)))

    # 히트맵용 피벗 데이터를 반환합니다.
    return pivot_df


# ---------------------------------------------------
# 4) 차트 함수
# ---------------------------------------------------
def line_chart(df, x, y, color=None, title="", y_title=""):
    # Plotly Express로 선그래프를 생성합니다.
    fig = px.line(
        df,
        x=x,
        y=y,
        color=color,
        title=title,
        markers=True,
    )

    # 차트 레이아웃을 조정합니다.
    fig.update_layout(
        height=420,
        hovermode="x unified",
        xaxis_title="기준월" if x == "base_ym" else x,
        yaxis_title=y_title if y_title else y,
        margin=dict(l=20, r=20, t=60, b=20),
    )

    # 생성된 그래프 객체를 반환합니다.
    return fig


def bar_chart(df, x, y, color=None, title="", y_title="", barmode="group"):
    # Plotly Express로 막대그래프를 생성합니다.
    fig = px.bar(
        df,
        x=x,
        y=y,
        color=color,
        title=title,
        barmode=barmode,
    )

    # 차트 레이아웃을 조정합니다.
    fig.update_layout(
        height=420,
        hovermode="x unified",
        xaxis_title="기준월" if x == "base_ym" else x,
        yaxis_title=y_title if y_title else y,
        margin=dict(l=20, r=20, t=60, b=20),
    )

    # 생성된 그래프 객체를 반환합니다.
    return fig


def horizontal_bar(df, x, y, title="", x_title=""):
    # Plotly Express로 가로 막대그래프를 생성합니다.
    fig = px.bar(
        df,
        x=x,
        y=y,
        orientation="h",
        title=title,
    )

    # 차트 레이아웃을 조정합니다.
    fig.update_layout(
        height=440,
        xaxis_title=x_title if x_title else x,
        yaxis_title="지역",
        margin=dict(l=20, r=20, t=60, b=20),
    )

    # 막대가 작은 값 -> 큰 값 순으로 자연스럽게 보이도록 정렬 기준을 설정합니다.
    fig.update_yaxes(categoryorder="total ascending")

    # 생성된 그래프 객체를 반환합니다.
    return fig


def donut_chart(df, names, values, title=""):
    # Plotly Express로 도넛 차트를 생성합니다.
    fig = px.pie(df, names=names, values=values, hole=0.45, title=title)

    # 차트 레이아웃을 조정합니다.
    fig.update_layout(
        height=440,
        margin=dict(l=20, r=20, t=60, b=20),
    )

    # 생성된 그래프 객체를 반환합니다.
    return fig


def heatmap_chart(pivot_df, title="전국 월별 순증 히트맵"):
    # Plotly Graph Objects로 히트맵을 생성합니다.
    fig = go.Figure(
        data=go.Heatmap(
            z=pivot_df.values,
            x=[f"{m}월" for m in pivot_df.columns],
            y=pivot_df.index.astype(str),
            hovertemplate="연도=%{y}<br>월=%{x}<br>순증=%{z:,}<extra></extra>",
        )
    )

    # 차트 레이아웃을 조정합니다.
    fig.update_layout(
        title=title,
        height=430,
        xaxis_title="월",
        yaxis_title="연도",
        margin=dict(l=20, r=20, t=60, b=20),
    )

    # 생성된 그래프 객체를 반환합니다.
    return fig


# ---------------------------------------------------
# 5) 1번 탭 렌더링
# ---------------------------------------------------
def render_region_ev_page(ev_registration_data: pd.DataFrame) -> None:
    # 페이지 상단 제목을 출력합니다.
    st.header("지역별 전기차 등록 현황")

    # 페이지 설명 문구를 출력합니다.
    st.caption("DB 조회 기반으로 누적 등록보다 증가 속도와 지역별 차이를 중심으로 확인합니다.")

    # 이 화면의 해석 포인트를 안내하는 정보 박스를 출력합니다.
    st.info(
        "핵심 해석 포인트: 누적 그래프는 항상 우상향하기 쉬우므로, "
        "이 화면에서는 월별 순증, 최근 12개월, 전년 동월 대비, 연/월 히트맵을 함께 보여줍니다."
    )

    # 데이터 로드 및 연도별 집계 과정에서 예외가 발생하면 화면에 에러를 출력하고 종료합니다.
    try:
        # DB에서 월별 등록 현황 데이터를 로드합니다.
        monthly_df = load_monthly_data()

        # 월별 데이터를 바탕으로 연도별 순증 데이터를 생성합니다.
        yearly_df = make_yearly_from_monthly(monthly_df)
    except Exception as e:
        st.error(f"데이터 로드 중 오류가 발생했습니다: {e}")
        return

    # 월별 데이터가 비어 있으면 경고 문구를 출력하고 종료합니다.
    if monthly_df.empty:
        st.warning("데이터가 없습니다.")
        return

    # "합계"를 제외한 모든 지역 목록을 추출합니다.
    all_regions = (
        monthly_df.loc[monthly_df["region_name"] != "합계", "region_name"]
        .drop_duplicates()
        .tolist()
    )

    # 전국 합계 데이터만 따로 분리합니다.
    total_df = monthly_df[monthly_df["region_name"] == "합계"].copy()

    # 지역별 데이터(합계 제외)만 따로 분리합니다.
    region_df = monthly_df[monthly_df["region_name"] != "합계"].copy()

    # 최신 기준월의 전체 스냅샷과 그 최신 기준월 값을 구합니다.
    latest_snapshot_all, latest_ym = get_latest_snapshot(monthly_df)

    # 최신 기준월 데이터 중 "합계" 행만 추출합니다.
    latest_total_df = latest_snapshot_all[latest_snapshot_all["region_name"] == "합계"]

    # 최신 합계 데이터가 없으면 경고 문구를 출력하고 종료합니다.
    if latest_total_df.empty:
        st.warning("합계 데이터가 없습니다.")
        return

    # 최신 합계 데이터의 첫 번째 행을 대표값으로 사용합니다.
    latest_total = latest_total_df.iloc[0]

    # 기본 비교 지역 목록을 설정합니다.
    # 서울, 경기, 인천, 부산, 제주가 존재하면 우선 선택합니다.
    default_regions = [r for r in ["서울", "경기", "인천", "부산", "제주"] if r in all_regions]

    # 위 기본 지역이 하나도 없으면, 전체 지역 중 앞 5개를 기본값으로 사용합니다.
    if not default_regions:
        default_regions = all_regions[:5]

    # 지역 선택과 기간 선택 UI를 2개 컬럼으로 나누어 배치합니다.
    filter_column_1, filter_column_2 = st.columns([2, 1])

    # 사용자가 비교할 지역을 선택할 수 있는 멀티셀렉트를 출력합니다.
    selected_regions = filter_column_1.multiselect(
        "비교 지역 선택",
        options=all_regions,
        default=default_regions,
    )

    # 사용자가 차트 기간을 선택할 수 있는 셀렉트박스를 출력합니다.
    period_label = filter_column_2.selectbox(
        "차트 기간",
        options=["최근 12개월", "최근 24개월", "최근 36개월", "전체"],
        index=1,
    )

    # 선택된 기간 라벨을 실제 개월 수로 변환하기 위한 매핑 딕셔너리입니다.
    period_map = {
        "최근 12개월": 12,
        "최근 24개월": 24,
        "최근 36개월": 36,
        "전체": 0,
    }

    # 사용자가 선택한 기간에 해당하는 개월 수를 가져옵니다.
    selected_months = period_map[period_label]

    # 전국 합계 데이터에 최근 N개월 필터를 적용합니다.
    filtered_total_df = recent_months_filter(total_df, selected_months)

    # 지역별 데이터에 최근 N개월 필터를 적용합니다.
    filtered_region_df = recent_months_filter(region_df, selected_months)

    # 비교 지역이 선택되어 있으면 해당 지역 데이터만 남깁니다.
    if selected_regions:
        filtered_region_df = filtered_region_df[
            filtered_region_df["region_name"].isin(selected_regions)
        ].copy()

    # 연도별 데이터는 전체 복사본에서 시작합니다.
    filtered_yearly_df = yearly_df.copy()

    # 비교 지역이 선택되어 있으면 선택 지역 + "합계" 데이터만 남깁니다.
    if selected_regions:
        filtered_yearly_df = filtered_yearly_df[
            filtered_yearly_df["region_name"].isin(selected_regions + ["합계"])
        ].copy()

    # 연도별 데이터의 숫자 컬럼을 숫자형으로 변환합니다.
    filtered_yearly_df["year_num"] = pd.to_numeric(filtered_yearly_df["year_num"], errors="coerce")
    filtered_yearly_df["yearly_increase"] = pd.to_numeric(filtered_yearly_df["yearly_increase"], errors="coerce")

    # 연도와 연도별 순증이 없는 행은 제거합니다.
    filtered_yearly_df = filtered_yearly_df.dropna(subset=["year_num", "yearly_increase"]).copy()

    # 최신 기준월의 지역별 스냅샷 데이터를 추출합니다.
    latest_region_snapshot = region_df[region_df["base_ym"] == latest_ym].copy()

    # 비교 지역이 선택되어 있으면 해당 지역만 남깁니다.
    if selected_regions:
        latest_region_snapshot = latest_region_snapshot[
            latest_region_snapshot["region_name"].isin(selected_regions)
        ].copy()

    # 최근 12개월 지역별 순증 데이터를 계산합니다.
    last12m_region_df = get_last_12m_increase(region_df)

    # 비교 지역이 선택되어 있으면 해당 지역만 남깁니다.
    if selected_regions:
        last12m_region_df = last12m_region_df[
            last12m_region_df["region_name"].isin(selected_regions)
        ].copy()

    # 최근 12개월 점유율 변화 데이터를 계산합니다.
    share_change_df = get_share_change_12m(region_df)

    # 비교 지역이 선택되어 있으면 해당 지역만 남깁니다.
    if selected_regions:
        share_change_df = share_change_df[
            share_change_df["region_name"].isin(selected_regions)
        ].copy()

    # 핵심 지표 영역 제목을 출력합니다.
    st.subheader("📌 핵심 지표")

    # 핵심 지표를 4개 metric 컬럼으로 나누어 배치합니다.
    k1, k2, k3, k4 = st.columns(4)

    with k1:
        # 전국 최신월 누적 등록 대수를 표시합니다.
        st.metric("전국 누적 등록대수", format_int(latest_total["cumulative_count"]))

    with k2:
        # 전국 최신월 전월 대비 순증을 표시합니다.
        st.metric("전월 대비 순증", format_int(latest_total["monthly_increase"]))

    with k3:
        # 전국 최신월 전년 동월 대비 증가를 표시합니다.
        st.metric("전년 동월 대비 증가", format_int(latest_total["yoy_diff"]))

    with k4:
        # 전국 합계의 최근 12개월 순증을 계산해 표시합니다.
        total_last12 = get_last_12m_increase(total_df)
        total_last12 = total_last12[total_last12["region_name"] == "합계"]

        if total_last12.empty:
            st.metric("최근 12개월 순증", "-")
        else:
            st.metric("최근 12개월 순증", format_int(total_last12.iloc[0]["last_12m_increase"]))

    # 최신 기준월을 캡션 형태로 표시합니다.
    st.caption(f"최신 기준월: {latest_ym.strftime('%Y-%m')}")

    # 구분선을 출력합니다.
    st.divider()

    # 전국 추세 영역 제목을 출력합니다.
    st.subheader("🌐 전국 추세")

    # 전국 추세 차트를 2개 컬럼으로 배치합니다.
    c1, c2 = st.columns(2)

    with c1:
        # 전국 월별 순증 막대그래프를 생성합니다.
        fig_total_monthly = bar_chart(
            filtered_total_df,
            x="base_ym",
            y="monthly_increase",
            title=f"전국 월별 순증 추이 ({period_label})",
            y_title="월별 순증",
        )

        # 그래프를 화면에 출력합니다.
        st.plotly_chart(fig_total_monthly, use_container_width=True)

    with c2:
        # 전국 전년 동월 대비 증가 선그래프를 생성합니다.
        fig_total_yoy = line_chart(
            filtered_total_df,
            x="base_ym",
            y="yoy_diff",
            title=f"전국 전년 동월 대비 증가 ({period_label})",
            y_title="전년 동월 대비 증가",
        )

        # 그래프를 화면에 출력합니다.
        st.plotly_chart(fig_total_yoy, use_container_width=True)

    # 전국 합계 데이터로 히트맵용 피벗 데이터를 생성합니다.
    heatmap_df = build_heatmap_source(total_df)

    # 히트맵 데이터가 비어 있거나 전부 결측치면 경고 문구를 출력합니다.
    if heatmap_df.empty or heatmap_df.notna().sum().sum() == 0:
        st.warning("전국 월별 순증 히트맵을 그릴 데이터가 없습니다.")
    else:
        # 히트맵 차트를 생성해 화면에 출력합니다.
        st.plotly_chart(
            heatmap_chart(heatmap_df, "전국 월별 순증 히트맵"),
            use_container_width=True,
        )

    # 구분선을 출력합니다.
    st.divider()

    # 지역 비교 영역 제목을 출력합니다.
    st.subheader("🗺️ 지역 비교")

    # 필터된 지역 데이터가 비어 있으면 경고 문구를 출력합니다.
    if filtered_region_df.empty:
        st.warning("선택한 지역 데이터가 없습니다.")
    else:
        # 지역 비교 차트를 2열씩 두 줄로 배치합니다.
        c3, c4 = st.columns(2)

        with c3:
            # 지역별 월별 순증 비교 선그래프를 생성합니다.
            fig_region_monthly = line_chart(
                filtered_region_df,
                x="base_ym",
                y="monthly_increase",
                color="region_name",
                title=f"지역별 월별 순증 비교 ({period_label})",
                y_title="월별 순증",
            )

            # 그래프를 화면에 출력합니다.
            st.plotly_chart(fig_region_monthly, use_container_width=True)

        with c4:
            # 지역별 전년 동월 대비 증가 비교 선그래프를 생성합니다.
            fig_region_yoy = line_chart(
                filtered_region_df,
                x="base_ym",
                y="yoy_diff",
                color="region_name",
                title=f"지역별 전년 동월 대비 증가 ({period_label})",
                y_title="전년 동월 대비 증가",
            )

            # 그래프를 화면에 출력합니다.
            st.plotly_chart(fig_region_yoy, use_container_width=True)

        c5, c6 = st.columns(2)

        with c5:
            # 최근 12개월 순증 데이터를 결측치 제거 후 오름차순 정렬합니다.
            tmp_last12 = last12m_region_df.dropna(subset=["last_12m_increase"]).sort_values(
                "last_12m_increase",
                ascending=True,
            )

            # 데이터가 없으면 경고 문구를 출력합니다.
            if tmp_last12.empty:
                st.warning("최근 12개월 순증 비교 데이터가 없습니다.")
            else:
                # 최근 12개월 순증 비교 가로 막대그래프를 생성합니다.
                fig_last12_rank = horizontal_bar(
                    tmp_last12,
                    x="last_12m_increase",
                    y="region_name",
                    title="최근 12개월 순증 비교",
                    x_title="최근 12개월 순증",
                )

                # 그래프를 화면에 출력합니다.
                st.plotly_chart(fig_last12_rank, use_container_width=True)

        with c6:
            # 최근 12개월 점유율 변화 데이터를 결측치 제거 후 오름차순 정렬합니다.
            tmp_share_change = share_change_df.dropna(subset=["share_change_12m"]).sort_values(
                "share_change_12m",
                ascending=True,
            )

            # 데이터가 없으면 경고 문구를 출력합니다.
            if tmp_share_change.empty:
                st.warning("최근 12개월 점유율 변화 데이터가 없습니다.")
            else:
                # 최근 12개월 점유율 변화 가로 막대그래프를 생성합니다.
                fig_share_change = horizontal_bar(
                    tmp_share_change,
                    x="share_change_12m",
                    y="region_name",
                    title="최근 12개월 점유율 변화",
                    x_title="점유율 변화(%p)",
                )

                # 그래프를 화면에 출력합니다.
                st.plotly_chart(fig_share_change, use_container_width=True)

    # 구분선을 출력합니다.
    st.divider()

    # 연도별 분석 영역 제목을 출력합니다.
    st.subheader("📈 연도별 분석")

    # 연도별 분석 차트를 2개 컬럼으로 배치합니다.
    c7, c8 = st.columns(2)

    with c7:
        # 연도별 순증 비교 데이터가 없으면 경고 문구를 출력합니다.
        if filtered_yearly_df.empty:
            st.warning("연도별 순증 비교를 그릴 데이터가 없습니다.")
        else:
            # 연도별 순증 비교 막대그래프를 생성합니다.
            fig_yearly = bar_chart(
                filtered_yearly_df,
                x="year_num",
                y="yearly_increase",
                color="region_name",
                title="연도별 순증 비교",
                y_title="연도별 순증",
                barmode="group",
            )

            # 그래프를 화면에 출력합니다.
            st.plotly_chart(fig_yearly, use_container_width=True)

    with c8:
        # 최신월 스냅샷에서 누적 등록대수 상위 10개 지역 데이터를 추출합니다.
        donut_base = latest_region_snapshot.dropna(subset=["cumulative_count"]).sort_values(
            "cumulative_count",
            ascending=False,
        ).head(10)

        # 데이터가 없으면 경고 문구를 출력합니다.
        if donut_base.empty:
            st.warning("최신월 기준 비중 차트를 그릴 데이터가 없습니다.")
        else:
            # 최신월 기준 누적 등록 비중 Top 10 도넛 차트를 생성합니다.
            fig_donut = donut_chart(
                donut_base,
                names="region_name",
                values="cumulative_count",
                title="최신월 기준 누적 등록 비중 Top 10",
            )

            # 그래프를 화면에 출력합니다.
            st.plotly_chart(fig_donut, use_container_width=True)

    # 연도별 순증 해석에 대한 안내 문구를 출력합니다.
    st.info("마지막 연도는 12월까지 모두 채워지지 않았을 수 있으므로 YTD 성격으로 해석해야 합니다.")

    # 구분선을 출력합니다.
    st.divider()

    # 최신월 랭킹 영역 제목을 출력합니다.
    st.subheader("🏆 최신월 랭킹")

    # 최신월 지역 데이터가 비어 있으면 경고 문구를 출력합니다.
    if latest_region_snapshot.empty:
        st.warning("최신월 지역 데이터가 없습니다.")
    else:
        # 랭킹 차트를 2개 컬럼으로 배치합니다.
        c9, c10 = st.columns(2)

        with c9:
            # 누적 등록대수 기준 상위 10개 지역을 추출합니다.
            rank_cum = latest_region_snapshot.dropna(subset=["cumulative_count"]).sort_values(
                "cumulative_count",
                ascending=False,
            ).head(10)

            # 데이터가 없으면 경고 문구를 출력합니다.
            if rank_cum.empty:
                st.warning("누적 등록대수 랭킹 데이터가 없습니다.")
            else:
                # 누적 등록대수 Top 10 가로 막대그래프를 생성합니다.
                fig_rank_cum = horizontal_bar(
                    rank_cum.sort_values("cumulative_count"),
                    x="cumulative_count",
                    y="region_name",
                    title="최신월 누적 등록대수 Top 10",
                    x_title="누적 등록대수",
                )

                # 그래프를 화면에 출력합니다.
                st.plotly_chart(fig_rank_cum, use_container_width=True)

        with c10:
            # 월별 순증 기준 상위 10개 지역을 추출합니다.
            rank_mom = latest_region_snapshot.dropna(subset=["monthly_increase"]).sort_values(
                "monthly_increase",
                ascending=False,
            ).head(10)

            # 데이터가 없으면 경고 문구를 출력합니다.
            if rank_mom.empty:
                st.warning("월별 순증 랭킹 데이터가 없습니다.")
            else:
                # 월별 순증 Top 10 가로 막대그래프를 생성합니다.
                fig_rank_mom = horizontal_bar(
                    rank_mom.sort_values("monthly_increase"),
                    x="monthly_increase",
                    y="region_name",
                    title="최신월 월별 순증 Top 10",
                    x_title="월별 순증",
                )

                # 그래프를 화면에 출력합니다.
                st.plotly_chart(fig_rank_mom, use_container_width=True)

    # 구분선을 출력합니다.
    st.divider()

    # 최신월 지역 현황 영역 제목을 출력합니다.
    st.subheader("📋 최신월 지역 현황")

    # 최신월 지역 현황 표에 사용할 컬럼만 골라 복사합니다.
    latest_table = latest_region_snapshot[[
        "region_name",
        "cumulative_count",
        "monthly_increase",
        "yoy_diff",
        "share_pct"
    ]].copy()

    # 컬럼명을 한글 표시용 이름으로 변경합니다.
    latest_table.columns = ["지역", "누적 등록대수", "월별 순증", "전년 동월 대비 증가", "점유율(%)"]

    # 최신월 지역 현황 표를 누적 등록대수 내림차순으로 정렬해 표시합니다.
    st.dataframe(
        latest_table.sort_values("누적 등록대수", ascending=False),
        use_container_width=True,
        hide_index=True,
    )

    # 상세 데이터 조회 영역 제목을 출력합니다.
    st.subheader("🔎 상세 데이터 조회")

    # 상세 조회 표에 사용할 컬럼만 골라 복사합니다.
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

    # 기준월은 최신순, 지역명은 오름차순으로 정렬합니다.
    detail_df = detail_df.sort_values(["base_ym", "region_name"], ascending=[False, True])

    # 화면에 표시하기 전, 기준월(base_ym) 컬럼은 제거합니다.
    detail_df = detail_df.drop(columns=["base_ym"], errors="ignore")

    # 컬럼명을 한글 표시용 이름으로 변경합니다.
    detail_df.columns = ["연도", "월", "지역", "누적 등록대수", "월별 순증", "전년 동월 대비 증가", "점유율(%)"]

    # 상세 데이터를 표 형태로 출력합니다.
    st.dataframe(detail_df, use_container_width=True, hide_index=True)

    # 상세 데이터를 CSV 문자열로 변환하고 UTF-8-SIG 인코딩합니다.
    csv_data = detail_df.to_csv(index=False).encode("utf-8-sig")

    # CSV 다운로드 버튼을 출력합니다.
    st.download_button(
        label="CSV 다운로드",
        data=csv_data,
        file_name="ev_registration_dashboard_filtered.csv",
        mime="text/csv",
    )

    # 구분선을 출력합니다.
    st.divider()

    # 화면 해석 팁을 Markdown 형태로 출력합니다.
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