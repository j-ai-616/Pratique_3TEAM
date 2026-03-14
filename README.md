# 🚘 전기차 전환 시대, 지역별 전기차 이용 환경 분석 및 정보 제공 시스템

> 전기차 등록 현황, 충전소 인프라, 정책/FAQ 정보를 한곳에서 확인할 수 있는 데이터 기반 정보 제공 시스템  
> 본 문서는 프로젝트 진행 상황에 맞춰 지속적으로 업데이트됩니다.

<br>

## 📌 프로젝트 한눈에 보기

- **프로젝트명**: 전기차 전환 시대, 지역별 전기차 이용 환경 분석 및 정보 제공 시스템
- **진행 기간**: 2026.03.11 ~ 2026.03.18
- **팀명**: 이손신김 코딩전투 (feat. 이순신님)
- **핵심 목표**
  - 지역별 전기차 등록 현황 분석
  - 충전소 위치 및 충전 정보 제공
  - 전기차 보조금 및 정책 FAQ 제공
  - Streamlit 기반 통합 정보 서비스 구현

---

## 👥 팀 소개

### 1) 팀명
## 이손신김 코딩전투 (feat. 이순신님)

<p align="center">
  <img src="./docs/images/1_team_introduction.png" alt="team introduction" width="700">
</p>

### 2) 팀원 소개

<p align="center">
  <img src="./docs/images/7_together.png" alt="team members" width="700">
</p>

| 이름 | 한 줄 소개 | 희망 역할 |
|:---|:---|:---|
| 김혜지 장군 | 데이터 속에서 답을 찾는 걸 즐기려고 노력중입니다. | 자료조사 및 크롤링 |
| 손지은 장군 | 데이터에서 답을 SELECT하고, 성장의 기록을 커밋하고자 합니다. | 테이블/모델 설계, MySQL 저장 |
| 신혜지 장군 | 그냥 코딩이 재미있어 즐기고 있습니다. | 자료조사 및 크롤링 |
| 이건우 장군 | 데이터를 통해 스포츠를 정교하게 분석하고 싶습니다. | API 및 데이터 처리 |
| 이상현 장군 | 핵심과 원리, 기본기를 중요시합니다. | Streamlit 구현 및 DB 기본 구축 |

---

## 🤝 그라운드 룰

- 모든 팀원은 최소 1개 이상의 의견을 제시한다.
- 모르는 점이나 문제는 바로 공유하고 함께 해결한다.
- 작업 진행 상황과 주요 변경 사항은 디스코드에 간단히 공유한다.
- 작은 아이디어도 자유롭게 제안하고, 비판보다 해결 중심으로 소통한다.
- 마감 전에 최소 1회 이상 진행 상황을 함께 점검한다.

---

## 📖 프로젝트 개요

### 1) 프로젝트 주제
**전기차 전환 시대, 지역별 전기차 이용 환경 분석 및 정보 제공 시스템**

### 2) 프로젝트 배경

최근 탄소중립 정책과 친환경 교통수단 확대에 따라 전기차 보급은 빠르게 증가하고 있습니다.  
하지만 실제 이용자 입장에서는 **지역별 전기차 보급 수준**, **충전소 위치 및 이용 가능 여부**, **충전 요금**, **보조금 정책** 등의 정보가 여러 기관과 플랫폼에 분산되어 있어 필요한 정보를 한 번에 파악하기 어렵습니다.

특히 전기차 구매를 고려하거나 이미 운행 중인 사용자에게는 다음 정보가 중요한 의사결정 요소가 됩니다.

- 지역별 전기차 등록 현황
- 충전소 위치 및 충전 가능 여부
- 충전 요금 정보
- 보조금 및 정책 FAQ

본 프로젝트는 이러한 문제를 해결하기 위해,  
**전기차 등록 현황 데이터 + 충전소 정보 + 정책/FAQ 정보를 통합 제공하는 데이터 기반 정보 시스템**을 구축하는 것을 목표로 합니다.

---

## 🎯 프로젝트 목표

### 주요 목표
1. **지역별 전기차 등록 현황 분석**
   - 지역별 보급 수준과 변화 추이를 시각적으로 제공

2. **지도 기반 충전소 정보 제공**
   - 카카오맵 API를 활용하여 충전소 위치 시각화
   - 가능 시 충전 요금 및 충전 가능 여부 함께 제공

3. **전기차 정책 및 보조금 FAQ 제공**
   - 전기차 구매 및 이용에 필요한 정책 정보를 쉽게 조회 가능하도록 구성

### 확장 목표
- 전기차 vs 비전기차 보급 비율 비교
- 전기차 관련 기사 크롤링 및 키워드 분석

### 학습 목표
- 공공데이터 수집 및 전처리
- MySQL 기반 데이터베이스 설계 및 적재
- Streamlit 기반 데이터 서비스 구현
- 지도 API 연동 및 시각화 경험

---

## 🧩 주요 담당 업무 (R&R)

| 역할 | 담당자 | 담당 업무 | 사용 데이터 | 주요 산출물 |
|:---|:---|:---|:---|:---|
| 데이터 총괄 / 등록 현황 분석 | 신장군 | 지역별 전기차 등록 현황 수집, 정제, 기초 분석 | 전기차 현황 CSV, 자동차 등록현황 XLS/XLSX | 지역별 전기차 현황 테이블, 증감 추이 차트 |
| 소통 채널 / 지도 및 API 총괄 | 이장군1 | 노션·디스코드 관리, 카카오맵 및 데이터 API 연동 | 카카오맵 API, 공공 데이터 API | 지도 API 화면, 데이터 테이블 |
| FAQ / 크롤링 담당 | 김장군 | 차종별 FAQ 정리 및 정책/기사 크롤링 | 무공해차 통합 누리집 | FAQ 데이터셋, 기사 크롤링 결과 |
| 충전소 데이터 / DB / 백엔드 | 손장군 | MySQL 스키마 설계, 적재, 조회 쿼리 작성, 데이터 연결 | 팀 정제 데이터 전체 | `schema.sql`, 적재/조회 코드, ERD |
| Streamlit / 통합 담당 | 이장군2 | Streamlit UI 구성, 필터, 화면 통합 | DB 조회 결과 | 메인 대시보드, 검색/필터 UI |

