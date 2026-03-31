-- =========================================================
-- INSERT DATA INTO DIM_DATE
-- =========================================================

INSERT INTO dim_date VALUES (20240501, DATE '2024-05-01', 1, 'Wednesday', 5, 'May', 2, 2024);
INSERT INTO dim_date VALUES (20240502, DATE '2024-05-02', 2, 'Thursday', 5, 'May', 2, 2024);
INSERT INTO dim_date VALUES (20240503, DATE '2024-05-03', 3, 'Friday', 5, 'May', 2, 2024);

-- =========================================================
-- INSERT DATA INTO DIM_EMPLOYEE
-- =========================================================

INSERT INTO dim_employee (employee_id, employee_email, employee_full_name, job_title, department_name)
VALUES (101, 'john.doe@email.com', 'John Doe', 'Developer', 'IT');

INSERT INTO dim_employee (employee_id, employee_email, employee_full_name, job_title, department_name)
VALUES (102, 'jane.smith@email.com', 'Jane Smith', 'Analyst', 'Finance');

-- =========================================================
-- INSERT DATA INTO DIM_ACTIVITIES
-- =========================================================

-- TIMESHEET
INSERT INTO dim_activities (activity_category, activity_type, project_id, project_name, title)
VALUES ('TIMESHEET', 'Development', 1, 'Payroll System', NULL);

INSERT INTO dim_activities (activity_category, activity_type, project_id, project_name, title)
VALUES ('TIMESHEET', 'Testing', 2, 'HR System', NULL);

-- ABSENCE
INSERT INTO dim_activities (activity_category, activity_type)
VALUES ('ABSENCE', 'Sick Leave');

INSERT INTO dim_activities (activity_category, activity_type)
VALUES ('ABSENCE', 'Vacation');

-- CONFLUENCE
INSERT INTO dim_activities (activity_category, activity_type, title)
VALUES ('CONFLUENCE', 'Documentation', 'Update Wiki');

INSERT INTO dim_activities (activity_category, activity_type, title)
VALUES ('CONFLUENCE', 'Meeting Notes', 'Sprint Meeting');

-- =========================================================
-- INSERT DATA INTO FACT TABLE
-- =========================================================

-- Use subqueries so it works regardless of generated IDs

-- John Doe
INSERT INTO fact_employee_day (date_key, employee_key, activity_key, hours)
SELECT 20240501, e.employee_key, a.activity_key, 8
FROM dim_employee e, dim_activities a
WHERE e.employee_id = 101
  AND a.activity_type = 'Development';

INSERT INTO fact_employee_day (date_key, employee_key, activity_key, hours)
SELECT 20240502, e.employee_key, a.activity_key, 8
FROM dim_employee e, dim_activities a
WHERE e.employee_id = 101
  AND a.activity_type = 'Sick Leave';

INSERT INTO fact_employee_day (date_key, employee_key, activity_key, hours)
SELECT 20240503, e.employee_key, a.activity_key, 2
FROM dim_employee e, dim_activities a
WHERE e.employee_id = 101
  AND a.activity_type = 'Documentation';

-- Jane Smith
INSERT INTO fact_employee_day (date_key, employee_key, activity_key, hours)
SELECT 20240501, e.employee_key, a.activity_key, 6
FROM dim_employee e, dim_activities a
WHERE e.employee_id = 102
  AND a.activity_type = 'Testing';

INSERT INTO fact_employee_day (date_key, employee_key, activity_key, hours)
SELECT 20240502, e.employee_key, a.activity_key, 8
FROM dim_employee e, dim_activities a
WHERE e.employee_id = 102
  AND a.activity_type = 'Vacation';

INSERT INTO fact_employee_day (date_key, employee_key, activity_key, hours)
SELECT 20240503, e.employee_key, a.activity_key, 3
FROM dim_employee e, dim_activities a
WHERE e.employee_id = 102
  AND a.activity_type = 'Meeting Notes';

-- =========================================================
-- QUICK TEST
-- =========================================================

SELECT COUNT(*) AS total_rows FROM fact_employee_day;