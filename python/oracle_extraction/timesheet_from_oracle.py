import pandas as pd
import oracledb
from pathlib import Path

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

connection = oracledb.connect(
    user="hr",
    password="1234",
    host="localhost",
    port=1521,
    service_name="XEPDB1"
)

print("Connected!")

# 1. Extract TS_TIMESHEETS
timesheets_query = """
SELECT
    ID,
    EMPLOYEE_ID,
    WEEK_START_DATE,
    WEEK_END_DATE
FROM hr.TS_TIMESHEETS
"""

timesheets_df = pd.read_sql(timesheets_query, con=connection)
timesheets_df.to_csv(RAW_DIR / "timesheets.csv", index=False)
print("timesheets.csv extracted")

# 2. Extract TS_TIMESHEET_ENTRIES
entries_query = """
SELECT
    TIMESHEET_ID,
    PROJECT_ID,
    WORK_DATE,
    HOURS_WORKED,
    WORK_TYPE,
    ENTRY_NOTE
FROM hr.TS_TIMESHEET_ENTRIES
"""

entries_df = pd.read_sql(entries_query, con=connection)
entries_df.to_csv(RAW_DIR / "timesheet_entries.csv", index=False)
print("timesheet_entries.csv extracted")

# 3. Extract TS_PROJECTS
projects_query = """
SELECT
    ID,
    NAME
FROM hr.TS_PROJECTS
"""

projects_df = pd.read_sql(projects_query, con=connection)
projects_df.to_csv(RAW_DIR / "projects.csv", index=False)
print("projects.csv extracted")

connection.close()
print("All extraction files created successfully!")