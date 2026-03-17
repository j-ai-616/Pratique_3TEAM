import html

# 이 코드는 운영체제(OS)와 관련된 기능을 사용하기 위해 불러옵니다.
# 주로 파일 경로를 합치거나, 현재 파일 위치를 기준으로 상위 폴더 경로를 찾을 때 사용합니다.
import os

# 이 코드는 파이썬이 모듈(다른 .py 파일들)을 찾는 경로(sys.path)를 수정할 때 사용합니다.
# 프로젝트 루트 경로를 등록해서 src 아래 파일들을 import 가능하게 만드는 데 필요합니다.
import sys


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
# 외부 라이브러리 import
# ------------------------------------------------------------
# pandas는 표 형태 데이터(DataFrame)를 처리하는 데 사용됩니다.
# 현재 main_app.py 내부에서 직접 많은 연산을 하지는 않지만,
# 다른 데이터 구조와의 호환 및 향후 확장성을 위해 import 되어 있습니다.
import pandas as pd

# streamlit은 웹 대시보드/앱을 빠르게 만들기 위한 라이브러리입니다.
# 이 프로젝트의 화면 구성, 사이드바, 버튼, 표 출력 등을 담당합니다.
import streamlit as st


# ------------------------------------------------------------
# 프로젝트 설정값 import
# ------------------------------------------------------------
# settings.py 안에 저장된 카카오 API 관련 설정값입니다.
# 현재 main_app.py 내부에서 직접 사용되지는 않지만,
# 프로젝트 전체 설정과의 일관성을 위해 import 되어 있습니다.
# 추후 지도, 검색, 위치 관련 기능을 여기서 직접 사용할 가능성도 있습니다.
from src.config.settings import KAKAO_REST_API_KEY, KAKAO_JAVASCRIPT_KEY


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
# 기존 subsidy_section.py는 국고 보조금 정책 페이지 역할을 담당합니다.
from src.data.subsidy_section import render_subsidy_page

# 5번 메뉴: 브랜드별 전기차 FAQ 페이지 렌더링 함수
from src.data.brand_faq_section import render_brand_faq_page

# 6번 메뉴: 서울시 전기차 FAQ 페이지 렌더링 함수
from src.data.faq_section import render_faq_page

# 7번 메뉴: 뉴스 기사 분석 페이지 렌더링 함수
from src.data.news_analysis_section import render_news_page

