-- sql/view.sql

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