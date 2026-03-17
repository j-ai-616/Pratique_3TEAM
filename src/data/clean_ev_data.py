# src/data/clean_ev_data.py

# 이 스크립트는 전기차 등록 현황 원본 엑셀 파일을 읽어서,
# 분석과 화면 출력에 적합한 형태의 CSV 파일로 정제/변환하는 전처리 스크립트입니다.
#
# 이 스크립트의 핵심 역할은 다음과 같습니다.
#
# 1) 원본 엑셀 파일 읽기
#    - 월별 전기차 등록 현황 원본 파일(.xls)을 읽어옵니다.
#    - 실제 헤더가 시작되는 행을 기준으로 컬럼을 읽고,
#      완전히 빈 행과 컬럼명 공백을 정리합니다.
#
# 2) wide 형태 데이터 정제
#    - "년월" + 지역별 누적 등록 대수 형태의 wide 데이터 구조를 정리합니다.
#    - 지역 컬럼명을 표준화하고, 숫자형으로 변환하며,
#      날짜형 컬럼과 연/월 파생 컬럼을 생성합니다.
#    - 지역 합계와 "합계" 컬럼이 일치하는지 검증합니다.
#
# 3) wide -> long 형태 변환
#    - 분석과 시각화에 더 유리한 long 형태로 변환합니다.
#    - 지역별 월간 순증, 전년동월 대비 증가(yoy_diff), 점유율(share_pct),
#      최신 년월 여부(is_latest_ym) 같은 파생 컬럼을 추가합니다.
#
# 4) 전처리 결과 저장
#    - 정제된 wide 데이터와 long 데이터를 각각 CSV 파일로 저장합니다.
#
# 이 스크립트는 "직접 Streamlit 화면을 그리는 역할"은 하지 않고,
# 이후 다른 스크립트들이 쉽게 사용할 수 있도록
# 전기차 등록 현황 데이터를 미리 깨끗하게 가공해 두는 데이터 준비 스크립트입니다.
#
# 이 스크립트와 상호작용하는 주요 스크립트는 다음과 같습니다.
#
# 1) src/data/region_processing.py
#    - standardize_region_name: 지역명 표준화 함수
#    - REGION_ORDER: 지역 컬럼의 표준 정렬 순서
#    - 이 스크립트는 region_processing.py의 기준을 사용해
#      원본 엑셀의 지역 컬럼명을 통일하고 순서를 맞춥니다.
#
# 2) src/db/query_data.py
#    - 저장된 전처리 CSV 파일(특히 long 또는 wide 형태)을 읽어
#      Streamlit 화면에서 사용할 DataFrame으로 불러오는 역할을 합니다.
#    - 즉, 이 스크립트가 만든 결과물을 query_data.py가 다시 읽어갑니다.
#
# 3) src/data/region_ev_section.py
#    - 지역별 전기차 등록 현황 화면을 구성하는 스크립트입니다.
#    - 보통 query_data.py를 통해 전처리된 데이터를 받아
#      사용자에게 그래프/표/지표 형태로 보여주는 역할을 합니다.
#
# 4) src/app/main_app.py
#    - 전체 앱 진입점이며 메뉴 라우팅을 담당합니다.
#    - 지역별 전기차 등록 현황 메뉴가 선택되면,
#      궁극적으로 이 스크립트가 사전에 정리해 둔 데이터가
#      query_data.py를 거쳐 화면으로 전달됩니다.
#
# 전체 데이터 흐름은 보통 다음과 같습니다.
#
# 원본 엑셀 파일
#   -> clean_ev_data.py (현재 스크립트)
#   -> processed 폴더에 wide/long CSV 저장
#   -> query_data.py 에서 CSV 읽기
#   -> region_ev_section.py 에서 화면 출력
#   -> main_app.py 에서 메뉴 연결
#
# 정리하면,
# 이 스크립트는 전기차 등록 현황 데이터를
# "원본 엑셀 -> 분석/시각화용 정제 데이터"로 바꾸는
# 전처리 전담 스크립트입니다.

from pathlib import Path
import pandas as pd

from src.data.region_processing import standardize_region_name, REGION_ORDER


# 현재 파일(clean_ev_data.py)을 기준으로 프로젝트 루트 디렉터리를 계산합니다.
# 예: src/data/clean_ev_data.py 기준으로 두 단계 위를 프로젝트 루트로 간주합니다.
BASE_DIR = Path(__file__).resolve().parents[2]

# 원본 데이터가 들어 있는 상위 raw 폴더 경로입니다.
RAW_DIR = BASE_DIR / "data" / "raw"

# 전기차 등록 현황 원본 엑셀 파일이 위치한 폴더 경로입니다.
RAW_EV_DIR = RAW_DIR / "ev_registration"

