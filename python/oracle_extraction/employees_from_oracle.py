import pandas as pd
import oracledb

connection = oracledb.connect(
    user="hr",
    password="1234",
    host="localhost",
    port=1521,
    service_name="XEPDB1"
)

print("Connected!")

query = """
SELECT
    employee_id,
    first_name || ' ' || last_name AS employee_full_name
FROM hr.employees
"""

df = pd.read_sql(query, con=connection)
df.to_csv("data/raw/employees.csv", index=False)

print("employees.csv extracted")
connection.close()