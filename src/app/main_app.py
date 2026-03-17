import os
import sys
import streamlit as st
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

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
from src.data.region_ev_section import render_region_ev_page
from src.data.charger_section import render_charger_page
from src.data.charging_fee_section import render_charging_fee_page
from src.data.subsidy_section import render_subsidy_page
from src.data.brand_faq_section import render_brand_faq_page
from src.data.faq_section import render_faq_page
from src.data.news_analysis_section import render_news_page
from src.data.local_subsidy_section import render_local_subsidy_page

MENU_REGION_EV = "지역별 전기차 등록 현황"
MENU_CHARGER = "전기차 충전소 정보"
MENU_CHARGING_FEE = "충전 요금 정보"
MENU_SUBSIDY = "보조금 정책"
SUBMENU_NATIONAL_SUBSIDY = "국고 보조금 정책"
SUBMENU_LOCAL_SUBSIDY = "지자체 보조금 정책"
MENU_EV_FAQ = "전기차 FAQ"
SUBMENU_BRAND_FAQ = "브랜드별 전기차 FAQ"
SUBMENU_SEOUL_FAQ = "서울시 전기차 FAQ"
MENU_NEWS = "뉴스 기사 분석"

@st.cache_data(show_spinner=False)
def load_dashboard_data():
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


def initialize_menu_state() -> None:
    if "current_menu" not in st.session_state:
        st.session_state.current_menu = MENU_REGION_EV
    if "current_submenu" not in st.session_state:
        st.session_state.current_submenu = None
    if "subsidy_expanded" not in st.session_state:
        st.session_state.subsidy_expanded = False
    if "faq_expanded" not in st.session_state:
        st.session_state.faq_expanded = False


def set_menu(menu_name: str, submenu_name: str | None = None):
    st.session_state.current_menu = menu_name
    st.session_state.current_submenu = submenu_name
    st.session_state.subsidy_expanded = menu_name == MENU_SUBSIDY
    st.session_state.faq_expanded = menu_name == MENU_EV_FAQ


def render_sidebar() -> None:
    st.sidebar.title("📘 EV 정보 포털")
    if st.sidebar.button(MENU_REGION_EV, use_container_width=True):
        set_menu(MENU_REGION_EV)
    if st.sidebar.button(MENU_CHARGER, use_container_width=True):
        set_menu(MENU_CHARGER)
    if st.sidebar.button(MENU_CHARGING_FEE, use_container_width=True):
        set_menu(MENU_CHARGING_FEE)

    subsidy_open = st.sidebar.checkbox(MENU_SUBSIDY, value=st.session_state.subsidy_expanded)
    st.session_state.subsidy_expanded = subsidy_open
    if subsidy_open:
        if st.sidebar.button(f"- {SUBMENU_NATIONAL_SUBSIDY}", use_container_width=True):
            set_menu(MENU_SUBSIDY, SUBMENU_NATIONAL_SUBSIDY)
        if st.sidebar.button(f"- {SUBMENU_LOCAL_SUBSIDY}", use_container_width=True):
            set_menu(MENU_SUBSIDY, SUBMENU_LOCAL_SUBSIDY)

    faq_open = st.sidebar.checkbox(MENU_EV_FAQ, value=st.session_state.faq_expanded)
    st.session_state.faq_expanded = faq_open
    if faq_open:
        if st.sidebar.button(f"- {SUBMENU_BRAND_FAQ}", use_container_width=True):
            set_menu(MENU_EV_FAQ, SUBMENU_BRAND_FAQ)
        if st.sidebar.button(f"- {SUBMENU_SEOUL_FAQ}", use_container_width=True):
            set_menu(MENU_EV_FAQ, SUBMENU_SEOUL_FAQ)

    if st.sidebar.button(MENU_NEWS, use_container_width=True):
        set_menu(MENU_NEWS)


def main():
    st.set_page_config(page_title="전기차 정보 포털", layout="wide")
    initialize_menu_state()
    render_sidebar()
    data = load_dashboard_data()

    current_menu = st.session_state.current_menu
    current_submenu = st.session_state.current_submenu

    if current_menu == MENU_REGION_EV:
        render_region_ev_page(data["ev_registration_data"])
    elif current_menu == MENU_CHARGER:
        render_charger_page(data["charger_operation_data"])
    elif current_menu == MENU_CHARGING_FEE:
        render_charging_fee_page(data["charging_fee_data"])
    elif current_menu == MENU_SUBSIDY and current_submenu == SUBMENU_NATIONAL_SUBSIDY:
        render_subsidy_page(data["policy_data"])
    elif current_menu == MENU_SUBSIDY and current_submenu == SUBMENU_LOCAL_SUBSIDY:
        render_local_subsidy_page(data["local_subsidy_data"])
    elif current_menu == MENU_EV_FAQ and current_submenu == SUBMENU_BRAND_FAQ:
        render_brand_faq_page(data["brand_faq_data"])
    elif current_menu == MENU_EV_FAQ and current_submenu == SUBMENU_SEOUL_FAQ:
        render_faq_page(data["faq_data"])
    elif current_menu == MENU_NEWS:
        render_news_page(data["news_keyword_data"])
    else:
        render_region_ev_page(data["ev_registration_data"])


if __name__ == "__main__":
    main()