---

## 🗂 프로젝트 구조

```bash
🚘 TeamProject01_car1/
├─ .env                         # API 키, DB 비밀번호 등 민감한 환경변수
├─ .env.example                 # .env 작성 예시 템플릿
├─ .gitignore                   # Git 추적 제외 파일 목록
├─ README.md                    # 프로젝트 소개 및 실행 가이드
├─ requirements.txt             # 프로젝트 의존성 패키지 목록
│
├─ data/
│  ├─ raw/                      # 원본 데이터 파일
│  └─ processed/                # 전처리 완료 데이터
│
├─ sql/
│  ├─ schema.sql                # MySQL 테이블 생성 SQL
│  ├─ view.sql                  # 조회용 View SQL
│  └─ analysis.sql              # 분석/검증용 SQL
│
├─ docs/
│  ├─ ERD.png                   # ERD 이미지
│  ├─ project_description.md    # 프로젝트 기획 문서
│  └─ images/                   # README용 이미지
│     ├─ 1_team_introduction.png
│     └─ 7_together.png
│
└─ src/
   ├─ app/
   │  └─ main_app.py            # Streamlit 메인 실행 파일
   │
   ├─ data/
   │  ├─ ev_registration.py     # 전기차 등록 현황 데이터 수집/로드
   │  ├─ charger_api.py         # 충전소/충전기 API 호출
   │  ├─ ev_policy_crawler.py   # 보조금/정책/FAQ 크롤링
   │  ├─ clean_ev_data.py       # 전기차 데이터 정제
   │  └─ region_processing.py   # 지역명 표준화 및 지역 컬럼 가공
   │
   ├─ db/
   │  ├─ db_connect.py          # MySQL 연결 설정
   │  ├─ insert_data.py         # 전처리 데이터 적재
   │  └─ query_data.py          # Streamlit 조회용 SQL 실행
   │
   ├─ map/
   │  ├─ kakao_map.py           # 카카오맵 시각화
   │  └─ map_service.py         # 카카오 REST API 검색/좌표 변환
   │
   ├─ config/
   │  └─ settings.py            # 환경변수 및 공통 설정
   │
   └─ utils/
      └─ helpers.py             # 공통 유틸 함수

## 🛠 기술 스택 및 협업 도구

<p>
  <img src="https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=Git&logoColor=white" alt="Git">
  <img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=GitHub&logoColor=white" alt="GitHub">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=Python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=MySQL&logoColor=white" alt="MySQL">
  <img src="https://img.shields.io/badge/Streamlit-FE4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit">
  <img src="https://img.shields.io/badge/Notion-000000?style=for-the-badge&logo=Notion&logoColor=white" alt="Notion">
  <img src="https://img.shields.io/badge/Google%20Drive-4285F4?style=for-the-badge&logo=GoogleDrive&logoColor=white" alt="Google Drive">
  <img src="https://img.shields.io/badge/VS%20Code-007ACC?style=for-the-badge&logo=visualstudiocode&logoColor=white" alt="VS Code">
</p>

---

## ✅ 요구사항 명세서

| No | 요구사항명 | 구현 여부 | 우선순위 | 상세 설명 | 비고 |
|:--:|:---|:---:|:---:|:---|:---|
| 1 | 지역별 전기차 등록 현황 제공 | 진행중 | 상 | 지역별 전기차 등록 데이터 수집 및 시각화 |  |
| 2 | 충전소 위치 조회 | 진행중 | 상 | 카카오맵 기반 충전소 위치 제공 |  |
| 3 | 충전기 상세 정보 제공 | 진행중 | 상 | 충전 가능 여부, 충전기 정보 제공 |  |
| 4 | 보조금/정책 FAQ 제공 | 진행중 | 상 | FAQ 및 정책 정보 조회 기능 구현 |  |
| 5 | 전기차 관련 기사 크롤링 | 예정 | 중 | 기사 데이터 수집 및 키워드 분석 | 확장 기능 |
| 6 | 전기차 vs 비전기차 비교 | 예정 | 중 | 비율 비교 시각화 | 확장 기능 |

---

## 🚀 실행 방법

~~~bash
# 1. 저장소 클론
git clone <repository_url>

# 2. 폴더 이동
cd TeamProject01_car1

# 3. 가상환경 생성 및 활성화
conda create -n car1_env python=3.12
conda activate car1_env

# 4. 패키지 설치
pip install -r requirements.txt

# 5. .env 파일 작성
# .env.example 참고하여 환경변수 설정

# 6. Streamlit 실행
streamlit run src/app/main_app.py
~~~

---

## 📌 향후 보완 예정

- README에 서비스 화면 캡처 추가
- ERD 및 데이터 흐름도 시각 자료 보강
- 주요 SQL / Python 처리 로직 요약 정리
- 배포 주소 및 시연 영상 추가

---

## 📂 문서 및 이미지

- [프로젝트 설명 문서](./docs/project_description.md)
- [ERD 이미지](./docs/ERD.png)

---

## ✨ 한 줄 정리

**전기차 이용자가 지역별 전기차 등록 현황, 충전소 정보, 정책 FAQ를 한 번에 확인할 수 있도록 돕는 통합 정보 제공 시스템입니다.**