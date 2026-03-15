-- sql/analysis.sql

-- 1. 최신월 기준 지역별 누적 등록 순위
SELECT
    region_name,
    cumulative_count
FROM vw_ev_registration_monthly
WHERE is_latest_ym = 'Y'
ORDER BY region_order;

-- 2. 합계 행의 월별 순증 확인
SELECT
    base_ym,
    cumulative_count,
    monthly_increase
FROM vw_ev_registration_monthly
WHERE region_name = '합계'
ORDER BY base_ym;

-- 3. 서울의 월별 순증 추이
SELECT
    base_ym,
    cumulative_count,
    monthly_increase,
    yoy_diff
FROM vw_ev_registration_monthly
WHERE region_name = '서울'
ORDER BY base_ym;

-- 4. 지역별 연도별 순증
SELECT
    region_name,
    year_num,
    yearly_increase
FROM vw_ev_yearly_increase
ORDER BY region_order, year_num;

-- 5. 최신월 기준 지역별 점유율
SELECT
    region_name,
    cumulative_count,
    share_pct
FROM vw_ev_registration_monthly
WHERE is_latest_ym = 'Y'
ORDER BY region_order;

-- 6. 특정 연도(예: 2025)의 지역별 순증
SELECT
    region_name,
    year_num,
    yearly_increase
FROM vw_ev_yearly_increase
WHERE year_num = 2025
ORDER BY region_order;

-- 7. 연도별 전국 순증
SELECT
    year_num,
    yearly_increase
FROM vw_ev_yearly_increase
WHERE region_name = '합계'
ORDER BY year_num;

-- 8. 연도별 말 기준 전국 누적값
SELECT
    year_num,
    base_ym,
    cumulative_count
FROM vw_ev_year_end_cumulative
WHERE region_name = '합계'
ORDER BY year_num;

-- 9. 지역별 최근 12개월 순증 합계
SELECT
    region_name,
    SUM(monthly_increase) AS last_12m_increase
FROM vw_ev_registration_monthly
WHERE base_ym >= DATE_SUB(
    (SELECT MAX(base_ym) FROM ev_registration_monthly),
    INTERVAL 11 MONTH
)
GROUP BY region_name, region_order
ORDER BY region_order;

-- 10. 합계 검증: latest 월 기준 지역합 vs 합계
SELECT
    SUM(CASE WHEN region_name <> '합계' THEN cumulative_count ELSE 0 END) AS sum_of_regions,
    MAX(CASE WHEN region_name = '합계' THEN cumulative_count END) AS total_row
FROM vw_ev_registration_monthly
WHERE is_latest_ym = 'Y';