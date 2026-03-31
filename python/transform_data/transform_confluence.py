import pandas as pd
import re

df = pd.read_csv("data/raw/Confluence.csv")
df.columns = df.columns.str.strip().str.lower()

# clean spaces
df["start"] = df["start"].astype(str).str.strip()
df["end"] = df["end"].astype(str).str.strip()

# parse mixed datetime formats, keeping day/month/year interpretation
df["start"] = pd.to_datetime(df["start"], format="mixed", dayfirst=True, errors="coerce")
df["end"] = pd.to_datetime(df["end"], format="mixed", dayfirst=True, errors="coerce")

df = df.dropna(subset=["start", "end"])

# duration in hours
df["hours"] = (df["end"] - df["start"]).dt.total_seconds() / 3600
df.loc[df["hours"] <= 0, "hours"] = 1

rows = []

for _, row in df.iterrows():
    attendees_value = str(row["attendees"]).strip()

    # split attendees by comma or semicolon
    attendees_list = [a.strip() for a in re.split(r"[;,]", attendees_value) if a.strip()]

    # if no attendee found
    if not attendees_list:
        attendees_list = ["UNKNOWN"]

    for attendee in attendees_list:
        rows.append({
            "employee_id": attendee,
            "activity_date": row["start"].date(),
            "activity_category": "CONFLUENCE",
            "activity_type": row["categories"],
            "project_name": None,
            "title": row["title"],
            "hours": round(row["hours"], 2)
        })

df_clean = pd.DataFrame(rows)

# remove duplicates
df_clean = df_clean.drop_duplicates()

df_clean.to_csv("data/processed/confluence_clean.csv", index=False)

print("Done: data/processed/confluence_clean.csv created")
print(df_clean.head(10))