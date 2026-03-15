from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / 'data' / 'raw'
PROCESSED_DIR = PROJECT_ROOT / 'data' / 'processed'


def _load_first_existing_csv(file_names: Iterable[str]) -> pd.DataFrame | None:
    for file_name in file_names:
        csv_path = PROCESSED_DIR / file_name
        if csv_path.exists():
            return pd.read_csv(csv_path)
    return None


def _load_first_existing_excel(
    file_names: Iterable[str],
    sheet_name: str | int | None = 0,
) -> pd.DataFrame | None:
    for file_name in file_names:
        for base_dir in (RAW_DIR, PROCESSED_DIR):
            excel_path = base_dir / file_name
            if excel_path.exists():
                try:
                    return pd.read_excel(excel_path, sheet_name=sheet_name)
                except ValueError:
                    return pd.read_excel(excel_path)
    return None


def _find_first_existing_path(file_names: Iterable[str], search_dirs: Iterable[Path]) -> Path | None:
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for file_name in file_names:
            direct_path = search_dir / file_name
            if direct_path.exists():
                return direct_path
            matched_paths = list(search_dir.rglob(file_name))
            if matched_paths:
                return matched_paths[0]
    return None


def _standardize_columns(dataframe: pd.DataFrame, rename_map: dict[str, str]) -> pd.DataFrame:
    available_rename_map = {
        original_column: new_column
        for original_column, new_column in rename_map.items()
        if original_column in dataframe.columns
    }
    if not available_rename_map:
        return dataframe
    return dataframe.rename(columns=available_rename_map)


def _to_datetime(dataframe: pd.DataFrame, column_names: Iterable[str]) -> pd.DataFrame:
    for column_name in column_names:
        if column_name in dataframe.columns:
            dataframe[column_name] = pd.to_datetime(dataframe[column_name], errors='coerce')
    return dataframe


def _to_numeric(dataframe: pd.DataFrame, column_names: Iterable[str]) -> pd.DataFrame:
    for column_name in column_names:
        if column_name in dataframe.columns:
            dataframe[column_name] = pd.to_numeric(dataframe[column_name], errors='coerce')
    return dataframe


# -------------------------------------------------
# 1. 지역 별 전기차 등록 현황 데이터
# -------------------------------------------------

def load_ev_registration_data() -> pd.DataFrame:
    ev_registration_data = _load_first_existing_csv(
        [
            'ev_registration_data.csv',
            'ev_registrations.csv',
            'region_ev_registration.csv',
        ]
    )

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
    ev_registration_data = _to_datetime(ev_registration_data, ['year_month'])
    ev_registration_data = _to_numeric(ev_registration_data, ['ev_count'])

    required_columns = ['year_month', 'region', 'ev_count']
    for required_column in required_columns:
        if required_column not in ev_registration_data.columns:
            ev_registration_data[required_column] = pd.NA

    ev_registration_data = ev_registration_data[required_columns].dropna(subset=['region'])
    ev_registration_data['ev_count'] = ev_registration_data['ev_count'].fillna(0)
    return ev_registration_data.sort_values(['year_month', 'region']).reset_index(drop=True)


# -------------------------------------------------
# 2. 충전소 위치 / 충전 가능 여부 / 운영 정보
# -------------------------------------------------

def load_charger_operation_data() -> pd.DataFrame:
    charger_operation_data = _load_first_existing_csv(
        [
            'charger_operation_data.csv',
            'charger_locations.csv',
            'charger_status_data.csv',
        ]
    )

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
    charger_operation_data = _to_numeric(
        charger_operation_data,
        ['latitude', 'longitude', 'available_count', 'total_count'],
    )

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
    for required_column in required_columns:
        if required_column not in charger_operation_data.columns:
            charger_operation_data[required_column] = pd.NA

    return charger_operation_data[required_columns].reset_index(drop=True)


# -------------------------------------------------
# 3. 충전 요금 관련 데이터
# -------------------------------------------------

