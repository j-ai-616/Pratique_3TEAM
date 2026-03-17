from __future__ import annotations

# 이 스크립트는 전기차 정보 포털 프로젝트에서 사용하는
# "공통 데이터 로딩 허브" 역할을 담당합니다.
#
# 이 스크립트의 핵심 역할은 다음과 같습니다.
#
# 1) 파일 탐색 및 공통 변환 유틸 제공
#    - CSV / Excel 파일을 여러 후보 이름과 경로에서 찾아 읽어옵니다.
#    - 컬럼명 표준화, 날짜형 변환, 숫자형 변환 같은 공통 전처리 기능을 제공합니다.
#
# 2) 각 메뉴별 데이터 로드 함수 제공
#    - 지역별 전기차 등록 현황 데이터
#    - 충전소 운영 정보 데이터
#    - 충전 요금 데이터
#    - 보조금 정책 데이터
#    - 서울시 FAQ 데이터
#    - 뉴스 키워드 분석 데이터
#    - 제조사별 FAQ 데이터
#    를 각각 표준화된 pandas DataFrame 형태로 반환합니다.
#
# 3) 파일이 없을 때 fallback 샘플 데이터 제공
#    - 실제 파일이 없거나 읽지 못하는 경우에도
#      화면이 완전히 깨지지 않도록 기본 예시 데이터를 생성해 반환합니다.
#
# 이 스크립트는 직접 Streamlit 화면을 그리지는 않습니다.
# 대신 다른 화면 스크립트들이 공통으로 사용할 데이터를 준비해 주는
# "데이터 준비/전처리 전담 스크립트"입니다.
#
# 이 스크립트와 상호작용하는 주요 스크립트는 다음과 같습니다.
#
# 1) src/app/main_app.py
#    - 가장 직접적으로 연결되는 스크립트입니다.
#    - main_app.py의 load_dashboard_data()에서
#      load_ev_registration_data(), load_charger_operation_data(),
#      load_charging_fee_data(), load_policy_data(), load_faq_data(),
#      load_news_keyword_data(), load_brand_faq_data()를 호출해
#      각 메뉴용 데이터를 한 번에 준비합니다.
#
# 2) src/data/region_ev_section.py
#    - 지역별 전기차 등록 현황 화면을 구성하는 스크립트입니다.
#    - load_ev_registration_data() 결과를 사용할 수 있습니다.
#    - 다만 프로젝트 현재 구조상 1번 탭은 DB 기반 화면을 직접 사용하는 버전도 함께 존재합니다.
#
# 3) src/data/charger_section.py
#    - 충전소 운영 정보 화면을 구성하는 스크립트입니다.
#    - load_charger_operation_data() 결과를 받아
#      필터링, 지도 표시, 운영 정보 테이블 화면을 구성합니다.
#
# 4) src/data/charging_fee_section.py
#    - 충전 요금 화면을 구성하는 스크립트입니다.
#    - load_charging_fee_data() 결과를 받아
#      요금 기준표와 예상 충전 비용 계산기를 출력합니다.
#
# 5) src/data/subsidy_section.py
#    - 보조금 정책 화면을 구성하는 스크립트입니다.
#    - load_policy_data() 결과를 받아
#      차량 유형/구분/제조사/차종별 보조금 정보를 표시합니다.
#
# 6) src/data/faq_section.py
#    - 서울시 전기차 FAQ 화면을 구성하는 스크립트입니다.
#    - load_faq_data() 결과를 받아
#      FAQ 구분/카테고리/검색 기반 화면을 구성합니다.
#
# 7) src/data/brand_faq_section.py
#    - 제조사별 FAQ 화면을 구성하는 스크립트입니다.
#    - load_brand_faq_data() 결과를 받아
#      브랜드 탭 기반 FAQ 화면을 구성합니다.
#
# 8) src/data/news_analysis_section.py
#    - 뉴스 기사 분석 화면을 구성하는 스크립트입니다.
#    - load_news_keyword_data() 결과와 resolve_news_wordcloud_path() 결과를 받아
#      키워드 빈도표, 막대그래프, 워드클라우드를 출력합니다.
#
# 전체 흐름을 간단히 정리하면 다음과 같습니다.
#
# raw / processed / webcrawling 폴더의 파일들
#   -> 현재 스크립트(query_data.py)
#      - 파일 탐색
#      - 컬럼 표준화
#      - 날짜/숫자 변환
#      - fallback 데이터 보완
#   -> main_app.py
#   -> 각 section 스크립트
#   -> 최종 Streamlit 화면 출력
#
# 정리하면,
# 이 스크립트는 프로젝트 전체의 여러 메뉴가 공통으로 의존하는
# "데이터 로딩 + 표준화 + fallback 처리 중심의 핵심 백엔드 유틸 스크립트"입니다.

from pathlib import Path
from typing import Iterable

import pandas as pd

# 현재 파일(query_data.py)의 위치를 기준으로 프로젝트 루트 경로를 계산합니다.
# 예: src/db/query_data.py 기준으로 두 단계 위를 프로젝트 루트로 간주합니다.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 원본(raw) 데이터 폴더 경로입니다.
RAW_DIR = PROJECT_ROOT / 'data' / 'raw'

# 전처리된(processed) 데이터 폴더 경로입니다.
PROCESSED_DIR = PROJECT_ROOT / 'data' / 'processed'


def _load_first_existing_csv(file_names: Iterable[str]) -> pd.DataFrame | None:
    # 전달받은 CSV 파일 이름 후보 목록을 순서대로 확인합니다.
    for file_name in file_names:
        # processed 폴더 아래에 해당 CSV 파일이 있는지 경로를 만듭니다.
        csv_path = PROCESSED_DIR / file_name

        # 파일이 실제로 존재하면 바로 pandas로 읽어서 반환합니다.
        if csv_path.exists():
            return pd.read_csv(csv_path)

    # 어떤 후보 파일도 찾지 못하면 None을 반환합니다.
    return None


