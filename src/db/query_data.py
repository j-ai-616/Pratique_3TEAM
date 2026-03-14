import os
from pathlib import Path

import pandas as pd
import pymysql
from dotenv import load_dotenv


# --------------------------------------------------
# .env 로드
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


# --------------------------------------------------
# DB 연결
# --------------------------------------------------
def get_connection():
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", 3306)),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


# --------------------------------------------------
# 공통 조회 함수
# --------------------------------------------------
def fetch_dataframe(sql, params=None):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or [])
            rows = cursor.fetchall()
        df = pd.DataFrame(rows)
        return df
    finally:
        conn.close()


# --------------------------------------------------
# 공통 문자열 정리
# --------------------------------------------------
def clean_text_series(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.strip()
        .replace({"None": None, "nan": None, "NaN": None, "": None})
    )


# --------------------------------------------------
# 헤더행/이상행 제거
# --------------------------------------------------
def remove_header_like_rows(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    bad_pairs = [
        ("region_name", "region_name"),
        ("station_name", "station_name"),
        ("address", "address"),
        ("charge_type", "charge_type"),
        ("status_name", "status_name"),
        ("operator_name", "operator_name"),
        ("available_time", "available_time"),
        ("phone", "phone"),
    ]

    result = df.copy()

    for col, bad_value in bad_pairs:
        if col in result.columns:
            result = result[result[col].astype(str).str.strip() != bad_value]

    return result


# --------------------------------------------------
# 조회 결과 후처리
# --------------------------------------------------
def postprocess_charger_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    result = df.copy()

    text_cols = [
        "region_name",
        "station_source_id",
        "station_name",
        "address",
        "address_detail",
        "operator_name",
        "available_time",
        "phone",
        "charger_source_id",
        "charge_type",
        "status_name",
    ]

    for col in text_cols:
        if col in result.columns:
            result[col] = clean_text_series(result[col])

    # 위경도 숫자 변환
    if "latitude" in result.columns:
        result["latitude"] = pd.to_numeric(result["latitude"], errors="coerce")
    if "longitude" in result.columns:
        result["longitude"] = pd.to_numeric(result["longitude"], errors="coerce")

    # station_id / charger_id 숫자 변환
    if "station_id" in result.columns:
        result["station_id"] = pd.to_numeric(result["station_id"], errors="coerce")
    if "charger_id" in result.columns:
        result["charger_id"] = pd.to_numeric(result["charger_id"], errors="coerce")

    # 헤더행 같은 이상 데이터 제거
    result = remove_header_like_rows(result)

    # 완전 중복 제거
    result = result.drop_duplicates()

    return result


# --------------------------------------------------
# 필터 옵션 조회
# --------------------------------------------------
def get_region_names():
    sql = """
    SELECT DISTINCT region_name
    FROM charger_station
    WHERE region_name IS NOT NULL
      AND TRIM(region_name) <> ''
    ORDER BY region_name
    """
    df = fetch_dataframe(sql)
    if df.empty:
        return []
    return df["region_name"].dropna().astype(str).str.strip().tolist()


def get_charge_types():
    sql = """
    SELECT DISTINCT charge_type
    FROM charge_info
    WHERE charge_type IS NOT NULL
      AND TRIM(charge_type) <> ''
    ORDER BY charge_type
    """
    df = fetch_dataframe(sql)
    if df.empty:
        return []
    return df["charge_type"].dropna().astype(str).str.strip().tolist()


def get_status_names():
    sql = """
    SELECT DISTINCT status_name
    FROM charge_info
    WHERE status_name IS NOT NULL
      AND TRIM(status_name) <> ''
    ORDER BY status_name
    """
    df = fetch_dataframe(sql)
    if df.empty:
        return []
    return df["status_name"].dropna().astype(str).str.strip().tolist()


# --------------------------------------------------
# 충전소 + 충전기 조회
# --------------------------------------------------
def get_charger_data(region_name=None, charge_type=None, status_name=None):
    sql = """
    SELECT
        cs.station_id AS station_id,
        cs.station_source_id AS station_source_id,
        cs.station_name AS station_name,
        cs.address AS address,
        cs.address_detail AS address_detail,
        cs.region_name AS region_name,
        cs.latitude AS latitude,
        cs.longitude AS longitude,
        cs.operator_name AS operator_name,
        cs.available_time AS available_time,
        cs.phone AS phone,
        cs.registered_at AS registered_at,
        ci.charger_id AS charger_id,
        ci.charger_source_id AS charger_source_id,
        ci.charge_type AS charge_type,
        ci.status_name AS status_name
    FROM charger_station cs
    LEFT JOIN charge_info ci
        ON cs.station_id = ci.station_id
    WHERE 1 = 1
    """

    params = []

    if region_name and region_name != "전체":
        sql += " AND cs.region_name = %s"
        params.append(region_name)

    if charge_type and charge_type != "전체":
        sql += " AND ci.charge_type = %s"
        params.append(charge_type)

    if status_name and status_name != "전체":
        sql += " AND ci.status_name = %s"
        params.append(status_name)

    sql += """
    ORDER BY
        cs.region_name,
        cs.station_name,
        ci.charge_type,
        ci.status_name
    """

    df = fetch_dataframe(sql, params)
    df = postprocess_charger_df(df)
    return df