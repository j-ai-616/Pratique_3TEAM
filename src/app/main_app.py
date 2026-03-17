import os
import sys

import streamlit as st


# ------------------------------------------------------------
# Streamlit secrets 설정값
# ------------------------------------------------------------
# .streamlit/secrets.toml 에 저장한 값을 불러옵니다.
kakao_rest_key = st.secrets["KAKAO_REST_API_KEY"]
kakao_js_key = st.secrets["KAKAO_JAVASCRIPT_KEY"]

naver_client_id = st.secrets["NAVER_CLIENT_ID"]
naver_client_secret = st.secrets["NAVER_CLIENT_SECRET"]

mysql_user = st.secrets["mysql"]["user"]
mysql_password = st.secrets["mysql"]["password"]
mysql_host = st.secrets["mysql"]["host"]
mysql_port = st.secrets["mysql"]["port"]
mysql_database = st.secrets["mysql"]["database"]


# ------------------------------------------------------------
# 프로젝트 루트 경로 설정
# ------------------------------------------------------------
# 현재 파일(main_app.py)은 보통 src/app/main_app.py 위치에 존재합니다.
# 따라서 두 단계 위(.., ..)로 올라가면 프로젝트의 최상위 폴더를 찾을 수 있습니다.
# 이렇게 찾은 경로를 PROJECT_ROOT 변수에 저장합니다.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# 파이썬이 프로젝트 루트 경로를 import 검색 대상에 포함하도록 설정합니다.
# 이렇게 해야 src.db.query_data, src.data.xxx_section 같은 모듈을 정상적으로 불러올 수 있습니다.
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ------------------------------------------------------------
# 데이터 로딩 함수 import
# ------------------------------------------------------------
# query_data.py 안에는 각 메뉴 페이지에 필요한 데이터를 읽어오는 함수들이 정의되어 있습니다.
# 예:
# - 전기차 등록 데이터
# - 충전소 운영 데이터
# - 충전 요금 데이터
# - 국고 보조금 데이터
# - 지자체 보조금 데이터
# - FAQ / 뉴스 / 브랜드 FAQ 데이터
#
# main_app.py는 이 함수들을 호출하여 화면에 보여줄 원본 데이터를 준비합니다.
from src.db.query_data import (
    load_charger_operation_data,
    load_charging_fee_data,
    load_ev_registration_data,
    load_faq_data,
    load_news_keyword_data,
    load_policy_data,
    load_brand_faq_data,
    load_local_subsidy_data,
)


# ------------------------------------------------------------
# 각 메뉴 화면 렌더링 함수 import
# ------------------------------------------------------------
# 아래 import들은 “데이터를 화면에 어떻게 보여줄지”를 담당하는 섹션 파일들입니다.
# main_app.py는 직접 복잡한 UI를 그리지 않고, 각 기능별 전담 스크립트에 화면 렌더링을 맡깁니다.

# 1번 메뉴: 지역별 전기차 등록 현황 페이지 렌더링 함수
from src.data.region_ev_section import render_region_ev_page

# 2번 메뉴: 전기차 충전소 정보 페이지 렌더링 함수
from src.data.charger_section import render_charger_page

# 3번 메뉴: 충전 요금 정보 페이지 렌더링 함수
from src.data.charging_fee_section import render_charging_fee_page

# 4-1번 하위 메뉴: 국고 보조금 정책 페이지 렌더링 함수
from src.data.subsidy_section import render_subsidy_page

# 5번 메뉴: 브랜드별 전기차 FAQ 페이지 렌더링 함수
from src.data.brand_faq_section import render_brand_faq_page

# 6번 메뉴: 서울시 전기차 FAQ 페이지 렌더링 함수
from src.data.faq_section import render_faq_page

# 7번 메뉴: 뉴스 기사 분석 페이지 렌더링 함수
from src.data.news_analysis_section import render_news_page

