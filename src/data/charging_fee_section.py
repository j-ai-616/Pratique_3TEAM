################################################################################################################
#### 3번탭 구현 - 충전 요금 관련

# 이 스크립트는 Streamlit 기반 전기차 정보 포털에서
# "3. 충전 요금 관련" 화면을 구성하는 역할을 합니다.
#
# 이 화면은 크게 두 가지 기능을 담당합니다.
#
# 1) 충전 요금 기준표 표시
#    - 사업자명(operator), 용량구분(charger_type), 회원가, 비회원가 정보를
#      보기 쉬운 표 형태로 화면에 출력합니다.
#
# 2) 예상 충전 비용 계산기
#    - 사용자가 사업자명과 용량구분을 선택하고,
#      충전량(kWh)과 요금 유형(회원 / 비회원 / 기본)을 고르면
#      예상 충전 비용을 계산하여 보여줍니다.
#
# 이 스크립트는 직접 원본 엑셀 파일을 읽는 역할은 하지 않습니다.
# 즉, 데이터 로딩 전담 스크립트와 화면 출력 전담 스크립트가 분리되어 있습니다.
#
# 이 스크립트와 상호작용하는 주요 스크립트는 다음과 같습니다.
#
# 1) src/db/query_data.py
#    - 충전 요금 원본 엑셀 파일을 읽고,
#      이 화면에서 사용할 수 있는 표준 컬럼 구조(DataFrame)로 가공합니다.
#    - 예를 들어 operator, charger_type, member_price_per_kwh,
#      non_member_price_per_kwh, base_price_per_kwh 등의 컬럼을 준비합니다.
#    - 이 스크립트는 query_data.py가 준비한 DataFrame을 입력으로 받아 화면에 표시합니다.
#
# 2) src/app/main_app.py
#    - 전체 Streamlit 앱의 진입점이며 메뉴 라우팅을 담당합니다.
#    - load_dashboard_data()에서 load_charging_fee_data()를 호출해
#      충전 요금 데이터를 미리 불러온 뒤,
#      사용자가 3번 메뉴를 선택하면 render_charging_fee_page()를 실행합니다.
#
# 즉, 전체 흐름은 다음과 같습니다.
#
# query_data.py
#   -> 충전 요금 데이터 로드 및 컬럼 표준화
# main_app.py
#   -> load_dashboard_data()로 데이터 저장
#   -> 3번 메뉴 선택 시 render_charging_fee_page() 호출
# charging_fee_section.py (현재 스크립트)
#   -> 요금 기준표 표시
#   -> 선택한 조건 기준 예상 충전 비용 계산
#
# 정리하면, 이 스크립트는
# "충전 요금 데이터를 화면에 보여주고, 사용자가 직접 비용을 계산해 볼 수 있게 만드는
# Streamlit 화면 렌더링 전담 스크립트"입니다.

# 표 형태 데이터(DataFrame)를 다루기 위한 pandas 라이브러리입니다.
# 숫자 변환(pd.to_numeric), 날짜 변환(pd.to_datetime), 결측치 검사(pd.isna) 등에 사용합니다.
import pandas as pd

# Streamlit 화면 구성을 위한 라이브러리입니다.
# 제목, 캡션, selectbox, slider, radio, dataframe, metric 등을 출력할 때 사용합니다.
import streamlit as st


