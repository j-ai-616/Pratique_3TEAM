# 이 스크립트는 전기차 등록 현황 데이터 중 "지역별 등록 현황" 화면에 필요한
# 데이터 가공 전용 보조 로직을 담당합니다.
#
# 이 스크립트의 핵심 역할은 다음과 같습니다.
#
# 1) 지역별 전기차 등록 데이터 필터링
#    - 사용자가 선택한 지역 목록(selected_regions)에 따라
#      전체 전기차 등록 데이터에서 필요한 지역만 남깁니다.
#
# 2) 최신 시점 기준 요약 정보 계산
#    - 필터링된 데이터에서 가장 최근 월(latest_month)을 찾고,
#      그 월의 지역별 등록 대수를 기준으로
#      총합, 평균, 최다 등록 지역, 포함 지역 수 등을 계산합니다.
#
# 3) 시계열 추이용 데이터 생성
#    - year_month를 행(index), region을 열(columns)로 하는
#      피벗 테이블을 만들어 지역별 월별 추이 그래프에 바로 사용할 수 있게 변환합니다.
#
# 이 스크립트는 직접 Streamlit 화면을 그리지 않습니다.
# 대신 "지역별 전기차 등록 현황" 화면을 구성하는 다른 스크립트에서
# 이 함수들을 호출하여 필터링, 요약, 추이 데이터 생성을 수행합니다.
#
# 이 스크립트와 주로 상호작용하는 스크립트는 다음과 같습니다.
#
# 1) src/data/region_ev_section.py
#    - 이 스크립트의 가장 직접적인 사용처입니다.
#    - region_ev_section.py는 화면(UI)을 그리는 역할을 하고,
#      현재 스크립트는 그 화면에 필요한 데이터 가공 로직을 제공합니다.
#    - 즉, 역할 분담은 보통 다음과 같습니다.
#         region_ev_section.py  -> 화면 출력
#         현재 스크립트         -> 데이터 필터링 / 요약 / 추이 생성
#
# 2) src/db/query_data.py
#    - 원본 또는 전처리된 전기차 등록 현황 데이터를 읽어서
#      ev_registration_data 형태의 DataFrame으로 준비합니다.
#    - 현재 스크립트는 query_data.py가 준비한 DataFrame을 입력으로 받아 가공합니다.
#
# 3) src/app/main_app.py
#    - 전체 앱의 진입점이며 메뉴 라우팅을 담당합니다.
#    - main_app.py에서 query_data.py를 통해 ev_registration_data를 불러오고,
#      지역별 전기차 등록 현황 메뉴 선택 시 region_ev_section.py에 전달합니다.
#    - 이후 region_ev_section.py 내부에서 현재 스크립트의 함수들이 호출됩니다.
#
# 정리하면,
# 이 스크립트는 "지역별 전기차 등록 현황 화면에 필요한 데이터 가공 전담 스크립트"입니다.

from __future__ import annotations

# 표 형태 데이터(DataFrame)를 다루기 위한 pandas 라이브러리입니다.
# 필터링, 정렬, 집계, 피벗 테이블 생성 등에 사용합니다.
import pandas as pd



def filter_region_ev_data(ev_registration_data: pd.DataFrame, selected_regions: list[str] | None = None) -> pd.DataFrame:
    # 입력 데이터가 None이거나 비어 있으면,
    # 이후 화면 로직에서 컬럼 참조 오류가 나지 않도록
    # 미리 정해 둔 컬럼 구조를 가진 빈 DataFrame을 반환합니다.
    if ev_registration_data is None or ev_registration_data.empty:
        return pd.DataFrame(columns=['year_month', 'region', 'ev_count'])

    # 원본 DataFrame을 직접 수정하지 않도록 복사본을 생성합니다.
    filtered_region_ev_data = ev_registration_data.copy()

    # 사용자가 선택한 지역 목록(selected_regions)이 존재하면
    # region 컬럼 값이 그 목록 안에 포함되는 행만 남깁니다.
    if selected_regions:
        filtered_region_ev_data = filtered_region_ev_data[
            filtered_region_ev_data['region'].isin(selected_regions)
        ]

    # year_month, region 순서로 정렬한 뒤
    # 인덱스를 0부터 다시 정리하여 반환합니다.
    return filtered_region_ev_data.sort_values(['year_month', 'region']).reset_index(drop=True)