# 4-2번 하위 메뉴: 지자체 보조금 정책 페이지 렌더링 함수
from src.data.local_subsidy_section import render_local_subsidy_page


# ------------------------------------------------------------
# 메뉴 이름 상수 정의
# ------------------------------------------------------------
# 메뉴명을 문자열 상수로 관리하면 오타를 줄일 수 있고,
# 나중에 메뉴명을 변경해도 한 곳만 수정하면 되어 유지보수가 쉬워집니다.

# 1번 메뉴 이름
MENU_REGION_EV = "지역별 전기차 등록 현황"

# 2번 메뉴 이름
MENU_CHARGER = "전기차 충전소 정보"

# 3번 메뉴 이름
MENU_CHARGING_FEE = "충전 요금 정보"

# 4번 상위 메뉴 이름
MENU_SUBSIDY = "보조금 정책"

# 4번 하위 메뉴 이름 - 국고 보조금
SUBMENU_NATIONAL_SUBSIDY = "국고 보조금 정책"

# 4번 하위 메뉴 이름 - 지자체 보조금
SUBMENU_LOCAL_SUBSIDY = "지자체 보조금 정책"

# 5번 상위 메뉴 이름
MENU_EV_FAQ = "전기차 FAQ"

# 5번 하위 메뉴 이름 - 브랜드 FAQ
SUBMENU_BRAND_FAQ = "브랜드별 전기차 FAQ"

# 5번 하위 메뉴 이름 - 서울시 FAQ
SUBMENU_SEOUL_FAQ = "서울시 전기차 FAQ"

# 6번 메뉴 이름
MENU_NEWS = "뉴스 기사 분석"


# ------------------------------------------------------------
# 데이터 일괄 로드 함수
# ------------------------------------------------------------
# 이 함수는 앱 전체에서 사용하는 주요 데이터를 한 번에 읽어와 딕셔너리로 반환합니다.
#
# @st.cache_data(show_spinner=False)의 의미:
# - 같은 데이터를 매번 다시 읽지 않고 캐시에 저장합니다.
# - 사용자가 메뉴를 바꿔도 이미 읽은 데이터는 재사용할 수 있어 앱이 더 빠르게 동작합니다.
# - show_spinner=False 는 데이터 로딩 중 기본 스피너를 표시하지 않겠다는 뜻입니다.
@st.cache_data(show_spinner=False)
def load_dashboard_data():
    """
    앱 전체에서 사용할 주요 데이터를 한 번에 불러옵니다.

    반환값:
        dict:
            각 메뉴에서 사용하는 DataFrame 들을 key-value 형태로 반환합니다.

    예:
        {
            "ev_registration_data": ...,
            "charger_operation_data": ...,
            ...
        }
    """
    return {
        "ev_registration_data": load_ev_registration_data(),
        "charger_operation_data": load_charger_operation_data(),
        "charging_fee_data": load_charging_fee_data(),
        "policy_data": load_policy_data(),
        "local_subsidy_data": load_local_subsidy_data(),
        "faq_data": load_faq_data(),
        "news_keyword_data": load_news_keyword_data(),
        "brand_faq_data": load_brand_faq_data(),
    }


# ------------------------------------------------------------
# 세션 상태 초기화 함수
# ------------------------------------------------------------
# Streamlit은 버튼 클릭 시 스크립트를 위에서부터 다시 실행하는 구조입니다.
# 따라서 “현재 어떤 메뉴가 선택되었는지”를 기억하려면 session_state를 사용해야 합니다.
#
# 여기서는 다음 상태값을 관리합니다.
# - current_menu: 현재 화면에 렌더링 중인 상위 메뉴
# - current_submenu: 현재 화면에 렌더링 중인 하위 메뉴(보조금 정책/FAQ 안에서 사용)
# - subsidy_expanded: 보조금 정책 하위 메뉴가 펼쳐져 있는지 여부
# - faq_expanded: FAQ 하위 메뉴가 펼쳐져 있는지 여부
def initialize_menu_state() -> None:
    """
    사이드바 메뉴 상태를 초기화합니다.

    초기 상태:
    - current_menu: 지역별 전기차 등록 현황
    - current_submenu: 없음
    - subsidy_expanded: 접힌 상태(False)
    - faq_expanded: 접힌 상태(False)
    """
    if "current_menu" not in st.session_state:
        st.session_state.current_menu = MENU_REGION_EV

    if "current_submenu" not in st.session_state:
        st.session_state.current_submenu = None

    if "subsidy_expanded" not in st.session_state:
        st.session_state.subsidy_expanded = False

    if "faq_expanded" not in st.session_state:
        st.session_state.faq_expanded = False


