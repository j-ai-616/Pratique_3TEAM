from pathlib import Path
import pandas as pd
import re


# --------------------------------------------------
# 경로 설정
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[2]

RAW_DIR = BASE_DIR / "data" / "raw" / "charger"
PROCESSED_DIR = BASE_DIR / "data" / "processed" / "charger"

KEPCO_FILE = RAW_DIR / "한국전력공사_충전소의 위치 및 현황 정보_20250630.csv"
ECO_FILE = RAW_DIR / "한국환경공단_전기차 충전소 위치 및 운영정보_20221027.csv"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# 공통 유틸
# --------------------------------------------------
def read_csv_flexible(file_path: Path) -> pd.DataFrame:
    """
    cp949, euc-kr, utf-8-sig 순서로 읽기 시도
    """
    encodings = ["cp949", "euc-kr", "utf-8-sig", "utf-8"]
    last_error = None

    for enc in encodings:
        try:
            return pd.read_csv(file_path, encoding=enc)
        except Exception as e:
            last_error = e

    raise ValueError(f"파일을 읽을 수 없습니다: {file_path}\n{last_error}")


def clean_text(value):
    """
    문자열 공백/개행/NaN 정리
    """
    if pd.isna(value):
        return None
    value = str(value).strip()
    value = re.sub(r"\s+", " ", value)
    if value == "" or value.lower() == "nan":
        return None
    return value


def normalize_station_name(name):
    """
    충전소명 비교용 정규화
    """
    name = clean_text(name)
    if not name:
        return None
    name = re.sub(r"[^\w가-힣]", "", name)
    return name.lower()


def normalize_address(addr):
    """
    주소 비교용 정규화
    """
    addr = clean_text(addr)
    if not addr:
        return None
    addr = addr.replace("특별시", "").replace("광역시", "").replace("특별자치시", "").replace("특별자치도", "")
    addr = re.sub(r"\s+", " ", addr)
    addr = addr.strip()
    return addr.lower()


def standardize_operator(name):
    """
    운영기관명 통일
    """
    name = clean_text(name)
    if not name:
        return None

    replace_map = {
        "환경부": "환경부",
        "한국환경공단": "한국환경공단",
        "한국전력": "한국전력공사",
        "한국전력공사": "한국전력공사",
        "KEPCO": "한국전력공사",
        "에버온": "에버온",
        "차지비": "차지비",
        "한국자동차환경협회": "한국자동차환경협회",
    }

    for key, val in replace_map.items():
        if key in name:
            return val

    return name


def classify_charge_type(value):
    """
    급속/완속/기타 분류
    """
    value = clean_text(value)
    if not value:
        return "미상"

    value_lower = value.lower()

    rapid_keywords = ["급속", "dc", "콤보", "차데모", "chademo", "combo", "dc콤보"]
    slow_keywords = ["완속", "ac", "ac3", "ac완속"]

    if any(k in value_lower for k in rapid_keywords):
        return "급속"
    if any(k in value_lower for k in slow_keywords):
        return "완속"

    return "기타"


def map_status(value):
    """
    상태/이용제한 관련 텍스트 정리
    """
    value = clean_text(value)
    if not value:
        return "정보없음"

    if "이용가능" in value or "사용가능" in value or value == "Y":
        return "이용가능"
    if "점검" in value or "고장" in value or "수리" in value:
        return "점검/고장"
    if "이용자제한" in value or "제한" in value or value == "N":
        return "이용제한"

    return value


def extract_region_from_address(address):
    """
    주소에서 시도명 추출
    """
    address = clean_text(address)
    if not address:
        return None

    region_map = {
        "서울": "서울특별시",
        "부산": "부산광역시",
        "대구": "대구광역시",
        "인천": "인천광역시",
        "광주": "광주광역시",
        "대전": "대전광역시",
        "울산": "울산광역시",
        "세종": "세종특별자치시",
        "경기": "경기도",
        "강원": "강원특별자치도",
        "충북": "충청북도",
        "충남": "충청남도",
        "전북": "전북특별자치도",
        "전남": "전라남도",
        "경북": "경상북도",
        "경남": "경상남도",
        "제주": "제주특별자치도",
    }

    first_token = address.split()[0]
    for key, val in region_map.items():
        if first_token.startswith(key):
            return val

    return None


