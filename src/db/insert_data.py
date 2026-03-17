# src/db/insert_data.py

# 이 스크립트는 전처리된 전기차 등록 현황 CSV 데이터를 MySQL 데이터베이스에 적재하는 역할을 합니다.
#
# 이 스크립트의 핵심 기능은 다음과 같습니다.
#
# 1) DB 연결 엔진 생성
#    - .env 파일에 저장된 MySQL 접속 정보를 읽어 SQLAlchemy 엔진을 생성합니다.
#
# 2) 지역 기준 테이블(region_master) 적재
#    - 지역명과 지역 정렬 순서를 region_master 테이블에 입력합니다.
#    - 이미 같은 지역이 존재하면 ON DUPLICATE KEY UPDATE 방식으로 갱신합니다.
#
# 3) 월별 전기차 등록 현황 테이블(ev_registration_monthly) 적재
#    - clean_ev_data.py에서 생성한 long 형태 CSV 파일을 읽습니다.
#    - region_master 테이블과 region_name 기준으로 매핑하여 region_id를 붙입니다.
#    - 최종적으로 ev_registration_monthly 테이블에 데이터를 재적재합니다.
#
# 4) 전체 적재 파이프라인 실행
#    - run() 함수가 호출되면
#      region_master 적재 -> ev_registration_monthly 적재 순으로 실행됩니다.
#
# 이 스크립트는 직접 Streamlit 화면을 그리는 역할은 하지 않습니다.
# 대신, 화면에서 사용할 수 있는 DB 테이블을 준비하는 "데이터 적재(ETL 적재 단계)" 역할을 합니다.
#
# 이 스크립트와 상호작용하는 주요 스크립트는 다음과 같습니다.
#
# 1) src/data/clean_ev_data.py
#    - 가장 직접적으로 연결되는 전처리 스크립트입니다.
#    - 이 스크립트가 생성한
#      ev_registration_monthly_wide.csv
#      ev_registration_monthly_long.csv
#      파일 중 특히 LONG_FILE을 읽어서 DB에 적재합니다.
#
# 2) MySQL의 region_master / ev_registration_monthly 테이블
#    - 현재 스크립트가 실제로 데이터를 넣는 대상 테이블입니다.
#
# 3) vw_ev_registration_monthly View
#    - ev_registration_monthly와 region_master를 기반으로 구성되는 조회용 View입니다.
#    - 이후 지역별 전기차 등록 현황 화면에서 이 View를 사용하게 됩니다.
#
# 4) src/data/region_ev_section.py
#    - 지역별 전기차 등록 현황 화면 렌더링 스크립트입니다.
#    - 이 스크립트는 직접 insert_data.py를 호출하지는 않지만,
#      insert_data.py가 적재한 DB 데이터를 기반으로 분석 화면을 구성합니다.
#
# 5) src/app/main_app.py
#    - 전체 앱 진입점이며, 사용자가 1번 탭을 선택하면
#      region_ev_section.py를 통해 최종적으로 DB 데이터를 사용하게 됩니다.
#
# 전체 흐름은 보통 다음과 같습니다.
#
# 원본 엑셀
#   -> clean_ev_data.py
#   -> processed CSV 생성
#   -> insert_data.py (현재 스크립트)
#   -> MySQL region_master / ev_registration_monthly 적재
#   -> View(vw_ev_registration_monthly) 조회
#   -> region_ev_section.py 화면 출력
#
# 정리하면,
# 이 스크립트는 "전처리된 전기차 등록 현황 CSV를 MySQL에 적재하여
# 이후 분석/시각화 화면이 사용할 수 있도록 준비하는 DB 적재 전담 스크립트"입니다.

from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os


# 현재 파일(insert_data.py)을 기준으로 프로젝트 루트 디렉터리를 계산합니다.
# 예: src/db/insert_data.py 기준으로 두 단계 위를 프로젝트 루트로 간주합니다.
BASE_DIR = Path(__file__).resolve().parents[2]

# 전처리된 데이터가 저장되는 processed 폴더 경로입니다.
PROCESSED_DIR = BASE_DIR / "data" / "processed"

# 전기차 등록 현황 전처리 결과가 저장되는 폴더 경로입니다.
PROCESSED_EV_DIR = PROCESSED_DIR / "ev_registration"

# wide 형태 CSV 파일 경로입니다.
# 현재 스크립트에서는 직접 사용하지 않지만, 함께 관리되는 전처리 결과물 경로입니다.
WIDE_FILE = PROCESSED_EV_DIR / "ev_registration_monthly_wide.csv"

# long 형태 CSV 파일 경로입니다.
# 실제 DB 적재 시 사용하는 핵심 입력 파일입니다.
LONG_FILE = PROCESSED_EV_DIR / "ev_registration_monthly_long.csv"