# ------------------------------------------------------------
# 사이드바 렌더링 함수
# ------------------------------------------------------------
# 이 함수는 왼쪽 사이드바 메뉴 UI를 구성하고,
# 사용자가 어떤 메뉴/하위 메뉴를 눌렀는지 session_state에 반영하는 역할을 합니다.
#
# 중요한 동작 규칙:
# 1. 일반 메뉴(지역별 전기차 등록 현황, 충전소 정보 등)는 클릭 즉시 해당 페이지로 이동합니다.
# 2. 보조금 정책은 “상위 토글 메뉴”입니다.
#    즉, 클릭 시 바로 화면이 바뀌는 것이 아니라 하위 메뉴를 펼치거나 접는 역할만 합니다.
# 3. 전기차 FAQ도 동일하게 상위 토글 메뉴입니다.
def render_sidebar() -> tuple[str, str | None]:
    """
    사이드바를 화면에 렌더링하고, 현재 선택 상태를 반환합니다.

    반환값:
        tuple[str, str | None]
        - 첫 번째 값: 현재 상위 메뉴
        - 두 번째 값: 현재 하위 메뉴 (없으면 None)
    """
    initialize_menu_state()

    def select_main_menu(menu_name: str) -> None:
        st.session_state.current_menu = menu_name
        st.session_state.current_submenu = None

        if menu_name != MENU_SUBSIDY:
            st.session_state.subsidy_expanded = False

        if menu_name != MENU_EV_FAQ:
            st.session_state.faq_expanded = False

    def toggle_subsidy_menu() -> None:
        st.session_state.subsidy_expanded = not st.session_state.subsidy_expanded

    def toggle_faq_menu() -> None:
        st.session_state.faq_expanded = not st.session_state.faq_expanded

    def select_subsidy_submenu(submenu_name: str) -> None:
        st.session_state.current_menu = MENU_SUBSIDY
        st.session_state.current_submenu = submenu_name
        st.session_state.subsidy_expanded = True

    def select_faq_submenu(submenu_name: str) -> None:
        st.session_state.current_menu = MENU_EV_FAQ
        st.session_state.current_submenu = submenu_name
        st.session_state.faq_expanded = True

    with st.sidebar:
        st.title("⚡ EV 정보 포털")
        st.caption("메뉴를 선택하면 전기차 관련 정보를 확인할 수 있습니다.")

        if st.button("지역별 전기차 등록 현황", use_container_width=True, key="menu_region_ev"):
            select_main_menu(MENU_REGION_EV)

        if st.button("전기차 충전소 정보", use_container_width=True, key="menu_charger"):
            select_main_menu(MENU_CHARGER)

        if st.button("충전 요금 정보", use_container_width=True, key="menu_charging_fee"):
            select_main_menu(MENU_CHARGING_FEE)

        # -------------------------------
        # 보조금 정책 상위 메뉴 + 하위 메뉴
        # -------------------------------
        subsidy_label = "▼ 보조금 정책" if st.session_state.subsidy_expanded else "▶ 보조금 정책"
        if st.button(subsidy_label, use_container_width=True, key="menu_subsidy"):
            toggle_subsidy_menu()

        if st.session_state.subsidy_expanded:
            st.markdown(
                """
                <div style="margin-left: 18px; margin-top: 2px; margin-bottom: 6px;"></div>
                """,
                unsafe_allow_html=True,
            )

            sub_col_1, sub_col_2 = st.columns([0.08, 0.92])

            with sub_col_2:
                if st.button("국고 보조금 정책", use_container_width=True, key="submenu_national_subsidy"):
                    select_subsidy_submenu(SUBMENU_NATIONAL_SUBSIDY)

                if st.button("지자체 보조금 정책", use_container_width=True, key="submenu_local_subsidy"):
                    select_subsidy_submenu(SUBMENU_LOCAL_SUBSIDY)

        # -------------------------------
        # 전기차 FAQ 상위 메뉴 + 하위 메뉴
        # -------------------------------
        faq_label = "▼ 전기차 FAQ" if st.session_state.faq_expanded else "▶ 전기차 FAQ"
        if st.button(faq_label, use_container_width=True, key="menu_ev_faq"):
            toggle_faq_menu()

        if st.session_state.faq_expanded:
            st.markdown(
                """
                <div style="margin-left: 18px; margin-top: 2px; margin-bottom: 6px;"></div>
                """,
                unsafe_allow_html=True,
            )

            faq_col_1, faq_col_2 = st.columns([0.08, 0.92])

            with faq_col_2:
                if st.button("브랜드별 전기차 FAQ", use_container_width=True, key="submenu_brand_faq"):
                    select_faq_submenu(SUBMENU_BRAND_FAQ)

                if st.button("서울시 전기차 FAQ", use_container_width=True, key="submenu_seoul_faq"):
                    select_faq_submenu(SUBMENU_SEOUL_FAQ)

        if st.button("뉴스 기사 분석", use_container_width=True, key="menu_news"):
            select_main_menu(MENU_NEWS)

    return st.session_state.current_menu, st.session_state.current_submenu


