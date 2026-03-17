# 기술 명세서 (Technical Specification)

> **전기차 전환 시대, 지역별 전기차 이용 환경 분석 및 정보 제공 시스템**
> 본 문서는 프로젝트의 기술적 설계와 구현 세부사항을 기록합니다.

---

## 1. 시스템 아키텍처

### 전체 데이터 흐름

| 단계 | 내용 |
|:---:|:---|
| **① 수집** | 공공데이터 CSV/XLS · 웹 크롤링 (FAQ/뉴스) · 카카오맵 REST API |
| **② 전처리** | `src/data/` — 정제, 지역명 표준화, 집계 |
| **③ 저장** | `data/processed/` CSV (기본) · MySQL DB (선택) |
| **④ 서비스** | Streamlit 대시보드 (`src/app/main_app.py`) |

### 데이터 로딩 전략 (Fallback 구조)

`src/db/query_data.py`는 아래 순서로 데이터를 로드합니다:

```
1순위: data/processed/ 디렉토리의 CSV/Excel 파일
2순위: MySQL DB 조회 (연결 설정된 경우)
3순위: 코드 내장 샘플 데이터 (Fallback)
```

→ DB 없이도 대시보드가 정상 동작하도록 설계된 **유연한 데이터 로딩 구조**입니다.

---

## 2. 기술 스택