def _load_first_existing_excel(
    file_names: Iterable[str],
    sheet_name: str | int | None = 0,
) -> pd.DataFrame | None:
    # 전달받은 엑셀 파일 이름 후보 목록을 순서대로 확인합니다.
    for file_name in file_names:
        # raw 폴더와 processed 폴더를 순회하면서 해당 파일이 있는지 찾습니다.
        for base_dir in (RAW_DIR, PROCESSED_DIR):
            excel_path = base_dir / file_name

            # 파일이 존재하면 읽기를 시도합니다.
            if excel_path.exists():
                try:
                    # 지정한 sheet_name으로 읽기를 시도합니다.
                    return pd.read_excel(excel_path, sheet_name=sheet_name)
                except ValueError:
                    # 지정 sheet_name이 없거나 읽기 실패 시 기본 시트로 다시 시도합니다.
                    return pd.read_excel(excel_path)

    # 어떤 후보 파일도 찾지 못하면 None을 반환합니다.
    return None


def _find_first_existing_path(file_names: Iterable[str], search_dirs: Iterable[Path]) -> Path | None:
    # 전달받은 탐색 디렉터리 목록을 순서대로 순회합니다.
    for search_dir in search_dirs:
        # 탐색 디렉터리가 실제로 없으면 건너뜁니다.
        if not search_dir.exists():
            continue

        # 각 디렉터리 안에서 파일 이름 후보들을 순서대로 확인합니다.
        for file_name in file_names:
            # 직접 search_dir / file_name 경로를 먼저 확인합니다.
            direct_path = search_dir / file_name
            if direct_path.exists():
                return direct_path

            # 직접 경로에 없으면 하위 폴더까지 재귀적으로 탐색합니다.
            matched_paths = list(search_dir.rglob(file_name))
            if matched_paths:
                return matched_paths[0]

    # 어떤 경로에서도 파일을 찾지 못하면 None을 반환합니다.
    return None


def _standardize_columns(dataframe: pd.DataFrame, rename_map: dict[str, str]) -> pd.DataFrame:
    # 실제 DataFrame 안에 존재하는 컬럼만 대상으로 rename_map을 다시 구성합니다.
    available_rename_map = {
        original_column: new_column
        for original_column, new_column in rename_map.items()
        if original_column in dataframe.columns
    }

    # 바꿀 수 있는 컬럼이 하나도 없으면 원본 DataFrame을 그대로 반환합니다.
    if not available_rename_map:
        return dataframe

    # 존재하는 컬럼만 선택적으로 이름을 변경해 반환합니다.
    return dataframe.rename(columns=available_rename_map)


def _to_datetime(dataframe: pd.DataFrame, column_names: Iterable[str]) -> pd.DataFrame:
    # 전달받은 컬럼 목록을 순회합니다.
    for column_name in column_names:
        # 해당 컬럼이 실제 DataFrame에 존재할 때만 날짜형 변환을 수행합니다.
        if column_name in dataframe.columns:
            dataframe[column_name] = pd.to_datetime(dataframe[column_name], errors='coerce')

    # 변환된 DataFrame을 반환합니다.
    return dataframe


def _to_numeric(dataframe: pd.DataFrame, column_names: Iterable[str]) -> pd.DataFrame:
    # 전달받은 컬럼 목록을 순회합니다.
    for column_name in column_names:
        # 해당 컬럼이 실제 DataFrame에 존재할 때만 숫자형 변환을 수행합니다.
        if column_name in dataframe.columns:
            dataframe[column_name] = pd.to_numeric(dataframe[column_name], errors='coerce')

    # 변환된 DataFrame을 반환합니다.
    return dataframe


# -------------------------------------------------
# 1. 지역 별 전기차 등록 현황 데이터
# -------------------------------------------------

def load_ev_registration_data() -> pd.DataFrame:
    # 후보 CSV 파일 이름들 중 실제 존재하는 첫 번째 파일을 읽어옵니다.
    ev_registration_data = _load_first_existing_csv(
        [
            'ev_registration_data.csv',
            'ev_registrations.csv',
            'region_ev_registration.csv',
        ]
    )

    # 파일을 찾지 못하면 fallback 예시 데이터를 직접 생성합니다.
    if ev_registration_data is None:
        ev_registration_data = pd.DataFrame(
            [
                ['2025-10', '서울', 180000],
                ['2025-10', '경기', 220000],
                ['2025-10', '인천', 52000],
                ['2025-10', '부산', 48000],
                ['2025-10', '대구', 41000],
                ['2025-11', '서울', 182500],
                ['2025-11', '경기', 223500],
                ['2025-11', '인천', 53100],
                ['2025-11', '부산', 49100],
                ['2025-11', '대구', 42050],
                ['2025-12', '서울', 185200],
                ['2025-12', '경기', 227000],
                ['2025-12', '인천', 54500],
                ['2025-12', '부산', 50200],
                ['2025-12', '대구', 43100],
            ],
            columns=['year_month', 'region', 'ev_count'],
        )

    # 한글/대체 컬럼명을 프로젝트 표준 컬럼명으로 바꿉니다.
    ev_registration_data = _standardize_columns(
        ev_registration_data,
        {
            '기준월': 'year_month',
            '연월': 'year_month',
            '시도': 'region',
            '지역': 'region',
            '등록대수': 'ev_count',
            '전기차등록대수': 'ev_count',
        },
    )

    # 날짜형, 숫자형으로 변환합니다.
    ev_registration_data = _to_datetime(ev_registration_data, ['year_month'])
    ev_registration_data = _to_numeric(ev_registration_data, ['ev_count'])

    # 반드시 존재해야 하는 최소 컬럼 목록입니다.
    required_columns = ['year_month', 'region', 'ev_count']

    # 누락된 필수 컬럼이 있으면 Na 값으로 새로 생성합니다.
    for required_column in required_columns:
        if required_column not in ev_registration_data.columns:
            ev_registration_data[required_column] = pd.NA

    # 필요한 컬럼만 남기고, region이 비어 있는 행은 제거합니다.
    ev_registration_data = ev_registration_data[required_columns].dropna(subset=['region'])

    # ev_count가 비어 있는 경우 0으로 채웁니다.
    ev_registration_data['ev_count'] = ev_registration_data['ev_count'].fillna(0)

    # 기준월, 지역 기준으로 정렬한 뒤 반환합니다.
    return ev_registration_data.sort_values(['year_month', 'region']).reset_index(drop=True)


# -------------------------------------------------
# 2. 충전소 위치 / 충전 가능 여부 / 운영 정보
# -------------------------------------------------

