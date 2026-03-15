# src/data/clean_ev_data.py

from pathlib import Path
import pandas as pd

from src.data.region_processing import standardize_region_name, REGION_ORDER


BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "data" / "raw"
RAW_EV_DIR = RAW_DIR / "ev_registration"
PROCESSED_DIR = BASE_DIR / "data" / "processed" / "ev_registration"

INPUT_FILE = RAW_EV_DIR / "201001_202603_전기차등록현황.xls"
OUTPUT_WIDE_FILE = PROCESSED_DIR / "ev_registration_monthly_wide.csv"
OUTPUT_LONG_FILE = PROCESSED_DIR / "ev_registration_monthly_long.csv"

def ensure_directories():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def read_raw_excel(file_path: Path) -> pd.DataFrame:
    """
    원본 엑셀은 header=3 에서 실제 컬럼이 시작됨.
    """
    df = pd.read_excel(file_path, header=3)

    # 완전히 빈 행 제거
    df = df.dropna(how="all").copy()

    # 컬럼명 공백 제거
    df.columns = [str(col).strip() for col in df.columns]

    return df


def clean_wide_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    wide 형태 정제:
    - 년월 날짜형 변환
    - 지역 컬럼명 표준화
    - 숫자형 변환
    - 오래된 순 -> 최신 순 정렬
    """
    df = df.copy()

    # 컬럼 표준화
    df.columns = [standardize_region_name(col) if col != "년월" else "년월" for col in df.columns]

    expected_cols = ["년월"] + REGION_ORDER
    missing_cols = [col for col in expected_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"필수 컬럼이 없습니다: {missing_cols}")

    df = df[expected_cols].copy()

    # 년월 변환
    df["년월"] = pd.to_datetime(df["년월"].astype(str) + "-01", format="%Y-%m-%d", errors="coerce")

    if df["년월"].isna().any():
        bad_rows = df[df["년월"].isna()]
        raise ValueError(f"년월 변환 실패 행이 있습니다.\n{bad_rows}")

    # 숫자형 변환
    numeric_cols = REGION_ORDER
    for col in numeric_cols:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.strip()
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 숫자 변환 실패 점검
    if df[numeric_cols].isna().any().any():
        null_summary = df[numeric_cols].isna().sum()
        raise ValueError(f"숫자형 변환 실패 컬럼이 있습니다.\n{null_summary[null_summary > 0]}")

    # 오래된 월부터 정렬
    df = df.sort_values("년월").reset_index(drop=True)

    # 연/월 파생컬럼
    df["year_num"] = df["년월"].dt.year
    df["month_num"] = df["년월"].dt.month

    # 합계 검증: 지역합과 합계 컬럼이 일치하는지 확인
    region_cols_without_total = [c for c in REGION_ORDER if c != "합계"]
    df["calc_sum"] = df[region_cols_without_total].sum(axis=1)
    df["sum_match_yn"] = (df["calc_sum"] == df["합계"]).map({True: "Y", False: "N"})

    mismatch_count = (df["sum_match_yn"] == "N").sum()
    if mismatch_count > 0:
        print(f"[경고] 합계 불일치 행 수: {mismatch_count}")

    return df


def convert_wide_to_long(df_wide: pd.DataFrame) -> pd.DataFrame:
    """
    wide -> long 변환 후
    월별 순증(monthly_increase), 전년동월 대비 증가(yoy_diff), 점유율(share_pct) 생성
    """
    id_vars = ["년월", "year_num", "month_num"]
    value_vars = REGION_ORDER

    df_long = df_wide.melt(
        id_vars=id_vars,
        value_vars=value_vars,
        var_name="region_name",
        value_name="cumulative_count"
    )

    # 지역 정렬 기준
    region_order_map = {region: idx + 1 for idx, region in enumerate(REGION_ORDER)}
    df_long["region_order"] = df_long["region_name"].map(region_order_map)

    df_long = df_long.sort_values(["region_name", "년월"]).reset_index(drop=True)

    # 월별 순증
    df_long["monthly_increase"] = (
        df_long.groupby("region_name")["cumulative_count"].diff()
    )

    # 첫 행은 누적값 자체로 처리 (실무상 첫 관측치)
    df_long["monthly_increase"] = df_long["monthly_increase"].fillna(df_long["cumulative_count"])

    # 전년 동월 대비 증가
    df_long["yoy_diff"] = (
        df_long.groupby("region_name")["cumulative_count"].diff(12)
    )

    # 전국 합계와 연결해서 점유율 계산
    total_df = df_long[df_long["region_name"] == "합계"][["년월", "cumulative_count"]].copy()
    total_df = total_df.rename(columns={"cumulative_count": "total_cumulative_count"})

    df_long = df_long.merge(total_df, on="년월", how="left")

    df_long["share_pct"] = (
        df_long["cumulative_count"] / df_long["total_cumulative_count"] * 100
    ).round(4)

    # 합계 행은 점유율 100%
    df_long.loc[df_long["region_name"] == "합계", "share_pct"] = 100.0

    # 연도별 순증 계산 편의용 플래그
    latest_ym = df_long["년월"].max()
    df_long["is_latest_ym"] = (df_long["년월"] == latest_ym).map({True: "Y", False: "N"})

    return df_long


def save_processed_files(df_wide: pd.DataFrame, df_long: pd.DataFrame):
    OUTPUT_WIDE_FILE.parent.mkdir(parents=True, exist_ok=True)

    df_wide.to_csv(OUTPUT_WIDE_FILE, index=False, encoding="utf-8-sig")
    df_long.to_csv(OUTPUT_LONG_FILE, index=False, encoding="utf-8-sig")

    print(f"[완료] wide 저장: {OUTPUT_WIDE_FILE}")
    print(f"[완료] long 저장: {OUTPUT_LONG_FILE}")


def run():
    ensure_directories()

    print(f"[시작] 원본 파일 읽기: {INPUT_FILE}")
    df_raw = read_raw_excel(INPUT_FILE)

    print("[진행] wide 정제")
    df_wide = clean_wide_dataframe(df_raw)

    print("[진행] long 변환 및 파생컬럼 생성")
    df_long = convert_wide_to_long(df_wide)

    print("[진행] CSV 저장")
    save_processed_files(df_wide, df_long)

    print("\n[샘플] wide 상위 5행")
    print(df_wide.head())

    print("\n[샘플] long 상위 10행")
    print(df_long.head(10))

    print("\n[요약]")
    print(f"wide shape: {df_wide.shape}")
    print(f"long shape: {df_long.shape}")
    print(f"기간: {df_wide['년월'].min().date()} ~ {df_wide['년월'].max().date()}")


if __name__ == "__main__":
    run()