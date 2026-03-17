from __future__ import annotations

# 이 스크립트는 프로젝트 전반에서 공통으로 사용하는 "작은 보조 유틸 함수"를 모아둔 파일입니다.
#
# 이 스크립트의 핵심 역할은 다음과 같습니다.
#
# 1) 숫자 표시 형식 통일
#    - 정수나 숫자형 값을 화면에 출력할 때
#      천 단위 콤마가 포함된 문자열 형태로 바꿔 줍니다.
#    - 값이 비어 있거나 숫자로 바꿀 수 없으면 "-"를 반환하여
#      화면에서 오류 대신 안전한 표시가 되도록 돕습니다.
#
# 2) 기본 지역 선택값 자동 추론
#    - 사용자가 검색창에 입력한 지역/장소 문자열(search_region)을 기준으로
#      region_list 안에서 관련 있는 지역명을 찾아 기본 선택값으로 반환합니다.
#    - 예를 들어 사용자가 "서울"을 입력했다면
#      region_list 안의 "서울"을 기본 선택값으로 잡아 줄 수 있습니다.
#
# 이 스크립트는 직접 Streamlit 화면을 그리지는 않습니다.
# 대신 다른 화면 스크립트에서 import해서 사용하는 공통 유틸 모듈입니다.
#
# 이 스크립트와 상호작용하는 주요 스크립트는 다음과 같습니다.
#
# 1) src/data/charger_section.py
#    - 가장 직접적으로 연결되는 스크립트입니다.
#    - format_number()를 사용해 충전소 수, 사용 가능 충전기 수, 전체 충전기 수를
#      metric에 보기 좋게 표시합니다.
#    - find_default_regions()를 사용해 사용자가 지역 검색창에 입력한 값과
#      운영 정보 지역 목록(region_list)을 비교한 뒤,
#      기본 선택 지역(default_region_list)을 자동으로 잡아 줍니다.
#
# 2) 다른 section 스크립트들
#    - 현재 코드 기준으로는 charger_section.py에서 특히 핵심적으로 사용되지만,
#      숫자 포맷이나 기본 선택값 로직이 필요한 다른 화면 스크립트에서도
#      재사용할 수 있도록 설계된 공통 함수입니다.
#
# 전체 흐름을 간단히 정리하면 다음과 같습니다.
#
# main_app.py
#   -> charger_section.py 실행
# charger_section.py
#   -> format_number() 호출
#   -> find_default_regions() 호출
# 현재 스크립트
#   -> 숫자 표시 문자열 반환
#   -> 기본 지역 선택 리스트 반환
# charger_section.py
#   -> Streamlit metric / multiselect 기본값에 반영
#
# 정리하면,
# 이 스크립트는 프로젝트 내부 여러 화면에서 공통으로 재사용되는
# "숫자 포맷 및 기본 지역 선택 처리용 유틸 스크립트"입니다.



def format_number(value) -> str:
    # 전달받은 값을 정수형으로 변환한 뒤,
    # 천 단위 콤마가 포함된 문자열로 반환합니다.
    # 예: 12345 -> "12,345"
    try:
        return f"{int(value):,}"

    # 값이 None이거나 숫자로 변환할 수 없는 문자열인 경우에는
    # 안전하게 "-"를 반환합니다.
    except (TypeError, ValueError):
        return '-'



def find_default_regions(search_region: str, region_list: list[str]) -> list[str]:
    # 사용자가 지역/장소 검색어를 입력하지 않았으면
    # 전달받은 전체 region_list를 그대로 반환합니다.
    if not search_region:
        return region_list

    # 검색어 앞뒤 공백을 제거합니다.
    cleaned_search_region = search_region.strip()

    # 공백 제거 후에도 빈 문자열이면
    # 전체 region_list를 그대로 반환합니다.
    if not cleaned_search_region:
        return region_list

    # 검색어와 region_list 안의 지역명을 비교하여
    # 서로 포함 관계가 있는 지역만 추출합니다.
    #
    # 예:
    # - cleaned_search_region = "서울"
    # - region_name = "서울"
    #   -> 일치하므로 포함
    #
    # - cleaned_search_region = "서울 강남구"
    # - region_name = "서울"
    #   -> region_name in cleaned_search_region 이므로 포함
    #
    # - cleaned_search_region = "경기"
    # - region_name = "경기"
    #   -> 포함
    matched_regions = [
        region_name
        for region_name in region_list
        if cleaned_search_region in region_name or region_name in cleaned_search_region
    ]

    # 일치하는 지역이 하나라도 있으면 그 목록을 반환하고,
    # 하나도 없으면 전체 region_list를 기본값으로 반환합니다.
    return matched_regions or region_list