def load_charger_operation_data() -> pd.DataFrame:
    # 후보 CSV 파일 이름들 중 실제 존재하는 첫 번째 파일을 읽어옵니다.
    charger_operation_data = _load_first_existing_csv(
        [
            'charger_operation_data.csv',
            'charger_locations.csv',
            'charger_status_data.csv',
        ]
    )

    # 파일을 찾지 못하면 fallback 예시 데이터를 직접 생성합니다.
    if charger_operation_data is None:
        charger_operation_data = pd.DataFrame(
            [
                ['서울', '서울시청 급속충전소', '급속', '환경부', '서울 중구 세종대로 110', 37.5662952, 126.9779451, 2, 3, '운영중', '24시간', '02-120', '서울특별시청 부설주차장'],
                ['서울', '강남 공영주차장 충전소', '완속', '한국전력', '서울 강남구 테헤란로 152', 37.5006220, 127.0364560, 8, 10, '운영중', '24시간', '1544-4279', '강남역 인근 공영주차장'],
                ['경기', '수원시청 충전소', '급속', '환경부', '경기 수원시 팔달구 효원로 241', 37.2635727, 127.0286009, 1, 2, '점검중', '09:00-18:00', '031-228-2114', '수원시청 방문객 주차장'],
                ['경기', '판교역 환승주차장 충전소', '초급속', 'E-pit', '경기 성남시 분당구 판교역로 160', 37.3947610, 127.1111600, 4, 4, '운영중', '24시간', '080-000-0123', '판교역 환승센터'],
                ['인천', '송도 컨벤시아 충전소', '급속', '한국전력', '인천 연수구 센트럴로 123', 37.3876110, 126.6432130, 0, 2, '혼잡', '24시간', '032-000-1111', '송도 컨벤시아 야외주차장'],
                ['부산', '벡스코 야외주차장 충전소', '완속', '부산환경공단', '부산 해운대구 APEC로 55', 35.1699080, 129.1368210, 6, 8, '운영중', '06:00-23:00', '051-000-2222', '벡스코 제1전시장'],
                ['대구', '동대구역 충전소', '급속', '환경부', '대구 동구 동대구로 550', 35.8779490, 128.6285820, 2, 2, '운영중', '24시간', '053-000-3333', '동대구역 환승센터'],
            ],
            columns=[
                'region',
                'charger_name',
                'charger_type',
                'operator',
                'address',
                'latitude',
                'longitude',
                'available_count',
                'total_count',
                'status',
                'operating_hours',
                'phone',
                'road_address',
            ],
        )

    # 다양한 원본 컬럼명을 프로젝트 표준 컬럼명으로 맞춥니다.
    charger_operation_data = _standardize_columns(
        charger_operation_data,
        {
            '지역': 'region',
            '충전소명': 'charger_name',
            '충전기유형': 'charger_type',
            '유형': 'charger_type',
            '운영사': 'operator',
            '주소': 'address',
            '위도': 'latitude',
            '경도': 'longitude',
            '사용가능수': 'available_count',
            '전체수': 'total_count',
            '운영상태': 'status',
            '운영시간': 'operating_hours',
            '도로명주소': 'road_address',
            '전화번호': 'phone',
        },
    )

    # 위도, 경도, 사용 가능 수, 전체 수 컬럼을 숫자형으로 변환합니다.
    charger_operation_data = _to_numeric(
        charger_operation_data,
        ['latitude', 'longitude', 'available_count', 'total_count'],
    )

    # 화면에서 사용될 필수 컬럼 목록입니다.
    required_columns = [
        'region',
        'charger_name',
        'charger_type',
        'operator',
        'address',
        'latitude',
        'longitude',
        'available_count',
        'total_count',
        'status',
        'operating_hours',
        'phone',
        'road_address',
    ]

    # 누락된 필수 컬럼이 있으면 Na 값으로 생성합니다.
    for required_column in required_columns:
        if required_column not in charger_operation_data.columns:
            charger_operation_data[required_column] = pd.NA

    # 필요한 컬럼만 남기고 인덱스를 초기화하여 반환합니다.
    return charger_operation_data[required_columns].reset_index(drop=True)


# -------------------------------------------------
# 3. 충전 요금 관련 데이터
# -------------------------------------------------

def _read_excel_with_fallback(excel_path: Path, **kwargs) -> pd.DataFrame:
    # 여러 엔진(auto, xlrd, openpyxl)을 순차적으로 시도하기 위해 에러 로그를 저장할 리스트입니다.
    read_errors: list[str] = []

    # 엔진을 바꿔 가며 읽기를 시도합니다.
    for engine in (None, 'xlrd', 'openpyxl'):
        try:
            # engine=None이면 pandas 기본 엔진 선택에 맡깁니다.
            if engine is None:
                return pd.read_excel(excel_path, **kwargs)

            # engine이 지정된 경우 해당 엔진으로 읽습니다.
            return pd.read_excel(excel_path, engine=engine, **kwargs)
        except Exception as exc:  # noqa: BLE001
            # 실패한 경우 에러 내용을 저장하고 다음 엔진을 시도합니다.
            read_errors.append(f'{engine or "auto"}: {exc}')

    # 모든 엔진으로 읽기 실패 시 상세 에러를 포함한 예외를 발생시킵니다.
    raise RuntimeError(
        f'엑셀 파일을 읽을 수 없습니다. path={excel_path}, errors={" | ".join(read_errors)}'
    )