# --------------------------------------------------
# 전처리 함수
# --------------------------------------------------
def preprocess_kepco(df: pd.DataFrame) -> pd.DataFrame:
    """
    한국전력공사 CSV 전처리
    """
    df = df.copy()

    rename_map = {
        "충전소아이디": "station_source_id",
        "충전소명": "station_name",
        "충전소주소": "address",
        "상세주소": "address_detail",
        "위도": "latitude",
        "경도": "longitude",
        "이용가능시간": "available_time",
        "연락처": "phone",
        "등록일자": "registered_at",
    }
    df = df.rename(columns=rename_map)

    needed_cols = list(rename_map.values())
    df = df[[c for c in needed_cols if c in df.columns]].copy()

    # 문자열 정리
    text_cols = ["station_source_id", "station_name", "address", "address_detail", "available_time", "phone"]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].apply(clean_text)

    # 숫자형 변환
    if "latitude" in df.columns:
        df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    if "longitude" in df.columns:
        df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    # 날짜형 변환
    if "registered_at" in df.columns:
        df["registered_at"] = pd.to_datetime(df["registered_at"], errors="coerce")

    # 지역명 생성
    df["region_name"] = df["address"].apply(extract_region_from_address)

    # 정규화 컬럼
    df["station_name_norm"] = df["station_name"].apply(normalize_station_name)
    df["address_norm"] = df["address"].apply(normalize_address)

    return df


def preprocess_eco(df: pd.DataFrame) -> pd.DataFrame:
    """
    한국환경공단 CSV 전처리
    """
    df = df.copy()

    rename_map = {
        "시도": "sido",
        "군구": "gungu",
        "주소": "address",
        "충전소명": "station_name",
        "기종(대)": "charger_type_major",
        "기종(소)": "charger_type_minor",
        "운영기관(대)": "operator_major",
        "운영기관(소)": "operator_minor",
        "이용자제한": "raw_status",
        "충전기ID": "charger_source_id",
    }
    df = df.rename(columns=rename_map)

    needed_cols = list(rename_map.values())
    df = df[[c for c in needed_cols if c in df.columns]].copy()

    # 문자열 정리
    for col in df.columns:
        df[col] = df[col].apply(clean_text)

    # 운영기관 통합
    df["operator_name"] = df["operator_minor"].fillna(df["operator_major"])
    df["operator_name"] = df["operator_name"].apply(standardize_operator)

    # 충전방식 통합
    df["charge_type_raw"] = df["charger_type_minor"].fillna(df["charger_type_major"])
    df["charge_type"] = df["charge_type_raw"].apply(classify_charge_type)

    # 상태 해석
    df["status_name"] = df["raw_status"].apply(map_status)

    # 지역명 표준화
    df["region_name"] = df["sido"].apply(clean_text)

    # 주소에서 보정
    df["region_name"] = df["region_name"].fillna(df["address"].apply(extract_region_from_address))

    # 정규화 컬럼
    df["station_name_norm"] = df["station_name"].apply(normalize_station_name)
    df["address_norm"] = df["address"].apply(normalize_address)

    return df


def merge_charger_data(kepco_df: pd.DataFrame, eco_df: pd.DataFrame) -> pd.DataFrame:
    """
    1차: station_name_norm + address_norm
    2차: address_norm 만으로 보조 매칭
    """
    # 1차 병합
    merged = pd.merge(
        kepco_df,
        eco_df,
        on=["station_name_norm", "address_norm"],
        how="left",
        suffixes=("_kepco", "_eco")
    )

    # 주소/충전소명 표시 컬럼 정리
    merged["station_name"] = merged["station_name_kepco"].fillna(merged["station_name_eco"])
    merged["address"] = merged["address_kepco"].fillna(merged["address_eco"])
    merged["region_name"] = merged["region_name_kepco"].fillna(merged["region_name_eco"])

    # 보조 주소 매칭용
    no_match_mask = merged["charger_source_id"].isna()

    if no_match_mask.any():
        fallback_base = kepco_df[["station_source_id", "station_name", "address", "address_norm"]].copy()
        fallback_target = eco_df[
            ["address_norm", "charge_type", "status_name", "operator_name", "charger_source_id"]
        ].drop_duplicates(subset=["address_norm", "charger_source_id"])

        fallback_merged = pd.merge(
            fallback_base,
            fallback_target,
            on="address_norm",
            how="left"
        )

        fallback_merged = fallback_merged.groupby(
            ["station_source_id", "station_name", "address", "address_norm"],
            as_index=False
        ).first()

        merged = pd.merge(
            merged,
            fallback_merged[
                ["station_source_id", "charge_type", "status_name", "operator_name", "charger_source_id"]
            ],
            on="station_source_id",
            how="left",
            suffixes=("", "_fallback")
        )

        merged["charge_type"] = merged["charge_type"].fillna(merged["charge_type_fallback"])
        merged["status_name"] = merged["status_name"].fillna(merged["status_name_fallback"])
        merged["operator_name"] = merged["operator_name"].fillna(merged["operator_name_fallback"])
        merged["charger_source_id"] = merged["charger_source_id"].fillna(merged["charger_source_id_fallback"])

        drop_cols = [
            "charge_type_fallback",
            "status_name_fallback",
            "operator_name_fallback",
            "charger_source_id_fallback",
        ]
        merged = merged.drop(columns=[c for c in drop_cols if c in merged.columns])

    # 최종 컬럼 선택
    final_cols = [
        "station_source_id",
        "charger_source_id",
        "station_name",
        "address",
        "address_detail",
        "region_name",
        "latitude",
        "longitude",
        "charge_type",
        "status_name",
        "operator_name",
        "available_time",
        "phone",
        "registered_at",
    ]
    final_cols = [c for c in final_cols if c in merged.columns]
    merged = merged[final_cols].copy()

    return merged