def summarize_region_ev_data(filtered_region_ev_data: pd.DataFrame) -> dict:
    # 입력 데이터가 None이거나 비어 있으면,
    # 화면에 표시할 기본 요약값들을 모두 0 또는 빈 값으로 반환합니다.
    if filtered_region_ev_data is None or filtered_region_ev_data.empty:
        return {
            'latest_month': None,
            'latest_region_data': pd.DataFrame(columns=['year_month', 'region', 'ev_count']),
            'total_ev_count': 0,
            'average_ev_count': 0,
            'top_region': '-',
            'top_region_count': 0,
            'covered_region_count': 0,
        }

    # 필터링된 데이터에서 가장 최신 월(year_month)의 값을 구합니다.
    latest_month = filtered_region_ev_data['year_month'].max()

    # 최신 월에 해당하는 데이터만 추출한 뒤,
    # ev_count가 큰 순서대로 정렬합니다.
    latest_region_data = filtered_region_ev_data[
        filtered_region_ev_data['year_month'] == latest_month
    ].sort_values('ev_count', ascending=False)

    # 최신 월 기준 전체 지역의 전기차 등록 대수 총합을 계산합니다.
    # 결측치는 0으로 처리합니다.
    total_ev_count = int(latest_region_data['ev_count'].fillna(0).sum())

    # 최신 월 기준 지역별 등록 대수 평균을 계산합니다.
    # latest_region_data가 비어 있으면 0을 사용합니다.
    average_ev_count = int(latest_region_data['ev_count'].fillna(0).mean()) if not latest_region_data.empty else 0

    # 최신 월 기준 포함된 지역 개수(고유 region 수)를 계산합니다.
    covered_region_count = int(latest_region_data['region'].nunique())

    # 최신 월 데이터가 비어 있으면
    # 최다 등록 지역(top_region) 정보는 기본값으로 설정합니다.
    if latest_region_data.empty:
        top_region = '-'
        top_region_count = 0
    else:
        # 최신 월 데이터 중 첫 번째 행은 ev_count 내림차순 정렬 기준으로
        # 가장 등록 대수가 큰 지역입니다.
        top_row = latest_region_data.iloc[0]

        # 최다 등록 지역명을 문자열로 추출합니다.
        top_region = str(top_row.get('region', '-'))

        # 해당 지역의 등록 대수를 정수형으로 추출합니다.
        top_region_count = int(top_row.get('ev_count', 0) or 0)

    # 계산한 요약 결과를 딕셔너리 형태로 반환합니다.
    return {
        'latest_month': latest_month,
        'latest_region_data': latest_region_data,
        'total_ev_count': total_ev_count,
        'average_ev_count': average_ev_count,
        'top_region': top_region,
        'top_region_count': top_region_count,
        'covered_region_count': covered_region_count,
    }



def build_region_ev_trend(filtered_region_ev_data: pd.DataFrame) -> pd.DataFrame:
    # 입력 데이터가 None이거나 비어 있으면
    # 추이 그래프에 사용할 수 있는 데이터가 없으므로 빈 DataFrame을 반환합니다.
    if filtered_region_ev_data is None or filtered_region_ev_data.empty:
        return pd.DataFrame()

    # year_month를 행(index), region을 열(columns), ev_count를 값(values)으로 하는
    # 피벗 테이블을 생성합니다.
    # 동일 월/동일 지역 데이터가 여러 건 있는 경우 aggfunc='sum'으로 합산합니다.
    region_ev_trend = filtered_region_ev_data.pivot_table(
        index='year_month',
        columns='region',
        values='ev_count',
        aggfunc='sum',
    ).sort_index()

    # 피벗 테이블의 인덱스(year_month)는 보통 datetime 타입이므로,
    # 그래프 축이나 표시에 더 보기 쉽도록 'YYYY-MM' 문자열 형태로 바꿉니다.
    region_ev_trend.index = [
        year_month.strftime('%Y-%m') if pd.notna(year_month) else '-'
        for year_month in region_ev_trend.index
    ]

    # 피벗 과정에서 생긴 결측치는 0으로 채운 뒤 반환합니다.
    return region_ev_trend.fillna(0)