def _load_charging_fee_excel_dataframe(excel_path: Path) -> pd.DataFrame | None:
    # ExcelFile 객체를 먼저 열어 시트 목록을 확인하려고 시도합니다.
    try:
        workbook = pd.ExcelFile(excel_path)
    except Exception:
        workbook = None

    # 후보 시트명 목록입니다.
    candidate_sheet_names: list[str | int] = []

    # workbook 객체 생성에 성공했다면 실제 시트명들을 후보 목록에 넣습니다.
    if workbook is not None:
        candidate_sheet_names.extend(workbook.sheet_names)

    # 시트 목록을 가져오지 못한 경우 기본적으로 첫 번째 시트(0번)를 사용합니다.
    if not candidate_sheet_names:
        candidate_sheet_names = [0]

    # 후보 시트들을 하나씩 순회하며 읽기를 시도합니다.
    for sheet_name in candidate_sheet_names:
        try:
            # 헤더를 직접 판단하기 위해 header=None으로 원본 형태 그대로 읽습니다.
            raw_fee_data = _read_excel_with_fallback(
                excel_path,
                sheet_name=sheet_name,
                header=None,
            )
        except Exception:
            # 특정 시트 읽기에 실패하면 다음 시트를 시도합니다.
            continue

        # 비어 있는 시트는 건너뜁니다.
        if raw_fee_data is None or raw_fee_data.empty:
            continue

        # 헤더 행의 위치를 찾기 위한 변수입니다.
        header_row_index = None

        # 단일 헤더인지, 2줄 헤더인지 구분하기 위한 모드 변수입니다.
        header_mode = 'single'

        # 앞부분 최대 10행 정도를 검사하여 헤더 행을 찾습니다.
        for row_index in range(min(10, len(raw_fee_data))):
            row_values = raw_fee_data.iloc[row_index].fillna('').astype(str).str.strip()

            # 한 줄 안에 사업자명과 용량구분이 함께 있으면 헤더 후보로 봅니다.
            if '사업자명' in row_values.values and '용량구분' in row_values.values:
                header_row_index = row_index

                # 다음 행에 충전요금 관련 보조 헤더가 있으면 2줄 헤더(double)로 판단합니다.
                if row_index + 1 < len(raw_fee_data):
                    next_row_values = raw_fee_data.iloc[row_index + 1].fillna('').astype(str).str.strip()
                    if next_row_values.str.contains('충전요금', regex=False).any():
                        header_mode = 'double'
                break

            # 한 줄 전체 문자열 기준으로도 헤더 여부를 느슨하게 검사합니다.
            joined_row_text = ' '.join(row_values.tolist())
            if ('사업자명' in joined_row_text or '운영사' in joined_row_text) and (
                '용량구분' in joined_row_text or '충전기유형' in joined_row_text
            ):
                header_row_index = row_index
                break

        # 헤더를 찾지 못하면 다음 시트를 검사합니다.
        if header_row_index is None:
            continue

        # 2줄 헤더인 경우 상단 헤더 + 하단 보조 헤더를 합쳐 최종 컬럼명을 만듭니다.
        if header_mode == 'double':
            upper_header = raw_fee_data.iloc[header_row_index].fillna('').astype(str).str.strip()
            lower_header = raw_fee_data.iloc[header_row_index + 1].fillna('').astype(str).str.strip()

            combined_columns = []
            for upper_value, lower_value in zip(upper_header, lower_header):
                pieces = [value for value in [upper_value, lower_value] if value]
                combined_columns.append(' '.join(pieces).strip())

            # 실제 데이터는 헤더 2줄 아래부터 시작한다고 보고 추출합니다.
            charging_fee_data = raw_fee_data.iloc[header_row_index + 2:].copy()
            charging_fee_data.columns = combined_columns
        else:
            # 단일 헤더인 경우 헤더 다음 줄부터 데이터를 사용합니다.
            charging_fee_data = raw_fee_data.iloc[header_row_index + 1:].copy()
            charging_fee_data.columns = raw_fee_data.iloc[header_row_index].fillna('').astype(str).str.strip().tolist()

        # 인덱스를 초기화하고 첫 번째 성공 결과를 반환합니다.
        charging_fee_data = charging_fee_data.reset_index(drop=True)
        return charging_fee_data

    # 어떤 시트에서도 유효한 데이터를 찾지 못하면 None을 반환합니다.
    return None


