-- ============================================
-- analysis.sql
-- 발표/검증/분석용 조회 SQL 모음
-- 목적:
-- - View를 활용하여 다양한 분석 결과를 빠르게 확인
-- - 화면 구성 전 검증용 쿼리로도 사용 가능
-- ============================================

-- 1. 최신월 기준 지역별 누적 등록 순위
-- 최신월 데이터만 필터링하여 지역별 누적 등록대수를 조회
SELECT
    region_name,
    cumulative_count
FROM vw_ev_registration_monthly
WHERE is_latest_ym = 'Y'
ORDER BY region_order;

-- 2. 전국 합계 행의 월별 순증 확인
-- '합계' 지역만 추출하여 전국 단위 월별 증가 추이를 확인
SELECT
    base_ym,
    cumulative_count,
    monthly_increase
FROM vw_ev_registration_monthly
WHERE region_name = '합계'
ORDER BY base_ym;

-- 3. 서울의 월별 순증 추이
-- 서울 지역만 별도로 추출하여 누적/순증/전년동월차를 함께 확인
SELECT
    base_ym,
    cumulative_count,
    monthly_increase,
    yoy_diff
FROM vw_ev_registration_monthly
WHERE region_name = '서울'
ORDER BY base_ym;

-- 4. 지역별 연도별 순증
-- 연도별 순증 View를 이용한 기본 집계 조회
SELECT
    region_name,
    year_num,
    yearly_increase
FROM vw_ev_yearly_increase
ORDER BY region_order, year_num;

-- 5. 최신월 기준 지역별 점유율
-- 최신월에 각 지역이 전국에서 차지하는 비중을 조회
SELECT
    region_name,
    cumulative_count,
    share_pct
FROM vw_ev_registration_monthly
WHERE is_latest_ym = 'Y'
ORDER BY region_order;

-- 6. 특정 연도(예: 2025)의 지역별 순증
-- 연도 필터를 통해 특정 시점의 지역별 증가 비교 가능
SELECT
    region_name,
    year_num,
    yearly_increase
FROM vw_ev_yearly_increase
WHERE year_num = 2025
ORDER BY region_order;

-- 7. 연도별 전국 순증
-- 합계 지역만 사용해 전국 단위 연도별 증가량을 확인
SELECT
    year_num,
    yearly_increase
FROM vw_ev_yearly_increase
WHERE region_name = '합계'
ORDER BY year_num;

-- 8. 연도별 말 기준 전국 누적값
-- 각 연도 말의 전국 누적 등록대수를 확인
SELECT
    year_num,
    base_ym,
    cumulative_count
FROM vw_ev_year_end_cumulative
WHERE region_name = '합계'
ORDER BY year_num;

-- 9. 지역별 최근 12개월 순증 합계
-- 최신 기준월로부터 12개월 범위를 계산해 최근 1년 증가량을 집계
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

-- 10. 합계 검증: 지역 합과 합계 행이 일치하는지 확인
-- 데이터 품질 검증용 쿼리
SELECT
    SUM(CASE WHEN region_name <> '합계' THEN cumulative_count ELSE 0 END) AS sum_of_regions,
    MAX(CASE WHEN region_name = '합계' THEN cumulative_count END) AS total_row
FROM vw_ev_registration_monthly
WHERE is_latest_ym = 'Y';