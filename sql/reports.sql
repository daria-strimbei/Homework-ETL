-- =========================================================
-- REPORT 1
-- What activities did each employee perform on each day?
-- This is the most direct report for the homework requirement:
-- activities by day, by employee.
-- =========================================================
SELECT
    d.full_date,
    e.employee_full_name,
    a.activity_category,
    a.activity_type,
    a.project_name,
    a.title,
    f.hours
FROM fact_employee_day f
JOIN dim_date d
    ON f.date_key = d.date_key
JOIN dim_employee e
    ON f.employee_key = e.employee_key
JOIN dim_activities a
    ON f.activity_key = a.activity_key
ORDER BY d.full_date, e.employee_full_name, a.activity_category;


-- =========================================================
-- REPORT 2
-- How many total hours did each employee work per day?
-- This shows daily workload by employee.
-- =========================================================
SELECT
    d.full_date,
    e.employee_full_name,
    SUM(f.hours) AS total_hours
FROM fact_employee_day f
JOIN dim_date d
    ON f.date_key = d.date_key
JOIN dim_employee e
    ON f.employee_key = e.employee_key
GROUP BY d.full_date, e.employee_full_name
ORDER BY d.full_date, e.employee_full_name;


-- =========================================================
-- REPORT 3
-- How many total hours were recorded for each activity category?
-- This shows time distribution across TIMESHEET, ABSENCE,
-- and CONFLUENCE.
-- =========================================================
SELECT
    a.activity_category,
    SUM(f.hours) AS total_hours
FROM fact_employee_day f
JOIN dim_activities a
    ON f.activity_key = a.activity_key
GROUP BY a.activity_category
ORDER BY total_hours DESC;


-- =========================================================
-- REPORT 4
-- How many total hours were recorded for each activity type?
-- This gives a more detailed breakdown inside each category,
-- for example work type, absence reason, or confluence type.
-- =========================================================
SELECT
    a.activity_category,
    a.activity_type,
    SUM(f.hours) AS total_hours
FROM fact_employee_day f
JOIN dim_activities a
    ON f.activity_key = a.activity_key
GROUP BY a.activity_category, a.activity_type
ORDER BY a.activity_category, total_hours DESC;


-- =========================================================
-- REPORT 5
-- How many hours did each employee spend in each activity category?
-- This helps compare employee time allocation across work,
-- absence, and confluence activities.
-- =========================================================
SELECT
    e.employee_full_name,
    a.activity_category,
    SUM(f.hours) AS total_hours
FROM fact_employee_day f
JOIN dim_employee e
    ON f.employee_key = e.employee_key
JOIN dim_activities a
    ON f.activity_key = a.activity_key
GROUP BY e.employee_full_name, a.activity_category
ORDER BY e.employee_full_name, a.activity_category;


-- =========================================================
-- REPORT 6
-- How many hours were recorded per project?
-- This report is mainly useful for TIMESHEET activities.
-- It shows which projects consumed the most work time.
-- =========================================================
SELECT
    a.project_name,
    SUM(f.hours) AS total_hours
FROM fact_employee_day f
JOIN dim_activities a
    ON f.activity_key = a.activity_key
WHERE a.activity_category = 'TIMESHEET'
  AND a.project_name IS NOT NULL
GROUP BY a.project_name
ORDER BY total_hours DESC;


-- =========================================================
-- REPORT 7
-- How many absence hours did each employee have?
-- This is useful for analyzing leave, sickness, or other
-- absence-related activity types.
-- =========================================================
SELECT
    e.employee_full_name,
    SUM(f.hours) AS absence_hours
FROM fact_employee_day f
JOIN dim_employee e
    ON f.employee_key = e.employee_key
JOIN dim_activities a
    ON f.activity_key = a.activity_key
WHERE a.activity_category = 'ABSENCE'
GROUP BY e.employee_full_name
ORDER BY absence_hours DESC;


-- =========================================================
-- REPORT 8
-- How many total hours were recorded by month and year?
-- This shows workload trends over time.
-- =========================================================
SELECT
    d.year_num,
    d.month_name,
    SUM(f.hours) AS total_hours
FROM fact_employee_day f
JOIN dim_date d
    ON f.date_key = d.date_key
GROUP BY d.year_num, d.month_name, d.month_number
ORDER BY d.year_num, d.month_number;