def load_charging_fee_data() -> pd.DataFrame:
    # 충전 요금 엑셀 파일 후보들을 여러 폴더에서 탐색합니다.
    charging_fee_excel_path = _find_first_existing_path(
        [
            'charge_fee(2026-03-15).xls',
            'charge_fee(2026-03-15).xlsx',
            'charge_fee.xls',
            'charge_fee.xlsx',
        ],
        [
            RAW_DIR / 'charge_fee',
            RAW_DIR,
            PROCESSED_DIR,
            PROJECT_ROOT / 'data',
            Path.cwd(),
            Path('/mnt/data'),
        ],
    )

    # 최종 로드된 충전 요금 데이터를 담을 변수입니다.
    charging_fee_data = None

    # 엑셀 파일을 찾았다면 구조 분석 기반 읽기를 시도합니다.
    if charging_fee_excel_path is not None and charging_fee_excel_path.exists():
        charging_fee_data = _load_charging_fee_excel_dataframe(charging_fee_excel_path)

    # 엑셀 읽기에 실패했으면 CSV 후보 파일을 시도합니다.
    if charging_fee_data is None:
        charging_fee_data = _load_first_existing_csv(
            [
                'charging_fee_data.csv',
                'charging_fee_reference.csv',
                'fee_reference.csv',
            ]
        )

    # 그래도 데이터가 없으면 fallback 예시 데이터를 생성합니다.
    if charging_fee_data is None:
        charging_fee_data = pd.DataFrame(
            [
                ['환경부', '급속(100kW미만)', '대표', 324.4, 324.4, '시간대/정책에 따라 변동 가능', '2026-03-13'],
                ['환경부', '급속(100kW이상)', '대표', 347.2, 347.2, '시간대/정책에 따라 변동 가능', '2026-03-13'],
                ['E1', '완속', '대표', 301.4, 301.4, '', '2026-03-13'],
                ['GS차지비', '완속', '대표', 319.0, 470.0, '', '2026-03-13'],
                ['GS차지비', '급속(100kW미만)', '대표', 335.0, 470.0, '', '2026-03-13'],
            ],
            columns=[
                'operator',
                'charger_type',
                'fee_type',
                'member_price_per_kwh',
                'non_member_price_per_kwh',
                'note',
                'updated_at',
            ],
        )

    # 컬럼명 안의 줄바꿈 문자를 공백으로 바꾸고 앞뒤 공백을 제거합니다.
    charging_fee_data.columns = [
        str(column).replace('\n', ' ').replace('\r', ' ').strip()
        for column in charging_fee_data.columns
    ]

    # 다양한 컬럼명 패턴을 프로젝트 표준 컬럼명으로 통일합니다.
    charging_fee_data = _standardize_columns(
        charging_fee_data,
        {
            '사업자명': 'operator',
            '운영사': 'operator',
            '운영 기관': 'operator',
            '사업자': 'operator',

            '요금유형': 'fee_type',
            '요금 유형': 'fee_type',

            '용량구분': 'charger_type',
            '충전기유형': 'charger_type',
            '충전기 유형': 'charger_type',
            '충전 유형': 'charger_type',

            '회원가 충전요금(원)': 'member_price_per_kwh',
            '회원가': 'member_price_per_kwh',
            '회원단가': 'member_price_per_kwh',
            '회원 단가': 'member_price_per_kwh',
            '회원단가(원/kWh)': 'member_price_per_kwh',
            '회원 단가(원/kWh)': 'member_price_per_kwh',

            '비회원가 충전요금(원)': 'non_member_price_per_kwh',
            '비회원가': 'non_member_price_per_kwh',
            '비회원단가': 'non_member_price_per_kwh',
            '비회원 단가': 'non_member_price_per_kwh',
            '비회원단가(원/kWh)': 'non_member_price_per_kwh',
            '비회원 단가(원/kWh)': 'non_member_price_per_kwh',

            '기본단가': 'base_price_per_kwh',
            '기본 단가': 'base_price_per_kwh',
            '기본단가(원/kWh)': 'base_price_per_kwh',
            '기본 단가(원/kWh)': 'base_price_per_kwh',

            '비고': 'note',
            '갱신일자': 'updated_at',
            '갱신일': 'updated_at',
        },
    )

    # 단가 관련 컬럼을 숫자형으로 변환합니다.
    charging_fee_data = _to_numeric(
        charging_fee_data,
        ['base_price_per_kwh', 'member_price_per_kwh', 'non_member_price_per_kwh'],
    )

    # base_price_per_kwh 컬럼이 없으면 먼저 생성합니다.
    if 'base_price_per_kwh' not in charging_fee_data.columns:
        charging_fee_data['base_price_per_kwh'] = pd.NA

    # 기본 단가가 비어 있으면 회원가로 대체합니다.
    charging_fee_data['base_price_per_kwh'] = charging_fee_data['base_price_per_kwh'].fillna(
        charging_fee_data.get('member_price_per_kwh')
    )

    # 그래도 비어 있으면 비회원가로 대체합니다.
    charging_fee_data['base_price_per_kwh'] = charging_fee_data['base_price_per_kwh'].fillna(
        charging_fee_data.get('non_member_price_per_kwh')
    )

    # fee_type 컬럼이 없으면 기본값 '대표'를 넣습니다.
    if 'fee_type' not in charging_fee_data.columns:
        charging_fee_data['fee_type'] = '대표'

    # note 컬럼이 없으면 생성합니다.
    if 'note' not in charging_fee_data.columns:
        charging_fee_data['note'] = pd.NA

    # updated_at 컬럼이 없으면 생성합니다.
    if 'updated_at' not in charging_fee_data.columns:
        charging_fee_data['updated_at'] = pd.NA

    # 갱신일자 컬럼을 날짜형으로 변환합니다.
    charging_fee_data = _to_datetime(charging_fee_data, ['updated_at'])

    # 최종적으로 유지할 필수 컬럼 순서입니다.
    required_columns = [
        'operator',
        'charger_type',
        'fee_type',
        'base_price_per_kwh',
        'member_price_per_kwh',
        'non_member_price_per_kwh',
        'note',
        'updated_at',
    ]

    # 누락된 필수 컬럼이 있으면 Na 값으로 생성합니다.
    for required_column in required_columns:
        if required_column not in charging_fee_data.columns:
            charging_fee_data[required_column] = pd.NA

    # 필요한 컬럼만 남깁니다.
    charging_fee_data = charging_fee_data[required_columns].copy()

    # 텍스트 컬럼들의 결측치를 빈 문자열로 바꾸고 문자열 정리를 수행합니다.
    for text_column in ['operator', 'charger_type', 'fee_type', 'note']:
        charging_fee_data[text_column] = (
            charging_fee_data[text_column]
            .fillna('')
            .astype(str)
            .str.strip()
        )

    # charger_type 안의 불필요한 특수기호/중복 공백을 정리합니다.
    charging_fee_data['charger_type'] = (
        charging_fee_data['charger_type']
        .str.replace('①', '', regex=False)
        .str.replace('  ', ' ', regex=False)
        .str.strip()
    )

    # 사업자명, 용량구분이 비어 있지 않고,
    # 단가 3종 중 하나라도 값이 있는 행만 남깁니다.
    charging_fee_data = charging_fee_data[
        (charging_fee_data['operator'] != '')
        & (charging_fee_data['charger_type'] != '')
        & (
            charging_fee_data[['base_price_per_kwh', 'member_price_per_kwh', 'non_member_price_per_kwh']]
            .notna()
            .any(axis=1)
        )
    ].copy()

    # 정렬 후 같은 사업자/용량구분/요금유형 조합이 중복되면 첫 번째 것만 남깁니다.
    charging_fee_data = charging_fee_data.sort_values(
        ['operator', 'charger_type', 'fee_type'],
        na_position='last',
    ).drop_duplicates(
        subset=['operator', 'charger_type', 'fee_type'],
        keep='first',
    ).reset_index(drop=True)

    # 최종 정리된 충전 요금 데이터를 반환합니다.
    return charging_fee_data


# -------------------------------------------------
# 4. 보조금 정책 / FAQ 데이터
# -------------------------------------------------