# 전처리 결과 CSV 파일을 저장할 processed 폴더 경로입니다.
PROCESSED_DIR = BASE_DIR / "data" / "processed" / "ev_registration"

# 입력 원본 엑셀 파일 경로입니다.
INPUT_FILE = RAW_EV_DIR / "201001_202603_전기차등록현황.xls"

# 전처리 결과로 저장할 wide 형태 CSV 파일 경로입니다.
OUTPUT_WIDE_FILE = PROCESSED_DIR / "ev_registration_monthly_wide.csv"

# 전처리 결과로 저장할 long 형태 CSV 파일 경로입니다.
OUTPUT_LONG_FILE = PROCESSED_DIR / "ev_registration_monthly_long.csv"


def ensure_directories():
    # 전처리 결과를 저장할 폴더가 없으면 자동으로 생성합니다.
    # parents=True : 상위 폴더가 없어도 함께 생성
    # exist_ok=True : 이미 폴더가 있어도 오류를 내지 않음
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def read_raw_excel(file_path: Path) -> pd.DataFrame:
    """
    원본 엑셀은 header=3 에서 실제 컬럼이 시작됨.
    """
    # 원본 엑셀 파일을 읽어옵니다.
    # header=3 은 엑셀의 4번째 행을 실제 컬럼명(header)로 사용하겠다는 뜻입니다.
    df = pd.read_excel(file_path, header=3)

    # 모든 값이 비어 있는 행은 제거합니다.
    # 원본 엑셀에 불필요한 빈 행이 섞여 있을 수 있기 때문입니다.
    df = df.dropna(how="all").copy()

    # 컬럼명 문자열 앞뒤 공백을 제거합니다.
    # 예: " 서울 " -> "서울"
    df.columns = [str(col).strip() for col in df.columns]

    # 1차 정리된 원본 DataFrame을 반환합니다.
    return df


