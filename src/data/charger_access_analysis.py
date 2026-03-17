# 이 스크립트는 전기차 충전소 운영 정보 데이터를 가공하는 역할을 합니다.
# 구체적으로는 다음 3가지 핵심 기능을 담당합니다.
#
# 1) 충전소 운영 정보 필터링
#    - 지역(region), 충전기 유형(charger_type), 사용 가능 여부(available_count > 0)를 기준으로
#      원본 충전소 데이터를 걸러냅니다.
#
# 2) 충전소 운영 정보 요약
#    - 필터링된 충전소 데이터로부터
#      충전소 개수, 사용 가능한 충전기 수, 전체 충전기 수를 집계합니다.
#
# 3) 지도 표시용 데이터 생성
#    - 필터링된 충전소 데이터 중 위도(latitude), 경도(longitude)가 존재하는 행만 골라
#      지도 시각화에 사용할 수 있는 리스트 형태의 결과를 만듭니다.
#
# 이 스크립트는 화면을 직접 그리는 역할은 하지 않으며,
# Streamlit 화면이나 지도 서비스에서 바로 사용할 수 있도록
# 충전소 데이터를 정리하고 가공하는 "중간 처리 로직" 역할을 합니다.

# charger_access_analysis.py → charger_section.py에 붙어서 동작하는 데이터 가공용 보조 모듈. 최종적으로 charger_section.py의 render_charger_page() 로 들어갑니다.

from __future__ import annotations

# 표 형태 데이터(DataFrame)를 다루기 위한 pandas 라이브러리입니다.
# 결측치 확인(pd.isna), DataFrame 필터링, 합계 계산 등에 사용합니다.
import pandas as pd



def filter_charger_operation_data(
    charger_operation_data: pd.DataFrame,
    selected_regions: list[str] | None = None,
    selected_charger_types: list[str] | None = None,
    only_available: bool = False,
) -> pd.DataFrame:
    # charger_operation_data가 None이거나 비어 있으면
    # 이후 코드에서 컬럼이 없어서 오류가 나지 않도록
    # 미리 정해 둔 컬럼 구조를 가진 빈 DataFrame을 반환합니다.
    if charger_operation_data is None or charger_operation_data.empty:
        return pd.DataFrame(
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
            ]
        )

    # 원본 DataFrame이 직접 변경되지 않도록 복사본을 만들어 사용합니다.
    filtered_charger_operation_data = charger_operation_data.copy()

    # 사용자가 선택한 지역 목록(selected_regions)이 존재하면
    # region 컬럼 값이 그 목록 안에 포함되는 행만 남깁니다.
    if selected_regions:
        filtered_charger_operation_data = filtered_charger_operation_data[
            filtered_charger_operation_data['region'].isin(selected_regions)
        ]

    # 사용자가 선택한 충전기 유형 목록(selected_charger_types)이 존재하면
    # charger_type 컬럼 값이 그 목록 안에 포함되는 행만 남깁니다.
    if selected_charger_types:
        filtered_charger_operation_data = filtered_charger_operation_data[
            filtered_charger_operation_data['charger_type'].isin(selected_charger_types)
        ]

    # only_available 값이 True이고,
    # DataFrame에 available_count 컬럼이 실제로 존재하면
    # 사용 가능한 충전기 수가 1개 이상인 행만 남깁니다.
    if only_available and 'available_count' in filtered_charger_operation_data.columns:
        filtered_charger_operation_data = filtered_charger_operation_data[
            filtered_charger_operation_data['available_count'].fillna(0) > 0
        ]

    # 필터링이 끝난 결과의 인덱스를 0부터 다시 정렬하여 반환합니다.
    return filtered_charger_operation_data.reset_index(drop=True)



def summarize_charger_operation_data(filtered_charger_operation_data: pd.DataFrame) -> dict:
    # 입력 데이터가 None이거나 비어 있으면
    # 집계할 값이 없으므로 모든 요약 수치를 0으로 반환합니다.
    if filtered_charger_operation_data is None or filtered_charger_operation_data.empty:
        return {
            'charger_station_count': 0,
            'available_charger_count': 0,
            'total_charger_count': 0,
        }

    # 현재 필터링된 DataFrame의 행 개수를 충전소 개수로 계산합니다.
    # 보통 한 행이 하나의 충전소 또는 충전소 운영 단위라고 가정합니다.
    charger_station_count = int(len(filtered_charger_operation_data))

    # available_count 컬럼의 결측치를 0으로 바꾼 뒤 모두 더해서
    # 사용 가능한 충전기 총 개수를 계산합니다.
    available_charger_count = int(filtered_charger_operation_data['available_count'].fillna(0).sum())

    # total_count 컬럼의 결측치를 0으로 바꾼 뒤 모두 더해서
    # 전체 충전기 총 개수를 계산합니다.
    total_charger_count = int(filtered_charger_operation_data['total_count'].fillna(0).sum())

    # 계산한 집계 결과를 딕셔너리 형태로 반환합니다.
    return {
        'charger_station_count': charger_station_count,
        'available_charger_count': available_charger_count,
        'total_charger_count': total_charger_count,
    }



def build_charger_map_results(filtered_charger_operation_data: pd.DataFrame) -> list[dict]:
    # 입력 데이터가 None이거나 비어 있으면
    # 지도에 표시할 결과가 없으므로 빈 리스트를 반환합니다.
    if filtered_charger_operation_data is None or filtered_charger_operation_data.empty:
        return []

    # 지도 표시용 결과를 담을 리스트를 초기화합니다.
    charger_map_results: list[dict] = []

    # DataFrame의 각 행을 순회하면서 지도에 올릴 포인트 데이터를 만듭니다.
    for _, charger_row in filtered_charger_operation_data.iterrows():
        # 현재 행에서 위도와 경도를 가져옵니다.
        latitude = charger_row.get('latitude')
        longitude = charger_row.get('longitude')

        # 위도나 경도 중 하나라도 결측치이면
        # 지도에 표시할 수 없으므로 이 행은 건너뜁니다.
        if pd.isna(latitude) or pd.isna(longitude):
            continue

        # 지도 표시용 딕셔너리를 만들어 결과 리스트에 추가합니다.
        charger_map_results.append(
            {
                # 지도 마커나 목록에 표시할 충전소 이름입니다.
                # 값이 없으면 기본값으로 '충전소'를 사용합니다.
                'name': str(charger_row.get('charger_name', '충전소')),

                # 지도 라이브러리에서 사용하기 쉽도록 위도/경도를 float 타입으로 변환합니다.
                'lat': float(latitude),
                'lng': float(longitude),

                # 일반 주소 정보입니다.
                'address': str(charger_row.get('address', '')),

                # 도로명 주소 정보입니다.
                'road_address': str(charger_row.get('road_address', '')),

                # 전화번호 정보입니다.
                'phone': str(charger_row.get('phone', '')),

                # 지도 분류(category) 용도로 충전기 유형(charger_type)을 넣습니다.
                'category': str(charger_row.get('charger_type', '')),

                # 외부 장소 상세 페이지 URL이 없으므로 빈 문자열로 둡니다.
                'place_url': '',
            }
        )

    # 완성된 지도 표시용 결과 리스트를 반환합니다.
    return charger_map_results