def load_policy_data() -> pd.DataFrame:
    # 보조금 정책 엑셀 파일 경로입니다.
    subsidy_excel_path = RAW_DIR / 'subsidy' / 'national subsidy.xlsx'

    # 파일이 존재하면 실제 엑셀 기반 로딩을 수행합니다.
    if subsidy_excel_path.exists():
        # 읽을 시트 이름 목록입니다.
        subsidy_sheet_names = [
            '승용 및 초소형 전기자동차(2026년)',
            '전기화물차(2026년)',
            '전기승합차(2026년)',
            '전기이륜차(2026년)',
            '건설기계(2026년)',
            '수소차(2026년)',
        ]

        # 시트별 DataFrame을 담을 리스트입니다.
        subsidy_dataframes = []

        # 각 시트를 순회하며 데이터를 읽습니다.
        for sheet_name in subsidy_sheet_names:
            try:
                sheet_dataframe = pd.read_excel(
                    subsidy_excel_path,
                    sheet_name=sheet_name,
                    engine='openpyxl',
                ).copy()
            except ValueError:
                # 특정 시트가 없으면 건너뜁니다.
                continue

            # 비어 있는 시트는 건너뜁니다.
            if sheet_dataframe.empty:
                continue

            # 어떤 시트에서 왔는지 기록하기 위해 sheet_name 컬럼을 추가합니다.
            sheet_dataframe['sheet_name'] = sheet_name

            # 승용/초소형 시트는 vehicle_class가 없을 수 있어 별도 처리합니다.
            if sheet_name == '승용 및 초소형 전기자동차(2026년)':
                sheet_dataframe = _standardize_columns(
                    sheet_dataframe,
                    {
                        '구분': 'vehicle_group',
                        '제조사': 'manufacturer',
                        '차종': 'model_name',
                        '국고보조금(만원)': 'subsidy_amount',
                    },
                )
                if 'vehicle_class' not in sheet_dataframe.columns:
                    sheet_dataframe['vehicle_class'] = pd.NA

            else:
                # 그 외 시트는 차량분류까지 포함되는 일반 구조로 처리합니다.
                sheet_dataframe = _standardize_columns(
                    sheet_dataframe,
                    {
                        '구분': 'vehicle_group',
                        '차량분류': 'vehicle_class',
                        '제조사': 'manufacturer',
                        '차종': 'model_name',
                        '국고보조금 지원금액(만원)': 'subsidy_amount',
                    },
                )

            # 최종적으로 유지할 필수 컬럼 목록입니다.
            required_columns = [
                'sheet_name',
                'vehicle_group',
                'vehicle_class',
                'manufacturer',
                'model_name',
                'subsidy_amount',
            ]

            # 누락된 컬럼은 Na 값으로 생성합니다.
            for required_column in required_columns:
                if required_column not in sheet_dataframe.columns:
                    sheet_dataframe[required_column] = pd.NA

            # 필요한 컬럼만 남깁니다.
            sheet_dataframe = sheet_dataframe[required_columns].copy()

            # 정상 처리된 시트 DataFrame을 리스트에 추가합니다.
            subsidy_dataframes.append(sheet_dataframe)

        # 하나 이상의 시트를 읽었다면 합쳐서 반환 준비를 합니다.
        if subsidy_dataframes:
            policy_data = pd.concat(subsidy_dataframes, ignore_index=True)
            policy_data = _to_numeric(policy_data, ['subsidy_amount'])

            # 문자열 컬럼 정리를 수행합니다.
            policy_data['sheet_name'] = policy_data['sheet_name'].fillna('').astype(str).str.strip()
            policy_data['vehicle_group'] = policy_data['vehicle_group'].fillna('').astype(str).str.strip()
            policy_data['vehicle_class'] = (
                policy_data['vehicle_class']
                    .fillna('미분류')
                    .astype(str)
                    .str.strip()
                    .replace(['', 'nan', 'None'], '미분류')
                )
            policy_data['manufacturer'] = policy_data['manufacturer'].fillna('').astype(str).str.strip()
            policy_data['model_name'] = policy_data['model_name'].fillna('').astype(str).str.strip()

            # 차종명이 비어 있는 행은 제거합니다.
            policy_data = policy_data[
                policy_data['model_name'] != ''
            ].reset_index(drop=True)

            # 정렬 후 반환합니다.
            return policy_data.sort_values(
                ['sheet_name', 'vehicle_group', 'vehicle_class', 'manufacturer', 'model_name'],
                na_position='last',
            ).reset_index(drop=True)

    # 파일이 없거나 읽기 실패 시 fallback 예시 데이터를 생성합니다.
    policy_data = pd.DataFrame(
        [
            ['승용 및 초소형 전기자동차(2026년)', '승용', pd.NA, '현대자동차', '코나 일렉트릭 2WD 롱레인지 17인치', 514],
            ['전기화물차(2026년)', '화물', '소형', '현대자동차', '포터 Ⅱ 일렉트릭', 968],
            ['전기승합차(2026년)', '승합', '중형', '현대자동차', '카운티일렉트릭', 5000],
            ['전기이륜차(2026년)', '소형', pd.NA, '그린모빌리티', 'GMT-V6', 192],
            ['수소차(2026년)', '수소 승용', pd.NA, '현대자동차', '넥쏘', 2250],
        ],
        columns=[
            'sheet_name',
            'vehicle_group',
            'vehicle_class',
            'manufacturer',
            'model_name',
            'subsidy_amount',
        ],
    )

    # fallback 데이터 반환
    return policy_data.reset_index(drop=True)