# ------------------------------------------------------------
# 메인 실행 함수
# ------------------------------------------------------------
# 이 함수는 Streamlit 앱의 진입점 역할을 합니다.
# 실제로는 아래 순서로 동작합니다.
#
# 1. 페이지 설정(title, icon, layout)
# 2. 사이드바 렌더링
# 3. 필요한 데이터 로딩
# 4. 현재 메뉴 상태에 따라 적절한 화면 렌더링 함수 호출
def main() -> None:
    """
    앱 전체를 실행하는 메인 함수입니다.
    """
    st.set_page_config(page_title="전기차 정보 포털", page_icon="⚡", layout="wide")

    st.title("전기차 정보 포털")

    current_menu, current_submenu = render_sidebar()
    dashboard_data = load_dashboard_data()

    if current_menu == MENU_REGION_EV:
        render_region_ev_page(dashboard_data["ev_registration_data"])

    elif current_menu == MENU_CHARGER:
        render_charger_page(dashboard_data["charger_operation_data"])

    elif current_menu == MENU_CHARGING_FEE:
        render_charging_fee_page(dashboard_data["charging_fee_data"])

    elif current_menu == MENU_SUBSIDY:
        if current_submenu == SUBMENU_NATIONAL_SUBSIDY:
            render_subsidy_page(dashboard_data["policy_data"])

        elif current_submenu == SUBMENU_LOCAL_SUBSIDY:
            render_local_subsidy_page(dashboard_data["local_subsidy_data"])

    elif current_menu == MENU_EV_FAQ:
        if current_submenu == SUBMENU_BRAND_FAQ:
            render_brand_faq_page(dashboard_data["brand_faq_data"])

        elif current_submenu == SUBMENU_SEOUL_FAQ:
            render_faq_page(dashboard_data["faq_data"])

    elif current_menu == MENU_NEWS:
        render_news_page(dashboard_data["news_keyword_data"])


# ------------------------------------------------------------
# 프로그램 시작 지점
# ------------------------------------------------------------
if __name__ == "__main__":
    main()