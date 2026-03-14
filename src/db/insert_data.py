from pathlib import Path
import pandas as pd
import pymysql
from dotenv import load_dotenv
import os

# --------------------------------------------------
# 환경변수 로드
# --------------------------------------------------
load_dotenv()

DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_PORT = int(os.getenv("MYSQL_PORT", 3306))
DB_USER = os.getenv("MYSQL_USER", "root")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
DB_NAME = os.getenv("MYSQL_DATABASE", "car1_db")

# --------------------------------------------------
# 경로 설정
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[2]
STATION_FILE = BASE_DIR / "data" / "processed" / "charger" / "charger_station.csv"
CHARGER_FILE = BASE_DIR / "data" / "processed" / "charger" / "charger_charger.csv"


# --------------------------------------------------
# DB 연결
# --------------------------------------------------
def get_connection():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
        autocommit=False,
        cursorclass=pymysql.cursors.DictCursor
    )


# --------------------------------------------------
# CSV 읽기
# --------------------------------------------------
def read_csv_file(file_path: Path) -> pd.DataFrame:
    if not file_path.exists():
        raise FileNotFoundError(f"파일이 없습니다: {file_path}")
    return pd.read_csv(file_path, encoding="utf-8-sig")


# --------------------------------------------------
# NaN -> None 변환
# --------------------------------------------------
def convert_nan_to_none(value):
    if pd.isna(value):
        return None
    return value


# --------------------------------------------------
# 충전소(station) 삽입
# --------------------------------------------------
def insert_station_data(conn, df: pd.DataFrame):
    sql = """
    INSERT INTO charger_station (
        station_source_id,
        station_name,
        address,
        address_detail,
        region_name,
        latitude,
        longitude,
        operator_name,
        available_time,
        phone,
        registered_at
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        station_name = VALUES(station_name),
        address = VALUES(address),
        address_detail = VALUES(address_detail),
        region_name = VALUES(region_name),
        latitude = VALUES(latitude),
        longitude = VALUES(longitude),
        operator_name = VALUES(operator_name),
        available_time = VALUES(available_time),
        phone = VALUES(phone),
        registered_at = VALUES(registered_at)
    """

    rows = []
    for _, row in df.iterrows():
        rows.append((
            convert_nan_to_none(row.get("station_source_id")),
            convert_nan_to_none(row.get("station_name")),
            convert_nan_to_none(row.get("address")),
            convert_nan_to_none(row.get("address_detail")),
            convert_nan_to_none(row.get("region_name")),
            convert_nan_to_none(row.get("latitude")),
            convert_nan_to_none(row.get("longitude")),
            convert_nan_to_none(row.get("operator_name")),
            convert_nan_to_none(row.get("available_time")),
            convert_nan_to_none(row.get("phone")),
            convert_nan_to_none(row.get("registered_at")),
        ))

    with conn.cursor() as cursor:
        cursor.executemany(sql, rows)


# --------------------------------------------------
# 충전기(charger) 삽입
# charger_station 테이블의 station_id를 찾아 연결
# --------------------------------------------------
def insert_charger_data(conn, df: pd.DataFrame):
    find_station_sql = """
    SELECT station_id
    FROM charger_station
    WHERE station_source_id = %s
    LIMIT 1
    """

    insert_sql = """
    INSERT INTO charge_info (
        charger_source_id,
        station_id,
        charge_type,
        status_name,
        operator_name
    )
    VALUES (%s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        station_id = VALUES(station_id),
        charge_type = VALUES(charge_type),
        status_name = VALUES(status_name),
        operator_name = VALUES(operator_name)
    """

    with conn.cursor() as cursor:
        for _, row in df.iterrows():
            station_source_id = convert_nan_to_none(row.get("station_source_id"))

            cursor.execute(find_station_sql, (station_source_id,))
            station_result = cursor.fetchone()

            if not station_result:
                print(f"[WARN] station_source_id 매칭 실패: {station_source_id}")
                continue

            station_id = station_result["station_id"]

            cursor.execute(
                insert_sql,
                (
                    convert_nan_to_none(row.get("charger_source_id")),
                    station_id,
                    convert_nan_to_none(row.get("charge_type")),
                    convert_nan_to_none(row.get("status_name")),
                    convert_nan_to_none(row.get("operator_name")),
                )
            )


# --------------------------------------------------
# 실행
# --------------------------------------------------
def run():
    station_df = read_csv_file(STATION_FILE)
    charger_df = read_csv_file(CHARGER_FILE)

    conn = get_connection()

    try:
        print("charger_station 적재 시작...")
        insert_station_data(conn, station_df)
        conn.commit()
        print("charger_station 적재 완료")

        print("charge_info 적재 시작...")
        insert_charger_data(conn, charger_df)
        conn.commit()
        print("charge_info 적재 완료")

    except Exception as e:
        conn.rollback()
        print("에러 발생, 롤백합니다.")
        print(e)

    finally:
        conn.close()


if __name__ == "__main__":
    run()