| Python | MySQL | Github | Pandas | Matplotlib | Streamlit | Selenium |
|:------:|:-----:|:------:|:------:|:----------:|:---------:|:--------:|
| ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white) | ![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white) | ![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white) ![Git](https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white) | ![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white) | ![Matplotlib](https://img.shields.io/badge/Matplotlib-11557C?style=for-the-badge&logo=matplotlib&logoColor=white) | ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white) | ![Selenium](https://img.shields.io/badge/Selenium-43B02A?style=for-the-badge&logo=selenium&logoColor=white) |

### 상세 의존성

| 분류 | 라이브러리 | 용도 |
|:---|:---|:---|
| 웹 프레임워크 | streamlit 1.55.0 | 대시보드 UI |
| 데이터 처리 | pandas 2.3.3, numpy 2.4.3 | 데이터프레임 조작 |
| 시각화 | plotly 6.6.0, matplotlib 3.10.8, wordcloud 1.9.6 | 차트·워드클라우드 |
| 데이터베이스 | SQLAlchemy 2.0.48, PyMySQL 1.1.2 | MySQL ORM 연동 |
| 크롤링 | selenium 4.18.1, beautifulsoup4 4.12.3 | 웹 크롤링 |
| 자연어 처리 | konlpy 0.6.0 | 한국어 형태소 분석 |
| 파일 처리 | openpyxl, xlrd | Excel 파일 읽기 |
| 설정 관리 | python-dotenv | .env 환경변수 로드 |
| 지도 | 카카오맵 REST API + JavaScript SDK | 충전소 검색 및 지도 렌더링 |

---

## 3. 데이터베이스 설계

### ERD

https://github.com/SKNETWORKS-FAMILY-AICAMP/SKN28-1st-3TEAM/blob/main/docs/ERD.png

### 테이블 정의

#### region_master (지역 마스터)

```sql
region_id    INT AUTO_INCREMENT PRIMARY KEY  -- 지역 ID
region_name  VARCHAR(20) NOT NULL UNIQUE     -- 지역명 (17개 시도 + 합계)
region_order INT NOT NULL                    -- 화면 정렬 순서
```

#### ev_registration_monthly (월별 전기차 등록 현황)

```sql
id                BIGINT AUTO_INCREMENT PRIMARY KEY
base_ym           DATE          -- 기준년월 (월초일 저장, 예: 2024-01-01)
year_num          SMALLINT      -- 연도
month_num         TINYINT       -- 월
region_id         INT           -- [FK → region_master]
cumulative_count  INT           -- 월말 기준 누적 등록대수
monthly_increase  INT           -- 전월 대비 순증
yoy_diff          INT NULL      -- 전년 동월 대비 증가량
share_pct         DECIMAL(10,4) -- 전국 합계 대비 점유율(%)
is_latest_ym      CHAR(1)       -- 최신월 여부 (Y/N)
created_at        TIMESTAMP     -- 적재 일시
```

**인덱스 설계:**
- `idx_ev_reg_base_ym` — 기준년월 기준 빠른 조회
- `idx_ev_reg_region_ym` — 지역 + 기준년월 복합 인덱스
- `idx_ev_reg_year_region` — 연도 + 지역 복합 인덱스

### View 정의

| View명 | 목적 |
|:---|:---|
| `vw_ev_registration_monthly` | 지역명 포함 월별 등록 현황 (region_master JOIN) |
| `vw_ev_yearly_increase` | 지역별 연도별 순증 합계 (GROUP BY 연도·지역) |
| `vw_ev_year_end_cumulative` | 연말 기준 지역별 누적 등록대수 (ROW_NUMBER 윈도우 함수) |

---

## 4. 모듈별 상세 설명

### src/app/

| 파일 | 역할 |
|:---|:---|
| `main_app.py` | Streamlit 진입점. 사이드바 네비게이션 구성, 7개 메뉴 라우팅 |

### src/data/

| 파일 | 역할 |
|:---|:---|
| `clean_ev_data.py` | 공공데이터 XLS → wide/long 형식 CSV로 변환·정제 |
| `region_processing.py` | 소스별 지역명 표준화 (예: "경기도" → "경기"), 정렬 순서 매핑 |
| `region_ev_analysis.py` | 전년 대비 증감, 점유율, 지역 순위 등 분석 로직 |
| `region_ev_section.py` | 지역별 전기차 현황 탭 UI 렌더링 |
| `charger_access_analysis.py` | 충전소 데이터 필터링, 요약, 지도용 데이터 변환 |
| `charger_section.py` | 충전소 탭 UI 렌더링 |
| `charging_fee_section.py` | 충전 요금표 + 비용 계산기 UI |
| `subsidy_section.py` | 보조금 정책 탭 UI (차종별 필터) |
| `faq_section.py` | 서울시 FAQ 탭 UI (카테고리 필터) |
| `brand_faq_section.py` | 브랜드별 FAQ 탭 UI |
| `news_analysis_section.py` | 뉴스 키워드 분석 + 워드클라우드 UI |

### src/db/

| 파일 | 역할 |
|:---|:---|
| `db_connect.py` | SQLAlchemy 엔진 생성 (.env 기반 MySQL 연결) |
| `insert_data.py` | 전처리 CSV → MySQL ETL 파이프라인 |
| `query_data.py` | 통합 데이터 로딩 허브 (CSV 우선 → DB → Fallback) |

### src/map/

| 파일 | 역할 |
|:---|:---|
| `map_service.py` | 카카오맵 REST API 호출 (키워드 기반 충전소 검색) |
| `kakao_map.py` | 카카오맵 JavaScript SDK HTML 컴포넌트 생성 (Streamlit 임베딩) |

### src/config/ & src/utils/

| 파일 | 역할 |
|:---|:---|
| `settings.py` | .env 파일 로드, 카카오 API 키 노출 |
| `helpers.py` | 숫자 포맷팅, 지역명 매칭 등 공통 유틸 함수 |

---

## 5. 카카오맵 API 연동 방식

```
사용자 지역 입력
    ↓
map_service.py → 카카오맵 REST API (키워드 검색)
    ↓
JSON 응답 파싱 (장소명, 주소, 위·경도, 전화번호)
    ↓
kakao_map.py → JavaScript SDK HTML 생성
    ↓
streamlit.components.v1.html() 로 지도 임베딩
```

- **REST API**: 장소 검색 (서버 사이드) — `KAKAO_REST_API_KEY` 사용
- **JavaScript SDK**: 지도 렌더링 (클라이언트 사이드) — `KAKAO_JAVASCRIPT_KEY` 사용

---

## 6. 데이터 전처리 파이프라인

```
data/raw/ev_registration/*.xls
    ↓ clean_ev_data.py
    ├─ ev_registration_monthly_wide.csv   (지역 × 연월 피벗 형태)
    └─ ev_registration_monthly_long.csv   (DB 적재용 Long 형태)
              ↓ insert_data.py
         MySQL ev_registration_monthly 테이블
```

**지역명 표준화 흐름:**
- 원본에는 "서울특별시", "경기도" 등 다양한 표기 존재
- `region_processing.py`에서 모든 소스의 지역명을 17개 표준 시도명으로 통일

---

## 7. 데이터 출처

| 데이터 | 출처 | 수집 방법 |
|:---|:---|:---|
| 전기차 등록 현황 | 국토교통부 자동차등록현황 통계 | 공공데이터 XLS 다운로드 |
| 충전소 위치/운영 정보 | 한국전력공사, 한국환경공단 | 공공데이터 CSV 다운로드 |
| 충전소 실시간 검색 | 카카오맵 REST API | API 호출 |
| 국고 보조금 기준표 | 무공해차 통합누리집 | XLSX 다운로드 (2026년 기준) |
| 서울시 전기차 FAQ | 서울시 전기차 충전 인프라 포털 | Selenium 웹 크롤링 |
| 뉴스 키워드 분석 | 네이버 뉴스 "전기차 보조금" | BeautifulSoup 크롤링 |

---

## 8. 환경 설정 및 실행 가이드

### 사전 요구사항

- Python 3.12
- MySQL 8.x (선택 — 없어도 CSV 기반으로 동작)
- 카카오 개발자 계정 (REST API 키 + JavaScript 키)

### 설치

```bash
# 1. 가상환경 생성
conda create -n car1_env python=3.12
conda activate car1_env

# 2. 패키지 설치
pip install -r requirements.txt

# 3. 환경변수 설정
cp .env.example .env
# .env 파일에 아래 항목 입력
# KAKAO_REST_API_KEY=...
# KAKAO_JAVASCRIPT_KEY=...
# MYSQL_USER=...
# MYSQL_PASSWORD=...
# MYSQL_HOST=localhost
# MYSQL_PORT=3306
# MYSQL_DATABASE=car1_db
```

### MySQL 연동 (선택)

```bash
# DB 생성
mysql -u root -p -e "CREATE DATABASE car1_db CHARACTER SET utf8mb4;"

# 테이블 및 View 생성
mysql -u root -p car1_db < sql/schema.sql
mysql -u root -p car1_db < sql/view.sql

# 데이터 적재
python -m src.db.insert_data
```

### 실행

```bash
streamlit run src/app/main_app.py
```
