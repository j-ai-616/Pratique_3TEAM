# src/db/insert_data.py

from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os


BASE_DIR = Path(__file__).resolve().parents[2]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
PROCESSED_EV_DIR = PROCESSED_DIR / "ev_registration"

WIDE_FILE = PROCESSED_EV_DIR / "ev_registration_monthly_wide.csv"
LONG_FILE = PROCESSED_EV_DIR / "ev_registration_monthly_long.csv"


def get_engine():
    load_dotenv()

    db_user = os.getenv("MYSQL_USER")
    db_password = os.getenv("MYSQL_PASSWORD")
    db_host = os.getenv("MYSQL_HOST", "localhost")
    db_port = os.getenv("MYSQL_PORT", "3306")
    db_name = os.getenv("MYSQL_DATABASE")

    if not all([db_user, db_password, db_name]):
        raise ValueError("MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE 환경변수를 확인하세요.")

    db_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"
    engine = create_engine(db_url)
    return engine


def insert_region_master(engine):
    region_master_rows = [
        ("서울", 1),
        ("부산", 2),
        ("대구", 3),
        ("인천", 4),
        ("광주", 5),
        ("대전", 6),
        ("울산", 7),
        ("세종", 8),
        ("경기", 9),
        ("강원", 10),
        ("충북", 11),
        ("충남", 12),
        ("전북", 13),
        ("전남", 14),
        ("경북", 15),
        ("경남", 16),
        ("제주", 17),
        ("합계", 99),
    ]

    insert_sql = """
    INSERT INTO region_master (region_name, region_order)
    VALUES (:region_name, :region_order)
    ON DUPLICATE KEY UPDATE
        region_name = VALUES(region_name),
        region_order = VALUES(region_order)
    """

    with engine.begin() as conn:
        for region_name, region_order in region_master_rows:
            conn.execute(
                text(insert_sql),
                {
                    "region_name": region_name,
                    "region_order": region_order
                }
            )

    print("[완료] region_master 적재 완료")


def insert_ev_registration_monthly(engine):
    df = pd.read_csv(LONG_FILE)

    # 날짜형 변환
    df["년월"] = pd.to_datetime(df["년월"])

    # 컬럼명 DB 적재용 변환
    db_df = df.rename(columns={
        "년월": "base_ym"
    }).copy()

    # region_master와 join하기 위해 region_name 사용
    region_df = pd.read_sql("SELECT region_id, region_name FROM region_master", con=engine)
    db_df = db_df.merge(region_df, on="region_name", how="left")

    if db_df["region_id"].isna().any():
        bad_rows = db_df[db_df["region_id"].isna()][["region_name"]].drop_duplicates()
        raise ValueError(f"region_id 매핑 실패:\n{bad_rows}")

    final_df = db_df[[
        "base_ym",
        "year_num",
        "month_num",
        "region_id",
        "cumulative_count",
        "monthly_increase",
        "yoy_diff",
        "share_pct",
        "region_order",
        "is_latest_ym"
    ]].copy()

    with engine.begin() as conn:
        # 기존 데이터 삭제 후 재적재 방식
        conn.execute(text("DELETE FROM ev_registration_monthly"))

    final_df.to_sql(
        name="ev_registration_monthly",
        con=engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000
    )

    print("[완료] ev_registration_monthly 적재 완료")
    print(final_df.head())


def run():
    engine = get_engine()
    insert_region_master(engine)
    insert_ev_registration_monthly(engine)
    print("[전체 완료] MySQL 적재 완료")


if __name__ == "__main__":
    run()