def clean_wide_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    wide 형태 정제:
    - 년월 날짜형 변환
    - 지역 컬럼명 표준화
    - 숫자형 변환
    - 오래된 순 -> 최신 순 정렬
    """
    # 원본 DataFrame 훼손을 방지하기 위해 복사본을 사용합니다.
    df = df.copy()

    # 컬럼명을 표준화합니다.
    # "년월" 컬럼은 그대로 두고,
    # 지역 컬럼들은 standardize_region_name()을 이용해 표준 명칭으로 바꿉니다.
    df.columns = [standardize_region_name(col) if col != "년월" else "년월" for col in df.columns]

    # 이 wide 데이터가 가져야 하는 기대 컬럼 순서를 정의합니다.
    # 첫 컬럼은 "년월", 이후는 REGION_ORDER에 정의된 지역 순서를 따릅니다.
    expected_cols = ["년월"] + REGION_ORDER

    # 실제 데이터에 없는 필수 컬럼이 있는지 검사합니다.
    missing_cols = [col for col in expected_cols if col not in df.columns]

    # 필수 컬럼이 하나라도 없으면 예외를 발생시켜 전처리를 중단합니다.
    if missing_cols:
        raise ValueError(f"필수 컬럼이 없습니다: {missing_cols}")

    # 컬럼 순서를 expected_cols 기준으로 정렬합니다.
    df = df[expected_cols].copy()

    # "년월" 값을 날짜형(datetime)으로 변환합니다.
    # 원래 값이 예: 2010-01 형태라고 가정하고 "-01"을 붙여 해당 월의 1일 날짜로 만듭니다.
    # format="%Y-%m-%d" 기준으로 변환하며, 실패한 값은 NaT로 처리합니다.
    df["년월"] = pd.to_datetime(df["년월"].astype(str) + "-01", format="%Y-%m-%d", errors="coerce")

    # "년월" 변환 결과 NaT가 하나라도 있으면
    # 어떤 행에서 실패했는지 찾아 예외를 발생시킵니다.
    if df["년월"].isna().any():
        bad_rows = df[df["년월"].isna()]
        raise ValueError(f"년월 변환 실패 행이 있습니다.\n{bad_rows}")

    # 숫자형으로 변환할 대상 컬럼은 REGION_ORDER에 포함된 지역 컬럼 전체입니다.
    numeric_cols = REGION_ORDER

    # 각 지역 컬럼에 대해 숫자형 변환을 수행합니다.
    for col in numeric_cols:
        # 우선 문자열로 변환한 뒤,
        # 천 단위 콤마를 제거하고 앞뒤 공백을 제거합니다.
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.strip()
        )

        # 정리된 문자열을 숫자형으로 변환합니다.
        # 변환 실패 시 NaN으로 처리합니다.
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 숫자형 변환 결과 NaN이 하나라도 있으면
    # 어떤 컬럼에서 실패가 발생했는지 집계하여 예외를 발생시킵니다.
    if df[numeric_cols].isna().any().any():
        null_summary = df[numeric_cols].isna().sum()
        raise ValueError(f"숫자형 변환 실패 컬럼이 있습니다.\n{null_summary[null_summary > 0]}")

    # "년월" 기준으로 오래된 월부터 최신 월 순으로 정렬합니다.
    df = df.sort_values("년월").reset_index(drop=True)

    # 분석과 필터링에 편리하도록 연도 숫자 컬럼을 생성합니다.
    df["year_num"] = df["년월"].dt.year

    # 분석과 필터링에 편리하도록 월 숫자 컬럼을 생성합니다.
    df["month_num"] = df["년월"].dt.month

    # 합계 검증을 수행합니다.
    # "합계" 컬럼을 제외한 지역별 값을 모두 합산한 뒤,
    # 실제 "합계" 컬럼과 일치하는지 검사합니다.
    region_cols_without_total = [c for c in REGION_ORDER if c != "합계"]

    # 지역별 합산 결과를 calc_sum 컬럼에 저장합니다.
    df["calc_sum"] = df[region_cols_without_total].sum(axis=1)

    # 계산된 합계(calc_sum)와 원본 합계("합계")가 일치하면 Y, 아니면 N으로 표시합니다.
    df["sum_match_yn"] = (df["calc_sum"] == df["합계"]).map({True: "Y", False: "N"})

    # 합계 불일치 행 수를 계산합니다.
    mismatch_count = (df["sum_match_yn"] == "N").sum()

    # 불일치가 하나라도 있으면 경고 메시지를 출력합니다.
    # 단, 예외를 발생시키지는 않고 경고만 보여줍니다.
    if mismatch_count > 0:
        print(f"[경고] 합계 불일치 행 수: {mismatch_count}")

    # 정제 완료된 wide 형태 DataFrame을 반환합니다.
    return df


def convert_wide_to_long(df_wide: pd.DataFrame) -> pd.DataFrame:
    """
    wide -> long 변환 후
    월별 순증(monthly_increase), 전년동월 대비 증가(yoy_diff), 점유율(share_pct) 생성
    """
    # melt 시 그대로 유지할 식별 컬럼 목록입니다.
    # 날짜와 연/월 파생 컬럼은 유지하고,
    # 지역별 등록 대수 컬럼만 세로 방향으로 풀어냅니다.
    id_vars = ["년월", "year_num", "month_num"]

    # 세로 방향으로 변환할 값 컬럼 목록입니다.
    # REGION_ORDER에 정의된 지역 컬럼 전체를 사용합니다.
    value_vars = REGION_ORDER

    # wide -> long 변환을 수행합니다.
    # 예: 서울, 부산, 대구 ... 열로 펼쳐진 데이터를
    #     region_name / cumulative_count 형태의 행 구조로 변환합니다.
    df_long = df_wide.melt(
        id_vars=id_vars,
        value_vars=value_vars,
        var_name="region_name",
        value_name="cumulative_count"
    )

    # 지역별 정렬 기준 번호를 만들기 위한 매핑 딕셔너리입니다.
    # REGION_ORDER에 정의된 순서대로 1, 2, 3 ... 값을 부여합니다.
    region_order_map = {region: idx + 1 for idx, region in enumerate(REGION_ORDER)}

    # 각 지역명(region_name)에 해당하는 정렬 순서를 region_order 컬럼으로 추가합니다.
    df_long["region_order"] = df_long["region_name"].map(region_order_map)

    # 지역명 + 년월 기준으로 정렬합니다.
    # 이후 diff() 계산을 정확히 하기 위해 반드시 정렬이 필요합니다.
    df_long = df_long.sort_values(["region_name", "년월"]).reset_index(drop=True)

    # 월별 순증(monthly_increase)을 계산합니다.
    # 같은 지역 내에서 전월 대비 누적 등록 대수 차이를 구합니다.
    df_long["monthly_increase"] = (
        df_long.groupby("region_name")["cumulative_count"].diff()
    )

    # 각 지역의 첫 번째 관측값은 전월 데이터가 없으므로 NaN이 됩니다.
    # 실무 편의상 첫 행은 누적값 자체를 monthly_increase로 간주합니다.
    df_long["monthly_increase"] = df_long["monthly_increase"].fillna(df_long["cumulative_count"])

    # 전년 동월 대비 증가(yoy_diff)를 계산합니다.
    # 같은 지역 내에서 12개월 전과의 차이를 구합니다.
    df_long["yoy_diff"] = (
        df_long.groupby("region_name")["cumulative_count"].diff(12)
    )

    # 전국 합계("합계") 데이터만 따로 추출하여 total_df를 만듭니다.
    # 이후 각 지역의 점유율 계산에 사용합니다.
    total_df = df_long[df_long["region_name"] == "합계"][["년월", "cumulative_count"]].copy()

    # 합계 컬럼명을 더 의미가 명확하도록 변경합니다.
    total_df = total_df.rename(columns={"cumulative_count": "total_cumulative_count"})

    # 원본 long 데이터와 전국 합계 데이터를 "년월" 기준으로 병합합니다.
    # 각 지역 행마다 같은 달의 전국 합계 값을 붙이기 위한 과정입니다.
    df_long = df_long.merge(total_df, on="년월", how="left")

    # 점유율(share_pct)을 계산합니다.
    # 지역 누적 등록 대수를 전국 누적 등록 대수로 나눈 뒤 백분율로 변환합니다.
    df_long["share_pct"] = (
        df_long["cumulative_count"] / df_long["total_cumulative_count"] * 100
    ).round(4)

    # 전국 합계 행은 논리적으로 점유율이 항상 100%이므로 강제로 100.0으로 설정합니다.
    df_long.loc[df_long["region_name"] == "합계", "share_pct"] = 100.0

    # 가장 최신 년월을 찾습니다.
    latest_ym = df_long["년월"].max()

    # 각 행이 최신 년월인지 여부를 is_latest_ym 컬럼으로 표시합니다.
    # 최신 년월이면 Y, 아니면 N으로 저장합니다.
    df_long["is_latest_ym"] = (df_long["년월"] == latest_ym).map({True: "Y", False: "N"})

    # long 형태 전환 및 파생 컬럼 생성이 끝난 DataFrame을 반환합니다.
    return df_long


def save_processed_files(df_wide: pd.DataFrame, df_long: pd.DataFrame):
    # wide CSV 출력 경로의 상위 폴더가 없으면 생성합니다.
    OUTPUT_WIDE_FILE.parent.mkdir(parents=True, exist_ok=True)

    # 정제된 wide DataFrame을 CSV 파일로 저장합니다.
    # utf-8-sig 인코딩을 사용하여 한글이 Excel에서 깨질 가능성을 줄입니다.
    df_wide.to_csv(OUTPUT_WIDE_FILE, index=False, encoding="utf-8-sig")

    # 변환된 long DataFrame을 CSV 파일로 저장합니다.
    df_long.to_csv(OUTPUT_LONG_FILE, index=False, encoding="utf-8-sig")

    # 저장 완료 메시지를 콘솔에 출력합니다.
    print(f"[완료] wide 저장: {OUTPUT_WIDE_FILE}")
    print(f"[완료] long 저장: {OUTPUT_LONG_FILE}")


def run():
    # 전처리 결과 저장 폴더가 존재하도록 보장합니다.
    ensure_directories()

    # 원본 파일 읽기 시작 메시지를 출력합니다.
    print(f"[시작] 원본 파일 읽기: {INPUT_FILE}")

    # 원본 엑셀 파일을 읽습니다.
    df_raw = read_raw_excel(INPUT_FILE)

    # wide 형태 정제 시작 메시지를 출력합니다.
    print("[진행] wide 정제")

    # 원본 DataFrame을 wide 형태 기준으로 정제합니다.
    df_wide = clean_wide_dataframe(df_raw)

    # long 변환 및 파생 컬럼 생성 시작 메시지를 출력합니다.
    print("[진행] long 변환 및 파생컬럼 생성")

    # 정제된 wide 데이터를 long 형태로 변환합니다.
    df_long = convert_wide_to_long(df_wide)

    # CSV 저장 시작 메시지를 출력합니다.
    print("[진행] CSV 저장")

    # wide/long 결과를 각각 CSV 파일로 저장합니다.
    save_processed_files(df_wide, df_long)

    # 전처리 결과 샘플 확인을 위해 wide 상위 5행을 출력합니다.
    print("\n[샘플] wide 상위 5행")
    print(df_wide.head())

    # 전처리 결과 샘플 확인을 위해 long 상위 10행을 출력합니다.
    print("\n[샘플] long 상위 10행")
    print(df_long.head(10))

    # 전체 요약 정보를 출력합니다.
    print("\n[요약]")
    print(f"wide shape: {df_wide.shape}")
    print(f"long shape: {df_long.shape}")
    print(f"기간: {df_wide['년월'].min().date()} ~ {df_wide['년월'].max().date()}")


if __name__ == "__main__":
    # 이 파일을 직접 실행한 경우 run() 함수를 실행합니다.
    # 즉, 전처리 전체 파이프라인을 시작합니다.
    run()