def load_charging_fee_data() -> pd.DataFrame:
    charging_fee_data = _load_first_existing_csv(
        [
            'charging_fee_data.csv',
            'charging_fee_reference.csv',
            'fee_reference.csv',
        ]
    )

    if charging_fee_data is None:
        charging_fee_data = pd.DataFrame(
            [
                ['환경부', '급속', 324.4, 292.9, 347.2, '시간대/정책에 따라 변동 가능'],
                ['환경부', '완속', 286.4, 258.2, 301.5, '회원/비회원 단가 상이'],
                ['한국전력', '급속', 339.0, 309.0, 359.0, '부가서비스에 따라 상이'],
                ['한국전력', '완속', 289.0, 265.0, 305.0, '지역/제휴 여부 반영 가능'],
                ['E-pit', '초급속', 415.0, 395.0, 435.0, '고출력 장비 기준 예시'],
            ],
            columns=[
                'operator',
                'charger_type',
                'base_price_per_kwh',
                'member_price_per_kwh',
                'non_member_price_per_kwh',
                'note',
            ],
        )

    charging_fee_data = _standardize_columns(
        charging_fee_data,
        {
            '운영사': 'operator',
            '충전기유형': 'charger_type',
            '기본단가': 'base_price_per_kwh',
            '회원단가': 'member_price_per_kwh',
            '비회원단가': 'non_member_price_per_kwh',
            '비고': 'note',
        },
    )
    charging_fee_data = _to_numeric(
        charging_fee_data,
        ['base_price_per_kwh', 'member_price_per_kwh', 'non_member_price_per_kwh'],
    )

    required_columns = [
        'operator',
        'charger_type',
        'base_price_per_kwh',
        'member_price_per_kwh',
        'non_member_price_per_kwh',
        'note',
    ]
    for required_column in required_columns:
        if required_column not in charging_fee_data.columns:
            charging_fee_data[required_column] = pd.NA

    return charging_fee_data[required_columns].reset_index(drop=True)


# -------------------------------------------------
# 4. 보조금 정책 / FAQ 데이터
# -------------------------------------------------

def load_policy_data() -> pd.DataFrame:
    subsidy_excel_path = RAW_DIR / 'subsidy' / 'national subsidy.xlsx'

    if subsidy_excel_path.exists():
        subsidy_sheet_names = [
            '승용 및 초소형 전기자동차(2026년)',
            '전기화물차(2026년)',
            '전기승합차(2026년)',
            '전기이륜차(2026년)',
            '건설기계(2026년)',
            '수소차(2026년)',
        ]

        subsidy_dataframes = []

        for sheet_name in subsidy_sheet_names:
            try:
                sheet_dataframe = pd.read_excel(
                    subsidy_excel_path,
                    sheet_name=sheet_name,
                    engine='openpyxl',
                ).copy()
            except ValueError:
                continue

            if sheet_dataframe.empty:
                continue

            sheet_dataframe['sheet_name'] = sheet_name

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

            required_columns = [
                'sheet_name',
                'vehicle_group',
                'vehicle_class',
                'manufacturer',
                'model_name',
                'subsidy_amount',
            ]

            for required_column in required_columns:
                if required_column not in sheet_dataframe.columns:
                    sheet_dataframe[required_column] = pd.NA

            sheet_dataframe = sheet_dataframe[required_columns].copy()
            subsidy_dataframes.append(sheet_dataframe)

        if subsidy_dataframes:
            policy_data = pd.concat(subsidy_dataframes, ignore_index=True)
            policy_data = _to_numeric(policy_data, ['subsidy_amount'])

            policy_data['sheet_name'] = policy_data['sheet_name'].fillna('').astype(str).str.strip() # 공란을 미분류 처리하는 코드
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

            policy_data = policy_data[
                policy_data['model_name'] != ''
            ].reset_index(drop=True)

            return policy_data.sort_values(
                ['sheet_name', 'vehicle_group', 'vehicle_class', 'manufacturer', 'model_name'],
                na_position='last',
            ).reset_index(drop=True)

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

    return policy_data.reset_index(drop=True)


