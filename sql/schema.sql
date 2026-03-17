-- ============================================
-- schema.sql
-- 전기차 등록 현황 저장용 테이블 생성 스크립트
-- 목적:
-- 1) 지역 기준 테이블(region_master) 생성
-- 2) 월별 전기차 등록 현황 테이블(ev_registration_monthly) 생성
-- 3) 무결성 제약조건 및 조회 성능 향상을 위한 인덱스 설정
-- ============================================

-- --------------------------------------------
-- 1. 지역 기준 테이블
-- 역할:
-- - 지역명과 지역 출력 순서를 관리하는 마스터 테이블
-- - 추후 사실상 차원 테이블(dimension table) 역할 수행
-- --------------------------------------------
CREATE TABLE IF NOT EXISTS region_master (
    region_id INT AUTO_INCREMENT PRIMARY KEY,   -- 지역 고유 PK
    region_name VARCHAR(20) NOT NULL UNIQUE,    -- 지역명 (중복 불가)
    region_order INT NOT NULL                   -- 화면/분석용 정렬 순서
);

-- --------------------------------------------
-- 2. 월별 전기차 등록 현황 테이블
-- 역할:
-- - 월별/지역별 누적 등록대수, 순증, 전년동월 차이 등을 저장
-- - 핵심 분석 테이블(fact table) 역할 수행
-- --------------------------------------------
CREATE TABLE IF NOT EXISTS ev_registration_monthly (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,          -- 적재용 PK
    base_ym DATE NOT NULL COMMENT '기준년월(월초일 저장)',   -- 예: 2025-01-01 형태로 월 기준 저장
    year_num SMALLINT NOT NULL,                    -- 연도 추출값
    month_num TINYINT NOT NULL,                    -- 월 추출값
    region_id INT NOT NULL,                        -- region_master FK
    cumulative_count INT NOT NULL COMMENT '월말 기준 누적 등록대수',
    monthly_increase INT NOT NULL COMMENT '전월 대비 순증',
    yoy_diff INT NULL COMMENT '전년 동월 대비 증가량',
    share_pct DECIMAL(10,4) NULL COMMENT '전국 합계 대비 점유율(%)',
    region_order INT NOT NULL,                     -- 조회 편의를 위한 정렬 순서
    is_latest_ym CHAR(1) NOT NULL DEFAULT 'N',    -- 최신월 여부 플래그
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,-- 적재 시각 기록

    -- 같은 월(base_ym)에 같은 지역(region_id)이 중복 적재되지 않도록 보장
    CONSTRAINT uq_ev_reg UNIQUE (base_ym, region_id),

    -- 지역 기준 테이블과의 참조 무결성 보장
    CONSTRAINT fk_ev_reg_region FOREIGN KEY (region_id)
        REFERENCES region_master(region_id)
);

-- --------------------------------------------
-- 3. 인덱스 생성
-- 역할:
-- - 월 기준 조회, 지역+월 조회, 연도+지역 조회 속도 개선
-- --------------------------------------------

-- 기준월 단독 검색 최적화
CREATE INDEX idx_ev_reg_base_ym
    ON ev_registration_monthly(base_ym);

-- 지역별 월 추이 조회 최적화
CREATE INDEX idx_ev_reg_region_ym
    ON ev_registration_monthly(region_id, base_ym);

-- 연도별 지역 집계 조회 최적화
CREATE INDEX idx_ev_reg_year_region
    ON ev_registration_monthly(year_num, region_id);