def get_engine():
    # .env 파일을 로드하여 환경변수를 읽을 수 있도록 합니다.
    load_dotenv()

    # MySQL 사용자명을 환경변수에서 읽습니다.
    db_user = os.getenv("MYSQL_USER")

    # MySQL 비밀번호를 환경변수에서 읽습니다.
    db_password = os.getenv("MYSQL_PASSWORD")

    # MySQL 호스트를 환경변수에서 읽습니다.
    # 값이 없으면 기본값으로 localhost를 사용합니다.
    db_host = os.getenv("MYSQL_HOST", "localhost")

    # MySQL 포트를 환경변수에서 읽습니다.
    # 값이 없으면 기본값 3306을 사용합니다.
    db_port = os.getenv("MYSQL_PORT", "3306")

    # 사용할 데이터베이스 이름을 환경변수에서 읽습니다.
    db_name = os.getenv("MYSQL_DATABASE")

    # 필수 환경변수(user, password, database)가 하나라도 없으면 예외를 발생시킵니다.
    if not all([db_user, db_password, db_name]):
        raise ValueError("MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE 환경변수를 확인하세요.")

    # SQLAlchemy용 MySQL 접속 URL을 생성합니다.
    db_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"

    # create_engine()으로 DB 엔진을 생성합니다.
    engine = create_engine(db_url)

    # 생성된 엔진 객체를 반환합니다.
    return engine


def insert_region_master(engine):
    # region_master 테이블에 넣을 지역 기준 데이터 목록입니다.
    # 각 항목은 (지역명, 정렬순서) 형태의 튜플입니다.
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

    # region_master 테이블에 데이터를 넣는 SQL입니다.
    # 이미 같은 키가 존재하면 UPDATE 하도록 작성되어 있습니다.
    insert_sql = """
    INSERT INTO region_master (region_name, region_order)
    VALUES (:region_name, :region_order)
    ON DUPLICATE KEY UPDATE
        region_name = VALUES(region_name),
        region_order = VALUES(region_order)
    """

    # engine.begin() 컨텍스트를 사용하여 트랜잭션 단위로 안전하게 실행합니다.
    with engine.begin() as conn:
        # region_master_rows를 순회하면서 한 행씩 INSERT / UPDATE 합니다.
        for region_name, region_order in region_master_rows:
            conn.execute(
                text(insert_sql),
                {
                    "region_name": region_name,
                    "region_order": region_order
                }
            )

    # 작업 완료 메시지를 콘솔에 출력합니다.
    print("[완료] region_master 적재 완료")


def insert_ev_registration_monthly(engine):
    # 전처리된 long 형태 CSV 파일을 읽어 DataFrame으로 로드합니다.
    df = pd.read_csv(LONG_FILE)

    # "년월" 컬럼을 날짜형(datetime)으로 변환합니다.
    df["년월"] = pd.to_datetime(df["년월"])

    # DB 테이블 컬럼명에 맞추기 위해 컬럼명을 변경합니다.
    # 예: "년월" -> "base_ym"
    db_df = df.rename(columns={
        "년월": "base_ym"
    }).copy()

    # region_master와 조인하기 위해 region_id, region_name 정보를 조회합니다.
    region_df = pd.read_sql("SELECT region_id, region_name FROM region_master", con=engine)

    # CSV 데이터의 region_name과 region_master의 region_name을 기준으로 병합합니다.
    # 이를 통해 각 행에 region_id를 붙입니다.
    db_df = db_df.merge(region_df, on="region_name", how="left")

    # 병합 결과 region_id가 비어 있는 행이 있으면
    # region_master 매핑에 실패한 것이므로 예외를 발생시킵니다.
    if db_df["region_id"].isna().any():
        bad_rows = db_df[db_df["region_id"].isna()][["region_name"]].drop_duplicates()
        raise ValueError(f"region_id 매핑 실패:\n{bad_rows}")

    # 실제 ev_registration_monthly 테이블에 적재할 최종 컬럼만 선택합니다.
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

    # 적재 전 기존 데이터를 모두 삭제하는 방식으로 재적재합니다.
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM ev_registration_monthly"))

    # 최종 DataFrame을 ev_registration_monthly 테이블에 append 방식으로 적재합니다.
    # method="multi" 와 chunksize=1000 설정으로 대량 삽입 성능을 개선합니다.
    final_df.to_sql(
        name="ev_registration_monthly",
        con=engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000
    )

    # 적재 완료 메시지와 샘플 데이터를 콘솔에 출력합니다.
    print("[완료] ev_registration_monthly 적재 완료")
    print(final_df.head())


def run():
    # DB 엔진을 생성합니다.
    engine = get_engine()

    # region_master 기준 데이터를 먼저 적재합니다.
    insert_region_master(engine)

    # 월별 전기차 등록 현황 데이터를 적재합니다.
    insert_ev_registration_monthly(engine)

    # 전체 작업 완료 메시지를 출력합니다.
    print("[전체 완료] MySQL 적재 완료")


if __name__ == "__main__":
    # 이 파일을 직접 실행한 경우 run() 함수를 호출합니다.
    # 즉, 전체 DB 적재 파이프라인을 시작합니다.
    run()