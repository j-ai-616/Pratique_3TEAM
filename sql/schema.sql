# 1:N 비식별관계 / 독립 테이블 구성
# region → ev_registration, region → car_registration
# charger_station → charge_info
# vehicle → national_subsidy
# region + vehicle → local_subsidy
# policy_faq 독립 테이블
# national_subsidy.subsidy_amount 추가 반영
# charger_station은 region_id FK 없이 region_name 문자열 저장 방식 유지

-- --------------------------------------------------
-- DB 생성 및 선택
-- --------------------------------------------------
CREATE DATABASE IF NOT EXISTS car1_db
DEFAULT CHARACTER SET utf8mb4
DEFAULT COLLATE utf8mb4_general_ci;

USE car1_db;


-- --------------------------------------------------
-- 1. 지역
-- --------------------------------------------------
CREATE TABLE IF NOT EXISTS region (
    region_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '지역 PK',
    region_code VARCHAR(20) UNIQUE COMMENT '지역 코드',
    region_name VARCHAR(100) NOT NULL UNIQUE COMMENT '지역명',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시'
) COMMENT='지역 기준 정보';


-- --------------------------------------------------
-- 2. 차량
-- --------------------------------------------------
CREATE TABLE IF NOT EXISTS vehicle (
    vehicle_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '차량 PK',
    manufacturer VARCHAR(100) COMMENT '제조사',
    model_name VARCHAR(150) NOT NULL COMMENT '차종명',
    fuel_type VARCHAR(50) COMMENT '연료유형',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시'
) COMMENT='차량 기준 정보';


-- --------------------------------------------------
-- 3. 전기차 등록 현황
-- UK: (region_id, base_date)
-- --------------------------------------------------
CREATE TABLE IF NOT EXISTS ev_registration (
    ev_reg_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '전기차 등록 현황 PK',
    base_date DATE NOT NULL COMMENT '기준일',
    ev_count INT NOT NULL COMMENT '전기차 등록 대수',
    source_file VARCHAR(255) COMMENT '원본 파일명',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
    region_id INT NOT NULL COMMENT '지역 FK',

    CONSTRAINT fk_ev_registration_region
        FOREIGN KEY (region_id) REFERENCES region(region_id),

    CONSTRAINT uq_ev_registration_region_date
        UNIQUE (region_id, base_date)
) COMMENT='지역별 월별 전기차 등록 현황';


-- --------------------------------------------------
-- 4. 자동차 등록 현황
-- UK: (region_id, base_date)
-- --------------------------------------------------
CREATE TABLE IF NOT EXISTS car_registration (
    car_reg_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '자동차 등록 현황 PK',
    region_id INT NOT NULL COMMENT '지역 FK',
    base_date DATE NOT NULL COMMENT '기준일',
    total_car_count INT NOT NULL COMMENT '전체 자동차 등록 대수',
    source_file VARCHAR(255) COMMENT '원본 파일명',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',

    CONSTRAINT fk_car_registration_region
        FOREIGN KEY (region_id) REFERENCES region(region_id),

    CONSTRAINT uq_car_registration_region_date
        UNIQUE (region_id, base_date)
) COMMENT='지역별 월별 자동차 등록 현황';


-- --------------------------------------------------
-- 5. 충전소
-- region과는 FK 연결 없이 region_name 문자열 저장
-- --------------------------------------------------
CREATE TABLE IF NOT EXISTS charger_station (
    station_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '충전소 PK',
    station_source_id VARCHAR(100) UNIQUE COMMENT '원본 충전소 ID',
    station_name VARCHAR(255) NOT NULL COMMENT '충전소명',
    address VARCHAR(255) COMMENT '주소',
    address_detail VARCHAR(255) COMMENT '상세주소',
    region_name VARCHAR(100) COMMENT '지역명',
    latitude DECIMAL(10,7) COMMENT '위도',
    longitude DECIMAL(10,7) COMMENT '경도',
    operator_name VARCHAR(100) COMMENT '운영기관명',
    available_time VARCHAR(255) COMMENT '이용가능시간',
    phone VARCHAR(50) COMMENT '연락처',
    registered_at DATETIME COMMENT '등록일자',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시'
) COMMENT='충전소 정보';


-- --------------------------------------------------
-- 6. 충전기
-- --------------------------------------------------
CREATE TABLE IF NOT EXISTS charge_info (
    charger_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '충전기 PK',
    charger_source_id VARCHAR(100) UNIQUE COMMENT '원본 충전기 ID',
    charge_type VARCHAR(50) COMMENT '충전방식',
    status_name VARCHAR(100) COMMENT '상태명',
    operator_name VARCHAR(100) COMMENT '운영기관명',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
    station_id INT NOT NULL COMMENT '충전소 FK',

    CONSTRAINT fk_charge_info_station
        FOREIGN KEY (station_id) REFERENCES charger_station(station_id)
) COMMENT='충전기 정보';


-- --------------------------------------------------
-- 7. 국고 보조금
-- UK: (vehicle_id, subsidy_year)
-- --------------------------------------------------
CREATE TABLE IF NOT EXISTS national_subsidy (
    national_subsidy_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '국고보조금 PK',
    subsidy_year YEAR NOT NULL COMMENT '기준연도',
    subsidy_amount INT NOT NULL COMMENT '국고보조금 금액',
    note VARCHAR(255) COMMENT '비고',
    source_url VARCHAR(500) COMMENT '출처 URL',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
    vehicle_id INT NOT NULL COMMENT '차량 FK',

    CONSTRAINT fk_national_subsidy_vehicle
        FOREIGN KEY (vehicle_id) REFERENCES vehicle(vehicle_id),

    CONSTRAINT uq_national_subsidy_vehicle_year
        UNIQUE (vehicle_id, subsidy_year)
) COMMENT='차량별 국고 보조금';


-- --------------------------------------------------
-- 8. 지자체 보조금
-- UK: (region_id, vehicle_id, subsidy_year)
-- --------------------------------------------------
CREATE TABLE IF NOT EXISTS local_subsidy (
    local_subsidy_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '지자체보조금 PK',
    subsidy_year YEAR NOT NULL COMMENT '기준연도',
    subsidy_amount INT NOT NULL COMMENT '지자체 보조금 금액',
    note VARCHAR(255) COMMENT '비고',
    source_url VARCHAR(500) COMMENT '출처 URL',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
    region_id INT NOT NULL COMMENT '지역 FK',
    vehicle_id INT NOT NULL COMMENT '차량 FK',

    CONSTRAINT fk_local_subsidy_region
        FOREIGN KEY (region_id) REFERENCES region(region_id),

    CONSTRAINT fk_local_subsidy_vehicle
        FOREIGN KEY (vehicle_id) REFERENCES vehicle(vehicle_id),

    CONSTRAINT uq_local_subsidy_region_vehicle_year
        UNIQUE (region_id, vehicle_id, subsidy_year)
) COMMENT='지역별 차량별 지자체 보조금';


-- --------------------------------------------------
-- 9. 정책 FAQ
-- --------------------------------------------------
CREATE TABLE IF NOT EXISTS policy_faq (
    faq_id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'FAQ PK',
    category VARCHAR(100) COMMENT '카테고리',
    question TEXT NOT NULL COMMENT '질문',
    answer TEXT NOT NULL COMMENT '답변',
    source_url VARCHAR(500) COMMENT '출처 URL',
    base_date DATE COMMENT '기준일',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시'
) COMMENT='전기차 정책 FAQ';