def _prepare_fee_display_dataframe(charging_fee_data: pd.DataFrame) -> pd.DataFrame:
    # 화면의 "충전 요금 기준표"에서 보여줄 원본 컬럼 목록입니다.
    # 현재는 사업자명, 용량구분, 회원가, 비회원가만 표시하도록 되어 있습니다.
    # fee_type, updated_at, note 컬럼은 주석 처리되어 있어 표에 나타나지 않습니다.
    display_columns = [
        'operator',
        'charger_type',
        #'fee_type',
        'member_price_per_kwh',
        'non_member_price_per_kwh',
        #'updated_at',
        #'note',
    ]

    # 실제로 charging_fee_data 안에 존재하는 컬럼만 골라서 사용합니다.
    # 원본 데이터 구조가 조금 달라도 오류가 나지 않도록 안전하게 처리합니다.
    existing_columns = [column for column in display_columns if column in charging_fee_data.columns]

    # 선택된 컬럼만 가진 복사본 DataFrame을 생성합니다.
    display_fee_data = charging_fee_data[existing_columns].copy()

    # 화면에 보여줄 한글 컬럼명 매핑 정보입니다.
    # 원본 영문 컬럼명을 사용자 친화적인 한글 명칭으로 바꿉니다.
    rename_map = {
        'operator': '사업자명',
        'charger_type': '용량구분',
        #'fee_type': '요금유형',
        'member_price_per_kwh': '회원가(원/kWh)',
        'non_member_price_per_kwh': '비회원가(원/kWh)',
        #'updated_at': '갱신일자',
        #'note': '비고',
    }

    # 컬럼명을 한글 이름으로 변경합니다.
    display_fee_data = display_fee_data.rename(columns=rename_map)

    # 만약 화면 표시용 DataFrame 안에 '갱신일자' 컬럼이 존재한다면,
    # 날짜 형식을 YYYY-MM-DD 형태 문자열로 통일합니다.
    # 현재는 updated_at / 갱신일자 컬럼이 주석 처리되어 있어 일반적으로 실행되지 않는 분기입니다.
    if '갱신일자' in display_fee_data.columns:
        display_fee_data['갱신일자'] = pd.to_datetime(
            display_fee_data['갱신일자'],
            errors='coerce',
        ).dt.strftime('%Y-%m-%d')

        # 날짜 변환 결과가 NaN인 값은 빈 문자열로 바꿉니다.
        display_fee_data['갱신일자'] = display_fee_data['갱신일자'].fillna('')

    # 화면 표시용으로 정리된 DataFrame을 반환합니다.
    return display_fee_data


