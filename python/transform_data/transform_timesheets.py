from pathlib import Path
import pandas as pd


RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

TIMESHEETS_FILE = RAW_DIR / "timesheets.csv"
ENTRIES_FILE = RAW_DIR / "timesheet_entries.csv"
PROJECTS_FILE = RAW_DIR / "projects.csv"

OUTPUT_FILE = PROCESSED_DIR / "timesheets_clean.csv"

REQUIRED_TIMESHEETS_COLUMNS = {
    "ID",
    "EMPLOYEE_ID",
}

REQUIRED_ENTRIES_COLUMNS = {
    "TIMESHEET_ID",
    "PROJECT_ID",
    "WORK_DATE",
    "HOURS_WORKED",
    "WORK_TYPE",
}

REQUIRED_PROJECTS_COLUMNS = {
    "ID",
    "NAME",
}


def load_csv(file_path: Path) -> pd.DataFrame:
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    return pd.read_csv(file_path)


def validate_required_columns(
    df: pd.DataFrame,
    required_columns: set[str],
    file_label: str
) -> None:
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(
            f"Missing required columns in {file_label}: "
            f"{', '.join(sorted(missing_columns))}"
        )


def clean_text_columns(
    timesheets_df: pd.DataFrame,
    entries_df: pd.DataFrame,
    projects_df: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    timesheets_df = timesheets_df.copy()
    entries_df = entries_df.copy()
    projects_df = projects_df.copy()

    if "WORK_TYPE" in entries_df.columns:
        entries_df["WORK_TYPE"] = entries_df["WORK_TYPE"].where(
            entries_df["WORK_TYPE"].isna(),
            entries_df["WORK_TYPE"].astype(str).str.strip().str.upper()
        )

    if "ENTRY_NOTE" in entries_df.columns:
        entries_df["ENTRY_NOTE"] = entries_df["ENTRY_NOTE"].where(
            entries_df["ENTRY_NOTE"].isna(),
            entries_df["ENTRY_NOTE"].astype(str).str.strip()
        )

    if "NAME" in projects_df.columns:
        projects_df["NAME"] = projects_df["NAME"].where(
            projects_df["NAME"].isna(),
            projects_df["NAME"].astype(str).str.strip()
        )

    return timesheets_df, entries_df, projects_df


def convert_types(
    timesheets_df: pd.DataFrame,
    entries_df: pd.DataFrame,
    projects_df: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    timesheets_df = timesheets_df.copy()
    entries_df = entries_df.copy()
    projects_df = projects_df.copy()

    timesheets_df["ID"] = pd.to_numeric(timesheets_df["ID"], errors="coerce")
    timesheets_df["EMPLOYEE_ID"] = pd.to_numeric(timesheets_df["EMPLOYEE_ID"], errors="coerce")

    entries_df["TIMESHEET_ID"] = pd.to_numeric(entries_df["TIMESHEET_ID"], errors="coerce")
    entries_df["PROJECT_ID"] = pd.to_numeric(entries_df["PROJECT_ID"], errors="coerce")
    entries_df["HOURS_WORKED"] = pd.to_numeric(entries_df["HOURS_WORKED"], errors="coerce")
    entries_df["WORK_DATE"] = pd.to_datetime(entries_df["WORK_DATE"], errors="coerce")

    projects_df["ID"] = pd.to_numeric(projects_df["ID"], errors="coerce")

    return timesheets_df, entries_df, projects_df


def validate_data(
    timesheets_df: pd.DataFrame,
    entries_df: pd.DataFrame,
    projects_df: pd.DataFrame
) -> None:
    if timesheets_df["ID"].isna().any():
        raise ValueError("Found invalid ID values in timesheets.csv")

    if timesheets_df["EMPLOYEE_ID"].isna().any():
        raise ValueError("Found invalid EMPLOYEE_ID values in timesheets.csv")

    if timesheets_df["ID"].duplicated().any():
        raise ValueError("Found duplicate ID values in timesheets.csv")

    if entries_df["TIMESHEET_ID"].isna().any():
        raise ValueError("Found invalid TIMESHEET_ID values in timesheet_entries.csv")

    if entries_df["PROJECT_ID"].isna().any():
        raise ValueError("Found invalid PROJECT_ID values in timesheet_entries.csv")

    if entries_df["WORK_DATE"].isna().any():
        raise ValueError("Found invalid WORK_DATE values in timesheet_entries.csv")

    if entries_df["HOURS_WORKED"].isna().any():
        raise ValueError("Found invalid HOURS_WORKED values in timesheet_entries.csv")

    if (entries_df["HOURS_WORKED"] < 0).any():
        raise ValueError("Found negative HOURS_WORKED values in timesheet_entries.csv")

    if (entries_df["HOURS_WORKED"] > 24).any():
        raise ValueError("Found HOURS_WORKED values greater than 24 in timesheet_entries.csv")

    if projects_df["ID"].isna().any():
        raise ValueError("Found invalid ID values in projects.csv")

    if projects_df["ID"].duplicated().any():
        raise ValueError("Found duplicate ID values in projects.csv")


def join_timesheet_data(
    timesheets_df: pd.DataFrame,
    entries_df: pd.DataFrame,
    projects_df: pd.DataFrame
) -> pd.DataFrame:
    merged_df = entries_df.merge(
        timesheets_df[["ID", "EMPLOYEE_ID"]],
        left_on="TIMESHEET_ID",
        right_on="ID",
        how="left"
    )

    if merged_df["EMPLOYEE_ID"].isna().any():
        raise ValueError("Some timesheet entries could not be matched to timesheets.csv")

    merged_df = merged_df.merge(
        projects_df[["ID", "NAME"]],
        left_on="PROJECT_ID",
        right_on="ID",
        how="left",
        suffixes=("", "_PROJECT")
    )

    if merged_df["NAME"].isna().any():
        raise ValueError("Some timesheet entries could not be matched to projects.csv")

    return merged_df


def standardize_output(df: pd.DataFrame) -> pd.DataFrame:
    output_df = pd.DataFrame({
        "employee_id": df["EMPLOYEE_ID"].astype(int),
        "activity_date": df["WORK_DATE"].dt.strftime("%Y-%m-%d"),
        "activity_category": "TIMESHEET",
        "activity_type": df["WORK_TYPE"],
        "project_id": df["PROJECT_ID"].astype("Int64"),
        "project_name": df["NAME"],
        "title": None,
        "hours": df["HOURS_WORKED"],
    })

    return output_df


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop_duplicates().copy()


def sort_data(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(
        by=["employee_id", "activity_date", "project_id"]
    ).reset_index(drop=True)


def save_clean_timesheets(df: pd.DataFrame, output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)


def transform_timesheets(output_file: Path) -> pd.DataFrame:
    timesheets_df = load_csv(TIMESHEETS_FILE)
    entries_df = load_csv(ENTRIES_FILE)
    projects_df = load_csv(PROJECTS_FILE)

    validate_required_columns(
        timesheets_df, REQUIRED_TIMESHEETS_COLUMNS, "timesheets.csv"
    )
    validate_required_columns(
        entries_df, REQUIRED_ENTRIES_COLUMNS, "timesheet_entries.csv"
    )
    validate_required_columns(
        projects_df, REQUIRED_PROJECTS_COLUMNS, "projects.csv"
    )

    timesheets_df, entries_df, projects_df = clean_text_columns(
        timesheets_df, entries_df, projects_df
    )
    timesheets_df, entries_df, projects_df = convert_types(
        timesheets_df, entries_df, projects_df
    )
    validate_data(timesheets_df, entries_df, projects_df)

    merged_df = join_timesheet_data(timesheets_df, entries_df, projects_df)
    cleaned_df = standardize_output(merged_df)
    cleaned_df = remove_duplicates(cleaned_df)
    cleaned_df = sort_data(cleaned_df)

    save_clean_timesheets(cleaned_df, output_file)
    return cleaned_df


cleaned_df = transform_timesheets(OUTPUT_FILE)

print("Timesheets transformation completed successfully.")
print(f"Output file: {OUTPUT_FILE}")
print(f"Rows written: {len(cleaned_df)}")
print("\nPreview:")
print(cleaned_df.head())