def load_faq_data() -> pd.DataFrame:
    # FAQ DataFrame이 실제 FAQ 구조인지 느슨하게 판별하는 내부 함수입니다.
    def _is_valid_faq_dataframe(dataframe: pd.DataFrame | None) -> bool:
        # None이거나 비어 있으면 유효하지 않은 FAQ 데이터로 판단합니다.
        if dataframe is None or dataframe.empty:
            return False

        # FAQ 데이터처럼 보이는 컬럼 집합입니다.
        faq_like_columns = {'구분', '번호', '질문', '질문_원문', '답', '답변', '카테고리', '태그'}

        # FAQ 유사 컬럼이 3개 이상 있고,
        # 질문/답변 계열 컬럼이 각각 하나 이상 있으면 FAQ 구조로 판단합니다.
        return len(set(dataframe.columns) & faq_like_columns) >= 3 and any(
            column in dataframe.columns for column in ['질문', 'question']
        ) and any(
            column in dataframe.columns for column in ['답', '답변', 'answer']
        )

    # 분류 완료된 FAQ 엑셀 파일 경로를 webcrawling 폴더에서 찾습니다.
    categorized_faq_path = _find_first_existing_path(
        ['seoul_ev_faq_categorized.xlsx'],
        [PROJECT_ROOT / 'data' / 'webcrawling'],
    )

    faq_data = None

    # 분류 완료 FAQ 파일이 있으면 우선 이것을 읽습니다.
    if categorized_faq_path is not None and categorized_faq_path.exists():
        for sheet_name in ['faq_categorized', 'faq_original', 0]:
            try:
                loaded_faq_data = pd.read_excel(
                    categorized_faq_path,
                    sheet_name=sheet_name,
                    engine='openpyxl',
                )
            except ValueError:
                continue

            if _is_valid_faq_dataframe(loaded_faq_data):
                faq_data = loaded_faq_data
                break

    # 없으면 legacy raw FAQ 파일을 시도합니다.
    if faq_data is None:
        legacy_faq_path = RAW_DIR / 'faq' / 'seoul_ev_faq.xlsx'
        if legacy_faq_path.exists():
            for sheet_name in ['faq', 0]:
                try:
                    loaded_faq_data = pd.read_excel(
                        legacy_faq_path,
                        sheet_name=sheet_name,
                        engine='openpyxl',
                    )
                except ValueError:
                    continue

                if _is_valid_faq_dataframe(loaded_faq_data):
                    faq_data = loaded_faq_data
                    break

    # 그래도 없으면 CSV 후보를 시도합니다.
    if faq_data is None:
        faq_data = _load_first_existing_csv(
            [
                'faq_data.csv',
                'ev_faq_data.csv',
                'faq.csv',
            ]
        )

    # 최종적으로 데이터가 없으면 fallback 예시 FAQ 데이터를 생성합니다.
    if faq_data is None:
        faq_data = pd.DataFrame(
            [
                ['전기승용,화물,승합 등', '지원대상·차종', '대상', 1, '전기차 지원 가능 차량 및 보조금 확인 방법은?', '무공해차 통합누리집에서 지역별 조회가 가능합니다.'],
                ['전기승용,화물,승합 등', '자격조건·제출서류', '자격', 2, '서울시 보조금 지원 자격 조건은?', '서울 거주 및 사업자 등록 여부 등 공고 기준을 확인해야 합니다.'],
                ['전기이륜', '신청방법·절차', '신청', 3, '전기이륜차 보조금 신청은 어떻게 하나요?', '구매 계약 후 무공해차 통합누리집 또는 지자체 공고 절차에 따라 진행합니다.'],
            ],
            columns=['faq_group', 'category', 'tag', 'faq_number', 'question', 'answer'],
        )

    # 다양한 원본 컬럼명을 프로젝트 표준 컬럼명으로 맞춥니다.
    faq_data = _standardize_columns(
        faq_data,
        {
            '구분': 'faq_group',
            '분류': 'category',
            '카테고리': 'category',
            '태그': 'tag',
            '번호': 'faq_number',
            '질문': 'question',
            '질문_원문': 'question_original',
            '답': 'answer',
            '답변': 'answer',
        },
    )

    # faq_number를 숫자형으로 변환합니다.
    faq_data = _to_numeric(faq_data, ['faq_number'])

    # 유지할 필수 컬럼 목록입니다.
    required_columns = ['faq_group', 'category', 'tag', 'faq_number', 'question', 'question_original', 'answer']

    # 누락된 필수 컬럼은 Na 값으로 생성합니다.
    for required_column in required_columns:
        if required_column not in faq_data.columns:
            faq_data[required_column] = pd.NA

    # 필요한 컬럼만 남깁니다.
    faq_data = faq_data[required_columns].copy()

    # 문자열 컬럼들을 정리합니다.
    faq_data['faq_group'] = faq_data['faq_group'].fillna('기타').astype(str).str.strip()
    faq_data['category'] = faq_data['category'].fillna('기타').astype(str).str.strip()
    faq_data['tag'] = faq_data['tag'].fillna('').astype(str).str.strip()
    faq_data['question'] = faq_data['question'].fillna('').astype(str).str.strip()
    faq_data['question_original'] = faq_data['question_original'].fillna('').astype(str).str.strip()
    faq_data['answer'] = faq_data['answer'].fillna('').astype(str).str.strip()

    # 질문과 답변이 모두 존재하는 FAQ만 남깁니다.
    faq_data = faq_data[
        (faq_data['question'] != '')
        & (faq_data['answer'] != '')
    ].reset_index(drop=True)

    # faq_number가 전부 비어 있으면 1부터 순번을 새로 부여합니다.
    if faq_data['faq_number'].isna().all():
        faq_data['faq_number'] = range(1, len(faq_data) + 1)

    # 정렬 후 반환합니다.
    return faq_data.sort_values(
        ['faq_group', 'category', 'faq_number', 'question'],
        na_position='last',
    ).reset_index(drop=True)


def load_news_keyword_data() -> pd.DataFrame:
    # 뉴스 키워드 빈도 엑셀 파일 경로를 webcrawling 폴더에서 찾습니다.
    keyword_excel_path = _find_first_existing_path(
        ['keyword_frequency.xlsx'],
        [PROJECT_ROOT / 'data' / 'webcrawling'],
    )

    # 파일이 있으면 실제 엑셀을 읽습니다.
    if keyword_excel_path is not None and keyword_excel_path.exists():
        news_keyword_data = pd.read_excel(keyword_excel_path, engine='openpyxl')
    else:
        # 파일이 없으면 fallback 예시 데이터를 생성합니다.
        news_keyword_data = pd.DataFrame(
            [
                ['구매', 28],
                ['시장', 27],
                ['가격', 25],
                ['정책', 23],
                ['차량', 22],
            ],
            columns=['키워드', '빈도수'],
        )

    # 컬럼명을 표준 형태(키워드, 빈도수)로 맞춥니다.
    news_keyword_data = _standardize_columns(
        news_keyword_data,
        {
            'keyword': '키워드',
            'count': '빈도수',
            '빈도': '빈도수',
        },
    )

    # 필수 컬럼이 없으면 생성합니다.
    required_columns = ['키워드', '빈도수']
    for required_column in required_columns:
        if required_column not in news_keyword_data.columns:
            news_keyword_data[required_column] = pd.NA

    # 문자열/숫자형 정리를 수행합니다.
    news_keyword_data['키워드'] = news_keyword_data['키워드'].fillna('').astype(str).str.strip()
    news_keyword_data['빈도수'] = pd.to_numeric(news_keyword_data['빈도수'], errors='coerce').fillna(0)

    # 키워드가 비어 있지 않은 행만 남깁니다.
    news_keyword_data = news_keyword_data[news_keyword_data['키워드'] != ''].copy()

    # 빈도수 내림차순, 키워드 오름차순으로 정렬해 반환합니다.
    return news_keyword_data.sort_values(['빈도수', '키워드'], ascending=[False, True]).reset_index(drop=True)


def resolve_news_wordcloud_path() -> Path | None:
    # 워드클라우드 이미지 파일(wordcloud.png)의 실제 경로를 찾아 반환합니다.
    return _find_first_existing_path(
        ['wordcloud.png'],
        [PROJECT_ROOT / 'data' / 'webcrawling'],
    )

