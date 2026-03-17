from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
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
    policy_data = _load_first_existing_csv(
        [
            'policy_data.csv',
            'ev_policy_data.csv',
            'ev_policies.csv',
        ]
    )

    if policy_data is None:
        policy_data = pd.DataFrame(
            [
                ['서울', '전기차 구매 보조금', '구매보조', '최대 680만원', '2026-03-01', '국비와 지방비를 합산한 예시 금액입니다.', 'https://example.com/seoul-policy'],
                ['경기', '전기차 구매 보조금', '구매보조', '최대 720만원', '2026-03-01', '차종과 배터리 조건에 따라 차등 지급됩니다.', 'https://example.com/gyeonggi-policy'],
                ['인천', '전기차 충전기 설치 지원', '설치지원', '최대 150만원', '2026-02-20', '공동주택 우선 지원 기준의 예시입니다.', 'https://example.com/incheon-policy'],
                ['부산', '친환경차 세제 안내', '세제혜택', '개별소비세 감면', '2026-02-15', '세부 적용 기준은 최신 공고 확인이 필요합니다.', 'https://example.com/busan-policy'],
                ['대구', '소상공인 전기화물차 지원', '특별지원', '추가 100만원', '2026-02-28', '예산 소진 시 조기 종료될 수 있습니다.', 'https://example.com/daegu-policy'],
            ],
            columns=['region', 'policy_name', 'support_type', 'amount', 'updated_at', 'summary', 'url'],
        )

    policy_data = _standardize_columns(
        policy_data,
        {
            '지역': 'region',
            '정책명': 'policy_name',
            '지원유형': 'support_type',
            '지원금액': 'amount',
            '갱신일': 'updated_at',
            '요약': 'summary',
            '링크': 'url',
        },
    )
    policy_data = _to_datetime(policy_data, ['updated_at'])

    required_columns = ['region', 'policy_name', 'support_type', 'amount', 'updated_at', 'summary', 'url']
    for required_column in required_columns:
        if required_column not in policy_data.columns:
            policy_data[required_column] = pd.NA

    return policy_data[required_columns].sort_values(['region', 'updated_at']).reset_index(drop=True)



def load_faq_data() -> pd.DataFrame:
    faq_data = _load_first_existing_excel(
        [
            'seoul_ev_faq.xlsx',
            'faq_data.xlsx',
            'ev_faq_data.xlsx',
            'faq.xlsx',
        ],
        sheet_name='faq',
    )

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
                ['보조금', 1, '보조금은 모든 전기차에 동일하게 적용되나요?', '차종, 가격 구간, 지자체 예산, 신청 시점에 따라 달라질 수 있습니다.'],
                ['보조금', 2, '보조금 신청 전 꼭 확인할 것은 무엇인가요?', '접수 기간, 대상 차종, 거주 요건, 예산 잔액, 필요 서류를 먼저 확인하는 것이 좋습니다.'],
                ['충전', 3, '충전소에서 바로 충전 가능한지 어떻게 확인하나요?', '운영 상태, 사용 가능 대수, 운영 시간을 함께 확인하면 됩니다. 실제 서비스에서는 운영사 API 연동으로 실시간 여부를 확인합니다.'],
            ],
            columns=['category', 'faq_number', 'question', 'answer'],
        )

    faq_data = _standardize_columns(
        faq_data,
        {
            '구분': 'category',
            '분류': 'category',
            '번호': 'faq_number',
            '질문': 'question',
            '답': 'answer',
            '답변': 'answer',
        },
    )
    faq_data = _to_numeric(faq_data, ['faq_number'])

    required_columns = ['category', 'faq_number', 'question', 'answer']
    for required_column in required_columns:
        if required_column not in faq_data.columns:
            faq_data[required_column] = pd.NA

    faq_data = faq_data[required_columns].copy()
    faq_data['category'] = faq_data['category'].fillna('기타').astype(str).str.strip()
    faq_data['question'] = faq_data['question'].fillna('').astype(str).str.strip()
    faq_data['answer'] = faq_data['answer'].fillna('').astype(str).str.strip()

    faq_data = faq_data[
        (faq_data['question'] != '')
        & (faq_data['answer'] != '')
    ].reset_index(drop=True)

    if faq_data['faq_number'].isna().all():
        faq_data['faq_number'] = range(1, len(faq_data) + 1)

    return faq_data.sort_values(
        ['category', 'faq_number', 'question'],
        na_position='last',
    ).reset_index(drop=True)