# 4-2번 하위 메뉴: 지자체 보조금 정책 페이지 렌더링 함수
# local_subsidy_section.py는 지역별 지자체 보조금 정보를 보여주는 별도 페이지입니다.
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
# - current_submenu: 현재 화면에 렌더링 중인 하위 메뉴(보조금 정책 안에서만 사용)
# - subsidy_expanded: 보조금 정책 하위 메뉴가 펼쳐져 있는지 여부
def initialize_menu_state() -> None:
    """
    사이드바 메뉴 상태를 초기화합니다.

    초기 상태:
    - current_menu: 지역별 전기차 등록 현황
    - current_submenu: 없음
    - subsidy_expanded: 접힌 상태(False)
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
# 3. 실제 보조금 화면 렌더링은
#    - 국고 보조금 정책
#    - 지자체 보조금 정책
#    하위 메뉴를 눌렀을 때만 발생합니다.
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

        # 다른 일반 메뉴로 이동하면 하위 트리 메뉴들은 접어줍니다.
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
    # 브라우저 탭 제목, 파비콘, 레이아웃 설정
    st.set_page_config(page_title="전기차 정보 포털", page_icon="⚡", layout="wide")

    # 메인 페이지 상단 제목
    st.title("전기차 정보 포털")

    # 현재 선택된 메뉴/하위 메뉴 상태를 받아옵니다.
    current_menu, current_submenu = render_sidebar()

    # 전체 페이지에서 사용할 데이터를 한 번에 로딩합니다.
    dashboard_data = load_dashboard_data()

    # --------------------------------------------------------
    # 현재 메뉴 상태에 따라 적절한 페이지를 렌더링합니다.
    # --------------------------------------------------------
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

        else:
            pass

    elif current_menu == MENU_EV_FAQ:
        if current_submenu == SUBMENU_BRAND_FAQ:
            render_brand_faq_page(dashboard_data["brand_faq_data"])

        elif current_submenu == SUBMENU_SEOUL_FAQ:
            render_faq_page(dashboard_data["faq_data"])

        else:
            pass

    elif current_menu == MENU_NEWS:
        render_news_page(dashboard_data["news_keyword_data"])


# ------------------------------------------------------------
# 프로그램 시작 지점
# ------------------------------------------------------------
# 파이썬 파일이 직접 실행될 때만 main()을 호출합니다.
# 다른 파일에서 import 할 때는 main()이 자동 실행되지 않습니다.
if __name__ == "__main__":
    main()


# ============================================================
# [스크립트 하단 설명]
# ============================================================
#
# 1. 이 페이지(main_app.py)의 역할
# ------------------------------------------------------------
# 이 파일은 전기차 정보 포털 앱 전체의 "메인 컨트롤러" 역할을 합니다.
# 쉽게 말해:
# - 왼쪽 사이드바 메뉴를 만들고
# - 어떤 데이터를 불러올지 정하고
# - 현재 어떤 페이지를 화면에 보여줄지 결정하는
# 앱의 중심 파일입니다.
#
# 이 파일 자체는 각 메뉴의 상세 화면을 직접 만들기보다는,
# 다른 전담 스크립트들을 불러와서 연결해주는 역할에 집중하고 있습니다.
#
#
# 2. 이 페이지에서 제공하는 기능
# ------------------------------------------------------------
# 현재 이 메인 앱은 아래 기능들을 제공합니다.
#
# (1) 지역별 전기차 등록 현황 조회
#     - 지역별 등록 대수 관련 통계/표/시각화 페이지 출력
#
# (2) 전기차 충전소 정보 조회
#     - 충전소 위치, 운영 여부, 충전 가능 정보 등의 화면 출력
#
# (3) 충전 요금 정보 조회
#     - 충전 요금 관련 데이터 기반 화면 출력
#
# (4) 보조금 정책 조회
#     - 상위 메뉴는 단순 펼침/접힘 역할만 수행
#     - 하위 메뉴:
#         ① 국고 보조금 정책
#         ② 지자체 보조금 정책
#
# (5) 브랜드별 전기차 FAQ 조회
#     - 브랜드/차종 관련 FAQ 화면 출력
#
# (6) 서울시 전기차 FAQ 조회
#     - 서울시 전기차 정책/민원/안내 관련 FAQ 출력
#
# (7) 뉴스 기사 분석
#     - 뉴스 키워드 분석 또는 기사 기반 요약/분석 화면 출력
#
#
# 3. 연동되는 주요 스크립트들
# ------------------------------------------------------------
# 이 파일은 크게 두 종류의 스크립트와 연결됩니다.
#
# [A] 데이터 로딩 스크립트
#     src/db/query_data.py
#
#     여기에는 실제 엑셀, CSV, DB, 전처리 데이터 등을 읽어오는 함수들이 들어 있습니다.
#     main_app.py는 이 함수들을 호출해서
#     각 페이지에 전달할 DataFrame(데이터 표)을 준비합니다.
#
#     예:
#     - load_ev_registration_data()
#     - load_charger_operation_data()
#     - load_charging_fee_data()
#     - load_policy_data()
#     - load_local_subsidy_data()
#     - load_faq_data()
#     - load_news_keyword_data()
#     - load_brand_faq_data()
#
#
# [B] 페이지 렌더링 스크립트
#     src/data/ 아래의 각 section 파일들
#
#     이 파일들은 “받아온 데이터를 화면에 어떻게 보여줄지”를 담당합니다.
#
#     예:
#     - region_ev_section.py
#         → 지역별 전기차 등록 현황 페이지 구성
#
#     - charger_section.py
#         → 충전소 정보 페이지 구성
#
#     - charging_fee_section.py
#         → 충전 요금 페이지 구성
#
#     - subsidy_section.py
#         → 국고 보조금 정책 페이지 구성
#
#     - local_subsidy_section.py
#         → 지자체 보조금 정책 페이지 구성
#
#     - brand_faq_section.py
#         → 브랜드별 FAQ 페이지 구성
#
#     - faq_section.py
#         → 서울시 전기차 FAQ 페이지 구성
#
#     - news_analysis_section.py
#         → 뉴스 기사 분석 페이지 구성
#
#
# 4. 전체 동작 흐름
# ------------------------------------------------------------
# 이 앱은 대략 다음 순서로 동작합니다.
#
# [1] 앱 시작
#     ↓
#     main() 함수 실행
#
# [2] 페이지 설정
#     ↓
#     st.set_page_config() 로 제목, 아이콘, 레이아웃 설정
#
# [3] 사이드바 렌더링
#     ↓
#     render_sidebar() 실행
#     - 메뉴 버튼 출력
#     - 보조금 정책 하위 메뉴 펼침/접힘 처리
#     - session_state에 현재 선택 상태 저장
#
# [4] 데이터 로딩
#     ↓
#     load_dashboard_data() 실행
#     - query_data.py의 함수들을 호출
#     - 필요한 DataFrame들을 한 번에 딕셔너리로 준비
#
# [5] 선택된 메뉴 판별
#     ↓
#     current_menu / current_submenu 값을 기준으로
#     어떤 페이지를 출력할지 결정
#
# [6] 실제 페이지 렌더링
#     ↓
#     예를 들어 current_menu == MENU_CHARGER 이면
#     render_charger_page(...) 호출
#
#     current_menu == MENU_SUBSIDY 인 경우:
#     - current_submenu == 국고 보조금 정책
#         → render_subsidy_page(...)
#     - current_submenu == 지자체 보조금 정책
#         → render_local_subsidy_page(...)
#
#
# 5. 보조금 정책 메뉴의 특별한 동작 방식
# ------------------------------------------------------------
# 이 앱에서 "보조금 정책"은 일반 메뉴와 다르게 동작합니다.
#
# 일반 메뉴:
# - 버튼을 클릭하면 바로 해당 페이지로 이동
#
# 보조금 정책:
# - 상위 메뉴 버튼은 페이지 이동용이 아니라
#   하위 메뉴(국고/지자체)를 펼치고 접는 역할만 함
#
# 즉,
# - "보조금 정책" 클릭
#     → 하위 메뉴 노출/숨김
#
# - "국고 보조금 정책" 클릭
#     → subsidy_section.py 화면 렌더링
#
# - "지자체 보조금 정책" 클릭
#     → local_subsidy_section.py 화면 렌더링
#
# 이 방식으로 구현한 이유는
# 보조금 정책이 하나의 단일 페이지가 아니라
# 두 개의 하위 정책 페이지를 묶는 부모 메뉴 역할이기 때문입니다.
#
#
# 6. 유지보수 관점에서 이 파일의 장점
# ------------------------------------------------------------
# 이 main_app.py는 다음 장점을 가집니다.
#
# (1) 역할 분리
#     - 데이터 로딩은 query_data.py
#     - 화면 렌더링은 section 파일들
#     - 메뉴 제어와 연결은 main_app.py
#
# (2) 확장 용이
#     - 새 메뉴를 추가하려면
#       ① 데이터 로더 추가
#       ② section 파일 추가
#       ③ main_app.py에 메뉴와 분기 추가
#       순서로 쉽게 확장 가능
#
# (3) 유지보수 편의성
#     - 메뉴명이 상수로 관리되어 오타 가능성 감소
#     - session_state 기반이라 사용자 메뉴 상태 유지 가능
#     - cache_data 덕분에 반복 로딩 비용 감소
#
#
# 7. 추가 개선 가능 포인트
# ------------------------------------------------------------
# 향후 개선할 수 있는 부분은 다음과 같습니다.
#
# (1) 사이드바 선택 메뉴 강조 스타일 개선
#     - 현재는 버튼 기반 메뉴이므로 CSS를 추가하면 더 자연스럽게 꾸밀 수 있음
#
# (2) 부모 메뉴 클릭 시 “기존 화면 유지” 로직 강화
#     - 현재 구조에서는 보조금 정책 부모 클릭 시
#       current_menu를 변경하지 않는 방식으로 처리하면 더 자연스러움
#
# (3) 공통 레이아웃 컴포넌트 분리
#     - 사이드바 메뉴 구성 자체를 별도 ui/sidebar.py 로 분리 가능
#
# (4) 로깅 및 예외 처리 강화
#     - 특정 데이터 파일이 없거나 비정상일 때 사용자 안내 메시지 개선 가능
#
# ============================================================