def remove_duplicates(merged_df: pd.DataFrame) -> pd.DataFrame:
    """
    중복 제거
    우선순위:
    1. 충전기ID + 충전소명 + 주소
    2. 충전소명 + 주소 + 충전방식
    """
    df = merged_df.copy()

    # 완전중복 제거
    df = df.drop_duplicates()

    # 핵심 중복 제거
    if "charger_source_id" in df.columns:
        df = df.sort_values(by=["station_name", "address"])
        df = df.drop_duplicates(
            subset=["charger_source_id", "station_name", "address"],
            keep="first"
        )

    df = df.drop_duplicates(
        subset=["station_name", "address", "charge_type"],
        keep="first"
    )

    return df


def build_station_table(merged_df: pd.DataFrame) -> pd.DataFrame:
    """
    충전소(station) 단위 테이블 생성
    """
    station_cols = [
        "station_source_id",
        "station_name",
        "address",
        "address_detail",
        "region_name",
        "latitude",
        "longitude",
        "operator_name",
        "available_time",
        "phone",
        "registered_at",
    ]
    station_cols = [c for c in station_cols if c in merged_df.columns]

    station_df = merged_df[station_cols].copy()
    station_df = station_df.drop_duplicates(subset=["station_name", "address"], keep="first")

    return station_df


def build_charger_table(merged_df: pd.DataFrame) -> pd.DataFrame:
    """
    충전기(charger) 단위 테이블 생성
    """
    charger_cols = [
        "station_source_id",
        "charger_source_id",
        "station_name",
        "address",
        "charge_type",
        "status_name",
        "operator_name",
    ]
    charger_cols = [c for c in charger_cols if c in merged_df.columns]

    charger_df = merged_df[charger_cols].copy()

    if "charger_source_id" in charger_df.columns:
        charger_df = charger_df.drop_duplicates(
            subset=["charger_source_id", "station_name", "address"],
            keep="first"
        )
    else:
        charger_df = charger_df.drop_duplicates()

    return charger_df


# --------------------------------------------------
# 실행 함수
# --------------------------------------------------
def run():
    print("충전소 원본 파일 읽는 중...")

    kepco_raw = read_csv_flexible(KEPCO_FILE)
    eco_raw = read_csv_flexible(ECO_FILE)

    print(f"한전 원본 shape: {kepco_raw.shape}")
    print(f"환경공단 원본 shape: {eco_raw.shape}")

    print("한전 데이터 전처리 중...")
    kepco_clean = preprocess_kepco(kepco_raw)

    print("환경공단 데이터 전처리 중...")
    eco_clean = preprocess_eco(eco_raw)

    print("데이터 병합 중...")
    merged = merge_charger_data(kepco_clean, eco_clean)

    print("중복 제거 중...")
    merged = remove_duplicates(merged)

    print("충전소/충전기 테이블 생성 중...")
    station_df = build_station_table(merged)
    charger_df = build_charger_table(merged)

    # 저장
    merged.to_csv(PROCESSED_DIR / "charger_merged.csv", index=False, encoding="utf-8-sig")
    station_df.to_csv(PROCESSED_DIR / "charger_station.csv", index=False, encoding="utf-8-sig")
    charger_df.to_csv(PROCESSED_DIR / "charger_charger.csv", index=False, encoding="utf-8-sig")

    print("저장 완료")
    print(f"merged shape: {merged.shape}")
    print(f"station shape: {station_df.shape}")
    print(f"charger shape: {charger_df.shape}")

    print("\n결측치 확인")
    check_cols = ["latitude", "longitude", "address", "station_name", "region_name"]
    existing_check_cols = [c for c in check_cols if c in merged.columns]
    print(merged[existing_check_cols].isna().sum())

    return merged, station_df, charger_df


if __name__ == "__main__":
    run()