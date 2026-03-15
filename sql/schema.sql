-- sql/schema.sql

-- 자동차등록현황 테이블 생성

CREATE TABLE IF NOT EXISTS region_master (
    region_id INT AUTO_INCREMENT PRIMARY KEY,
    region_name VARCHAR(20) NOT NULL UNIQUE,
    region_order INT NOT NULL
);

CREATE TABLE IF NOT EXISTS ev_registration_monthly (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    base_ym DATE NOT NULL COMMENT '기준년월(월초일 저장)',
    year_num SMALLINT NOT NULL,
    month_num TINYINT NOT NULL,
    region_id INT NOT NULL,
    cumulative_count INT NOT NULL COMMENT '월말 기준 누적 등록대수',
    monthly_increase INT NOT NULL COMMENT '전월 대비 순증',
    yoy_diff INT NULL COMMENT '전년 동월 대비 증가량',
    share_pct DECIMAL(10,4) NULL COMMENT '전국 합계 대비 점유율(%)',
    region_order INT NOT NULL,
    is_latest_ym CHAR(1) NOT NULL DEFAULT 'N',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_ev_reg UNIQUE (base_ym, region_id),
    CONSTRAINT fk_ev_reg_region FOREIGN KEY (region_id)
        REFERENCES region_master(region_id)
);

CREATE INDEX idx_ev_reg_base_ym
    ON ev_registration_monthly(base_ym);

CREATE INDEX idx_ev_reg_region_ym
    ON ev_registration_monthly(region_id, base_ym);

CREATE INDEX idx_ev_reg_year_region
    ON ev_registration_monthly(year_num, region_id);