-- ============================================
-- view.sql
-- 조회 및 분석을 단순화하기 위한 View 정의 스크립트
-- 목적:
-- 1) 조인을 반복하지 않도록 조회용 View 생성
-- 2) 연도별 순증 집계 View 생성
-- 3) 연말 누적값 조회용 View 생성
-- ============================================

-- --------------------------------------------
-- 1. 월별 전기차 등록 현황 조회 View
-- 역할:
-- - ev_registration_monthly와 region_master를 조인한 결과를
--   재사용 가능한 형태로 제공
-- - 화면/분석 쿼리에서 매번 JOIN을 작성하지 않아도 됨
-- --------------------------------------------
CREATE OR REPLACE VIEW vw_ev_registration_monthly AS
SELECT
    e.id,
    e.base_ym,
    e.year_num,
    e.month_num,
    r.region_name,
    r.region_order,
    e.cumulative_count,
    e.monthly_increase,
    e.yoy_diff,
    e.share_pct,
    e.is_latest_ym
FROM ev_registration_monthly e
JOIN region_master r
  ON e.region_id = r.region_id;

-- --------------------------------------------
-- 2. 연도별 순증 집계 View
-- 역할:
-- - 월별 순증(monthly_increase)을 연도 단위로 합산
-- - 지역별/연도별 증가 추이 분석에 사용
-- --------------------------------------------
CREATE OR REPLACE VIEW vw_ev_yearly_increase AS
SELECT
    r.region_name,
    r.region_order,
    e.year_num,
    SUM(e.monthly_increase) AS yearly_increase
FROM ev_registration_monthly e
JOIN region_master r
  ON e.region_id = r.region_id
GROUP BY r.region_name, r.region_order, e.year_num;

-- --------------------------------------------
-- 3. 연말 누적값 View
-- 역할:
-- - 각 지역/연도별로 가장 마지막 월의 누적값만 추출
-- - 연도 말 기준 누적 보유 대수를 비교할 때 사용
-- 구현 포인트:
-- - ROW_NUMBER() 윈도우 함수를 사용하여
--   지역+연도별 최신 행 1개만 선택
-- --------------------------------------------
CREATE OR REPLACE VIEW vw_ev_year_end_cumulative AS
SELECT
    sub.region_name,
    sub.region_order,
    sub.year_num,
    sub.base_ym,
    sub.cumulative_count
FROM (
    SELECT
        r.region_name,
        r.region_order,
        e.year_num,
        e.base_ym,
        e.cumulative_count,
        ROW_NUMBER() OVER (
            PARTITION BY r.region_name, e.year_num
            ORDER BY e.base_ym DESC
        ) AS rn
    FROM ev_registration_monthly e
    JOIN region_master r
      ON e.region_id = r.region_id
) sub
WHERE sub.rn = 1;