def load_faq_data() -> pd.DataFrame:
    def _is_valid_faq_dataframe(dataframe: pd.DataFrame | None) -> bool:
        if dataframe is None or dataframe.empty:
            return False

        faq_like_columns = {'구분', '번호', '질문', '질문_원문', '답', '답변', '카테고리', '태그'}
        return len(set(dataframe.columns) & faq_like_columns) >= 3 and any(
            column in dataframe.columns for column in ['질문', 'question']
        ) and any(
            column in dataframe.columns for column in ['답', '답변', 'answer']
        )

    categorized_faq_path = _find_first_existing_path(
        ['seoul_ev_faq_categorized.xlsx'],
        [PROJECT_ROOT / 'data' / 'webcrawling'],
    )
    faq_data = None

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

    if faq_data is None:
        faq_data = _load_first_existing_csv(
            [
                'faq_data.csv',
                'ev_faq_data.csv',
                'faq.csv',
            ]
        )

    if faq_data is None:
        faq_data = pd.DataFrame(
            [
                ['전기승용,화물,승합 등', '지원대상·차종', '대상', 1, '전기차 지원 가능 차량 및 보조금 확인 방법은?', '무공해차 통합누리집에서 지역별 조회가 가능합니다.'],
                ['전기승용,화물,승합 등', '자격조건·제출서류', '자격', 2, '서울시 보조금 지원 자격 조건은?', '서울 거주 및 사업자 등록 여부 등 공고 기준을 확인해야 합니다.'],
                ['전기이륜', '신청방법·절차', '신청', 3, '전기이륜차 보조금 신청은 어떻게 하나요?', '구매 계약 후 무공해차 통합누리집 또는 지자체 공고 절차에 따라 진행합니다.'],
            ],
            columns=['faq_group', 'category', 'tag', 'faq_number', 'question', 'answer'],
        )

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
    faq_data = _to_numeric(faq_data, ['faq_number'])

    required_columns = ['faq_group', 'category', 'tag', 'faq_number', 'question', 'question_original', 'answer']
    for required_column in required_columns:
        if required_column not in faq_data.columns:
            faq_data[required_column] = pd.NA

    faq_data = faq_data[required_columns].copy()
    faq_data['faq_group'] = faq_data['faq_group'].fillna('기타').astype(str).str.strip()
    faq_data['category'] = faq_data['category'].fillna('기타').astype(str).str.strip()
    faq_data['tag'] = faq_data['tag'].fillna('').astype(str).str.strip()
    faq_data['question'] = faq_data['question'].fillna('').astype(str).str.strip()
    faq_data['question_original'] = faq_data['question_original'].fillna('').astype(str).str.strip()
    faq_data['answer'] = faq_data['answer'].fillna('').astype(str).str.strip()

    faq_data = faq_data[
        (faq_data['question'] != '')
        & (faq_data['answer'] != '')
    ].reset_index(drop=True)

    if faq_data['faq_number'].isna().all():
        faq_data['faq_number'] = range(1, len(faq_data) + 1)

    return faq_data.sort_values(
        ['faq_group', 'category', 'faq_number', 'question'],
        na_position='last',
    ).reset_index(drop=True)


def load_news_keyword_data() -> pd.DataFrame:
    keyword_excel_path = _find_first_existing_path(
        ['keyword_frequency.xlsx'],
        [PROJECT_ROOT / 'data' / 'webcrawling'],
    )

    if keyword_excel_path is not None and keyword_excel_path.exists():
        news_keyword_data = pd.read_excel(keyword_excel_path, engine='openpyxl')
    else:
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

    news_keyword_data = _standardize_columns(
        news_keyword_data,
        {
            'keyword': '키워드',
            'count': '빈도수',
            '빈도': '빈도수',
        },
    )
    required_columns = ['키워드', '빈도수']
    for required_column in required_columns:
        if required_column not in news_keyword_data.columns:
            news_keyword_data[required_column] = pd.NA

    news_keyword_data['키워드'] = news_keyword_data['키워드'].fillna('').astype(str).str.strip()
    news_keyword_data['빈도수'] = pd.to_numeric(news_keyword_data['빈도수'], errors='coerce').fillna(0)

    news_keyword_data = news_keyword_data[news_keyword_data['키워드'] != ''].copy()
    return news_keyword_data.sort_values(['빈도수', '키워드'], ascending=[False, True]).reset_index(drop=True)


def resolve_news_wordcloud_path() -> Path | None:
    return _find_first_existing_path(
        ['wordcloud.png'],
        [PROJECT_ROOT / 'data' / 'webcrawling'],
    )