def load_brand_faq_data() -> pd.DataFrame:
    # 제조사별 FAQ 엑셀 파일 경로를 여러 후보 폴더에서 탐색합니다.
    manufacturer_faq_path = _find_first_existing_path(
        ['전기차 FAQ_제조사별.xlsx'],
        [
            RAW_DIR / 'faq',
            RAW_DIR,
            PROCESSED_DIR,
            PROJECT_ROOT / 'data',
            Path.cwd(),
            Path('/mnt/data'),
        ],
    )

    # 파일이 없으면 빈 DataFrame을 반환합니다.
    if manufacturer_faq_path is None or not manufacturer_faq_path.exists():
        return pd.DataFrame(
            columns=[
                'brand',
                'category',
                'faq_number',
                'question',
                'question_original',
                'answer',
            ]
        )

    # 먼저 workbook 객체를 열어 시트 목록을 가져오려고 시도합니다.
    try:
        workbook = pd.ExcelFile(manufacturer_faq_path, engine='openpyxl')
    except Exception:
        workbook = pd.ExcelFile(manufacturer_faq_path)

    # 시트별 FAQ DataFrame을 담을 리스트입니다.
    brand_faq_frames = []

    # 제조사별 FAQ 파일의 모든 시트를 순회합니다.
    for sheet_name in workbook.sheet_names:
        try:
            sheet_df = pd.read_excel(
                manufacturer_faq_path,
                sheet_name=sheet_name,
                engine='openpyxl',
            )
        except Exception:
            # openpyxl 실패 시 pandas 기본 방식으로 다시 시도합니다.
            sheet_df = pd.read_excel(
                manufacturer_faq_path,
                sheet_name=sheet_name,
            )

        # 비어 있는 시트는 건너뜁니다.
        if sheet_df is None or sheet_df.empty:
            continue

        # 시트 내부 컬럼명을 프로젝트 표준 FAQ 컬럼명으로 맞춥니다.
        sheet_df = _standardize_columns(
            sheet_df,
            {
                '번호': 'faq_number',
                '질문 카테고리': 'category',
                '카테고리': 'category',
                '질문': 'question',
                '질문_원문': 'question_original',
                '답': 'answer',
                '답변': 'answer',
            },
        ).copy()

        # 필요한 필수 컬럼 목록입니다.
        required_columns = [
            'faq_number',
            'category',
            'question',
            'question_original',
            'answer',
        ]

        # 누락된 필수 컬럼은 Na 값으로 생성합니다.
        for required_column in required_columns:
            if required_column not in sheet_df.columns:
                sheet_df[required_column] = pd.NA

        # 필요한 컬럼만 남기고, 현재 시트명을 brand 컬럼으로 추가합니다.
        sheet_df = sheet_df[required_columns].copy()
        sheet_df['brand'] = str(sheet_name).strip()

        # 문자열 컬럼 정리 및 faq_number 숫자형 변환을 수행합니다.
        sheet_df['category'] = sheet_df['category'].fillna('기타').astype(str).str.strip()
        sheet_df['question'] = sheet_df['question'].fillna('').astype(str).str.strip()
        sheet_df['question_original'] = sheet_df['question_original'].fillna('').astype(str).str.strip()
        sheet_df['answer'] = sheet_df['answer'].fillna('').astype(str).str.strip()
        sheet_df['faq_number'] = pd.to_numeric(sheet_df['faq_number'], errors='coerce')

        # 질문과 답변이 모두 있는 행만 남깁니다.
        sheet_df = sheet_df[
            (sheet_df['question'] != '')
            & (sheet_df['answer'] != '')
        ].copy()

        # 비어 있지 않은 시트 결과만 리스트에 추가합니다.
        if not sheet_df.empty:
            brand_faq_frames.append(sheet_df)

    # 어떤 시트에서도 유효한 FAQ를 찾지 못하면 빈 DataFrame을 반환합니다.
    if not brand_faq_frames:
        return pd.DataFrame(
            columns=[
                'brand',
                'category',
                'faq_number',
                'question',
                'question_original',
                'answer',
            ]
        )

    # 모든 시트의 FAQ를 하나의 DataFrame으로 합칩니다.
    brand_faq_data = pd.concat(brand_faq_frames, ignore_index=True)

    # 브랜드, 카테고리, 번호, 질문 기준으로 정렬해 반환합니다.
    return brand_faq_data.sort_values(
        ['brand', 'category', 'faq_number', 'question'],
        na_position='last',
    ).reset_index(drop=True)

def load_local_subsidy_data() -> pd.DataFrame:
    local_subsidy_excel_path = _find_first_existing_path(
        ['무공해_지자체_보조금.xlsx'],
        [
            RAW_DIR / 'subsidy',
            RAW_DIR,
            PROCESSED_DIR,
            PROJECT_ROOT / 'data',
            Path.cwd(),
            Path('/mnt/data'),
        ],
    )

    if local_subsidy_excel_path is None or not local_subsidy_excel_path.exists():
        return pd.DataFrame(
            [
                ['서울특별시', '60', '700'],
                ['부산광역시', '280', '1100'],
                ['경기도', '200~484', '1,000~1,250'],
                ['제주특별자치도', '400', '-'],
            ],
            columns=['region', 'ev_subsidy', 'hydrogen_subsidy'],
        )

    local_subsidy_data = pd.read_excel(local_subsidy_excel_path, sheet_name=0)

    local_subsidy_data = _standardize_columns(
        local_subsidy_data,
        {
            '시도': 'region',
            '전기자동차': 'ev_subsidy',
            '수소자동차': 'hydrogen_subsidy',
        },
    )

    required_columns = ['region', 'ev_subsidy', 'hydrogen_subsidy']
    for required_column in required_columns:
        if required_column not in local_subsidy_data.columns:
            local_subsidy_data[required_column] = pd.NA

    local_subsidy_data = local_subsidy_data[required_columns].copy()

    for column_name in ['region', 'ev_subsidy', 'hydrogen_subsidy']:
        local_subsidy_data[column_name] = (
            local_subsidy_data[column_name]
            .fillna('')
            .astype(str)
            .str.strip()
        )

    local_subsidy_data = local_subsidy_data[
        local_subsidy_data['region'] != ''
    ].reset_index(drop=True)

    return local_subsidy_data