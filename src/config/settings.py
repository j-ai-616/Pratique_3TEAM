import os
from pathlib import Path

from dotenv import load_dotenv
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT_DIR / ".env"

load_dotenv(ENV_PATH)


def _get_secret(key: str, default: str = "") -> str:
    try:
        value = st.secrets.get(key, default)
        if value is not None and str(value).strip() != "":
            return str(value).strip()
    except Exception:
        pass

    return os.getenv(key, default).strip()


def get_mysql_config() -> dict:
    try:
        mysql_section = st.secrets.get("mysql", {})
        if mysql_section:
            return {
                "user": str(mysql_section.get("user", "")).strip(),
                "password": str(mysql_section.get("password", "")).strip(),
                "host": str(mysql_section.get("host", "127.0.0.1")).strip(),
                "port": str(mysql_section.get("port", "3306")).strip(),
                "database": str(mysql_section.get("database", "")).strip(),
            }
    except Exception:
        pass

    return {
        "user": os.getenv("MYSQL_USER", "").strip(),
        "password": os.getenv("MYSQL_PASSWORD", "").strip(),
        "host": os.getenv("MYSQL_HOST", "127.0.0.1").strip(),
        "port": os.getenv("MYSQL_PORT", "3306").strip(),
        "database": os.getenv("MYSQL_DATABASE", "").strip(),
    }


KAKAO_REST_API_KEY = _get_secret("KAKAO_REST_API_KEY")
KAKAO_JAVASCRIPT_KEY = _get_secret("KAKAO_JAVASCRIPT_KEY")
NAVER_CLIENT_ID = _get_secret("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = _get_secret("NAVER_CLIENT_SECRET")