def render_charging_fee_page(charging_fee_data: pd.DataFrame) -> None:
    # 페이지 상단 제목을 출력합니다.
    st.header("충전 요금 관련")

    # 페이지에 대한 간단한 설명 문구를 출력합니다.
    st.caption("엑셀 원본 기준의 사업자별 충전요금을 조회하고 예상 충전 비용을 계산합니다.")

    # 이 화면이 정상 동작하기 위해 반드시 필요한 최소 컬럼 목록입니다.
    # 이 컬럼들이 있어야 사업자 선택, 용량구분 선택, 단가 계산이 가능합니다.
    required_columns = {
        'operator',
        'charger_type',
        'member_price_per_kwh',
        'non_member_price_per_kwh',
    }

    # 전달받은 데이터가 비어 있거나,
    # 필수 컬럼이 하나라도 없으면 안내 문구를 출력하고 종료합니다.
    if charging_fee_data.empty or not required_columns.issubset(set(charging_fee_data.columns)):
        st.info("표시할 충전 요금 데이터가 없습니다.")
        return

    # 원본 DataFrame을 직접 수정하지 않기 위해 복사본을 생성합니다.
    cleaned_fee_data = charging_fee_data.copy()

    # 문자열로 다루는 컬럼들의 결측치를 빈 문자열로 바꾸고,
    # 문자열 타입으로 변환한 뒤, 앞뒤 공백을 제거합니다.
    # fee_type과 note 컬럼은 현재 화면에 직접 보이지 않더라도
    # 데이터 정리 차원에서 함께 처리합니다.
    for column_name in ['operator', 'charger_type', 'fee_type', 'note']:
        if column_name in cleaned_fee_data.columns:
            cleaned_fee_data[column_name] = cleaned_fee_data[column_name].fillna('').astype(str).str.strip()

    # 숫자형으로 다뤄야 하는 컬럼들을 숫자 타입으로 변환합니다.
    # 변환이 불가능한 값은 NaN으로 처리합니다.
    for column_name in ['base_price_per_kwh', 'member_price_per_kwh', 'non_member_price_per_kwh']:
        if column_name in cleaned_fee_data.columns:
            cleaned_fee_data[column_name] = pd.to_numeric(cleaned_fee_data[column_name], errors='coerce')

    # 사업자명(operator)과 용량구분(charger_type)이 비어 있지 않은 행만 남깁니다.
    # 이 두 값이 없으면 화면에서 선택 조건을 만들 수 없기 때문입니다.
    cleaned_fee_data = cleaned_fee_data[
        (cleaned_fee_data['operator'] != '')
        & (cleaned_fee_data['charger_type'] != '')
    ].copy()

    # 정리 후 데이터가 비어 있으면 안내 문구를 출력하고 종료합니다.
    if cleaned_fee_data.empty:
        st.info("표시할 충전 요금 데이터가 없습니다.")
        return

    # 사업자명 목록을 정렬하여 selectbox 선택지로 만듭니다.
    operator_list = sorted(cleaned_fee_data['operator'].unique().tolist())

    # 사용자가 조회할 사업자명을 선택할 수 있도록 selectbox를 출력합니다.
    selected_operator = st.selectbox("사업자명 선택", operator_list)

    # 선택한 사업자명에 해당하는 데이터만 필터링합니다.
    operator_filtered_data = cleaned_fee_data[
        cleaned_fee_data['operator'] == selected_operator
    ].copy()

    # 선택한 사업자 내부에서 존재하는 용량구분 목록을 정렬하여 선택지로 만듭니다.
    charger_type_list = sorted(operator_filtered_data['charger_type'].unique().tolist())

    # 사용자가 조회할 용량구분을 선택할 수 있도록 selectbox를 출력합니다.
    selected_charger_type = st.selectbox("용량구분 선택", charger_type_list)

    # 선택한 사업자명 + 용량구분 조건에 맞는 데이터만 남깁니다.
    filtered_charging_fee_data = operator_filtered_data[
        operator_filtered_data['charger_type'] == selected_charger_type
    ].copy()

    # 선택 조건에 해당하는 첫 번째 행을 대표 데이터로 사용합니다.
    # 현재 구조상 선택한 사업자와 용량구분 조합에 대해 첫 행을 기준으로 요금을 계산합니다.
    selected_fee_row = filtered_charging_fee_data.iloc[0]

    # 요금 기준표 영역의 소제목을 출력합니다.
    st.subheader("충전 요금 기준표")

    # 화면 표시용으로 정리한 DataFrame을 표 형태로 출력합니다.
    # use_container_width=True 로 화면 너비에 맞춰 넓게 표시하며,
    # hide_index=True 로 인덱스 열은 숨깁니다.
    st.dataframe(
        _prepare_fee_display_dataframe(cleaned_fee_data),
        use_container_width=True,
        hide_index=True,
    )

    # 선택한 요금 정보 영역의 소제목을 출력합니다.
    st.subheader("선택한 요금 정보")

    # 선택한 요금 정보를 3개의 metric 영역으로 나누어 배치합니다.
    info_column_1, info_column_2, info_column_3 = st.columns(3)

    # 선택한 사업자명을 metric으로 출력합니다.
    info_column_1.metric("사업자명", str(selected_fee_row['operator']))

    # 선택한 용량구분을 metric으로 출력합니다.
    info_column_2.metric("용량구분", str(selected_fee_row['charger_type']))

    # fee_type 값이 있으면 그 값을 사용하고,
    # 없거나 비어 있으면 기본값으로 '대표'를 사용합니다.
    #fee_type_text = str(selected_fee_row.get('fee_type', '대표')).strip() or '대표'

    # 요금유형을 metric으로 출력합니다.
    #info_column_3.metric("요금유형", fee_type_text)

    # 예상 충전 비용 계산기 영역의 소제목을 출력합니다.
    st.subheader("예상 충전 비용 계산기")

    # 사용자가 충전량(kWh)을 선택할 수 있도록 슬라이더를 출력합니다.
    # 최소 5, 최대 100, 기본 40, 5 단위로 움직이도록 설정되어 있습니다.
    charging_kwh = st.slider("충전량(kWh)", min_value=5, max_value=100, value=40, step=5)

    # 사용자가 어떤 요금 유형으로 계산할지 선택할 수 있도록 라디오 버튼을 출력합니다.
    price_type = st.radio("요금 유형", ["회원 요금", "비회원 요금"], horizontal=True)

    # 사용자가 선택한 요금 유형에 따라 적용할 단가를 결정합니다.
    if price_type == "비회원 요금":
        # 비회원 요금 선택 시 non_member_price_per_kwh 값을 사용합니다.
        selected_unit_price = selected_fee_row.get("non_member_price_per_kwh")
    #elif price_type == "기본 요금":
        # 기본 요금 선택 시 base_price_per_kwh 값을 사용합니다.
        # selected_unit_price = selected_fee_row.get("base_price_per_kwh")

        # base_price_per_kwh 값이 없으면 회원가를 기본값처럼 대신 사용합니다.
        #if pd.isna(selected_unit_price):
        #    selected_unit_price = selected_fee_row.get("member_price_per_kwh")
    else:
        # 그 외(회원 요금 선택)인 경우 회원가를 사용합니다.
        selected_unit_price = selected_fee_row.get("member_price_per_kwh")

    # 선택된 단가가 NaN이면 계산할 수 없으므로 경고 문구를 출력하고 종료합니다.
    if pd.isna(selected_unit_price):
        st.warning("선택한 조건에 맞는 단가 데이터가 없습니다.")
        return

    # 단가를 float 타입으로 변환합니다.
    selected_unit_price = float(selected_unit_price)

    # 예상 비용은 "충전량 * 단가"로 계산하고 반올림합니다.
    expected_charging_fee = round(charging_kwh * selected_unit_price)

    # 계산 결과를 3개의 metric 영역으로 나누어 배치합니다.
    metric_column_1, metric_column_2, metric_column_3 = st.columns(3)

    # 선택 단가를 표시합니다.
    metric_column_1.metric("선택 단가", f"{selected_unit_price:,.1f} 원/kWh")

    # 선택한 충전량을 표시합니다.
    metric_column_2.metric("충전량", f"{charging_kwh} kWh")

    # 계산된 예상 비용을 표시합니다.
    metric_column_3.metric("예상 비용", f"{expected_charging_fee:,.0f} 원")

    # 실제 충전 요금은 정책, 시간대, 할인 조건 등에 따라 달라질 수 있음을 안내합니다.
    st.info("실제 충전 요금은 사업자 정책, 시간대, 제휴 할인, 로밍 여부 등에 따라 달라질 수 있습니다.")

'''
    # 아래 코드는 현재 주석 처리되어 실행되지 않는 영역입니다.
    # 과거 또는 향후 확장용으로 보이며,
    # 선택한 요금 정보의 갱신일자와 비고를 화면 하단에 표시하는 용도입니다.

    # 선택한 행에서 updated_at 값을 가져옵니다.
    updated_at = selected_fee_row.get("updated_at")

    # updated_at 값이 비어 있지 않으면 날짜 변환을 시도합니다.
    if pd.notna(updated_at):
        updated_at_text = pd.to_datetime(updated_at, errors='coerce')

        # 날짜 변환이 성공하면 YYYY-MM-DD 형태로 캡션을 출력합니다.
        if pd.notna(updated_at_text):
            st.caption(f"갱신일자: {updated_at_text.strftime('%Y-%m-%d')}")

    # 선택한 행에서 note 값을 가져와 문자열로 정리합니다.
    note_text = str(selected_fee_row.get("note", "")).strip()

    # 비고 값이 비어 있지 않으면 캡션 형태로 출력합니다.
    if note_text:
        st.caption(f"비고: {note_text}")
'''