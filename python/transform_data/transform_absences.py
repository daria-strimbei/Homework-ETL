import pandas as pd
from datetime import timedelta

# load file
df = pd.read_csv("data/raw/Absences.csv")

# normalize column names
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

# basic cleaning
df["name"] = df["name"].astype(str).str.strip()
df["email"] = df["email"].astype(str).str.strip().str.lower()
df["reason"] = df["reason"].astype(str).str.strip()

# convert dates
df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")
df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")

# drop bad rows (simple instead of strict validation)
df = df.dropna(subset=["name", "email", "start_date", "end_date", "reason"])

# expand to daily rows
rows = []

for _, row in df.iterrows():
    current_date = row["start_date"]

    while current_date <= row["end_date"]:
        rows.append({
            "activity_date": current_date.date(),
            "employee_id": row["email"],  # using email as id
            "employee_name": row["name"],
            "activity_category": "ABSENCE",
            "activity_type": row["reason"],
            "project_id": None,
            "project_name": None,
            "title": None,
            "hours": 8
        })
        current_date += timedelta(days=1)

# create dataframe
df_clean = pd.DataFrame(rows)

# remove duplicates (like confluence script)
df_clean = df_clean.drop_duplicates()

# save
df_clean.to_csv("data/processed/absences_clean.csv", index=False)

print("Done: data/processed/absences_clean.csv created")
print(df_clean.head())