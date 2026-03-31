from pathlib import Path
import re
import pandas as pd
import oracledb


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
PROCESSED_DIR = PROJECT_ROOT / 'data' / 'processed'

DB_CONFIG = {
    'user': 'hr',
    'password': '1234',
    'host': 'localhost',
    'port': 1521,
    'service_name': 'XEPDB1',
}


def load_csv(path):
    if not path.exists():
        raise FileNotFoundError(f'Could not find file: {path}')
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    return df


def df_to_rows(df):
    return df.where(pd.notna(df), None).values.tolist()


def extract_email(value):
    if pd.isna(value):
        return None
    match = re.search(r'([A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})', str(value))
    return match.group(1).lower() if match else None


def extract_name_from_confluence(value):
    if pd.isna(value):
        return None
    text = str(value).strip()
    match = re.match(r'^(.*?)\s*<[^>]+>$', text)
    if match:
        name = match.group(1).strip()
        return name if name else None
    return None


def normalize_employee_bk(value, source):
    if pd.isna(value):
        return None
    if source == 'TIMESHEET':
        return f"ID:{str(value).strip()}"
    if source == 'CONFLUENCE':
        email = extract_email(value)
        return email if email else str(value).strip().lower()
    return str(value).strip().lower()


def build_employee_name(employee_bk, employee_name, employee_email, source_employee_value, source):
    if pd.notna(employee_name) and str(employee_name).strip():
        return str(employee_name).strip()

    if source == 'CONFLUENCE':
        confluence_name = extract_name_from_confluence(source_employee_value)
        if confluence_name:
            return confluence_name

    if pd.notna(employee_email) and str(employee_email).strip():
        return str(employee_email).strip()

    if pd.notna(employee_bk) and str(employee_bk).strip():
        return str(employee_bk).strip()

    return 'Unknown Employee'


def prepare_source(filename, source):
    df = load_csv(PROCESSED_DIR / filename)

    for col in [
        'employee_id', 'employee_name', 'activity_date', 'activity_category',
        'activity_type', 'project_id', 'project_name', 'title', 'hours'
    ]:
        if col not in df.columns:
            df[col] = None

    original_employee_value = df['employee_id'].copy()

    df['employee_bk'] = df['employee_id'].apply(lambda x: normalize_employee_bk(x, source))

    if source == 'CONFLUENCE':
        df['employee_email'] = df['employee_id'].apply(extract_email)
    elif source == 'ABSENCE':
        df['employee_email'] = df['employee_id'].astype(str).str.strip().str.lower()
    else:
        df['employee_email'] = None

    df['employee_name'] = [
        build_employee_name(bk, name, email, raw_value, source)
        for bk, name, email, raw_value in zip(
            df['employee_bk'],
            df['employee_name'],
            df['employee_email'],
            original_employee_value
        )
    ]

    df['activity_date'] = pd.to_datetime(df['activity_date'], errors='coerce')
    df['hours'] = pd.to_numeric(df['hours'], errors='coerce')
    df['source_system'] = source

    return df[
        [
            'employee_bk', 'employee_email', 'employee_name', 'activity_date',
            'activity_category', 'activity_type', 'project_id', 'project_name',
            'title', 'hours', 'source_system'
        ]
    ].dropna(subset=['employee_bk', 'activity_date', 'hours'])


def check_data(df):
    print(f'Exact duplicate rows: {df.duplicated().sum()}')

    overlap = (
        df[df['source_system'].isin(['ABSENCE', 'CONFLUENCE'])]
        .groupby(['employee_bk', 'activity_date'])['source_system']
        .nunique()
    )
    print(f'Absence/Confluence overlaps: {(overlap > 1).sum()}')

    return df.drop_duplicates().reset_index(drop=True)


def build_dimensions(df):
    dim_date = df[['activity_date']].drop_duplicates().copy()
    dim_date['date_key'] = dim_date['activity_date'].dt.strftime('%Y%m%d').astype(int)
    dim_date['full_date'] = dim_date['activity_date'].dt.date
    dim_date['day_number'] = dim_date['activity_date'].dt.day
    dim_date['day_name'] = dim_date['activity_date'].dt.day_name()
    dim_date['month_number'] = dim_date['activity_date'].dt.month
    dim_date['month_name'] = dim_date['activity_date'].dt.month_name()
    dim_date['quarter_num'] = dim_date['activity_date'].dt.quarter
    dim_date['year_num'] = dim_date['activity_date'].dt.year
    dim_date = dim_date[
        ['date_key', 'full_date', 'day_number', 'day_name',
         'month_number', 'month_name', 'quarter_num', 'year_num']
    ]

    dim_employee = (
        df[['employee_bk', 'employee_email', 'employee_name']]
        .drop_duplicates()
        .rename(columns={'employee_bk': 'employee_id', 'employee_name': 'employee_full_name'})
    )

    dim_employee['employee_full_name'] = dim_employee['employee_full_name'].fillna('Unknown Employee')
    dim_employee['employee_full_name'] = dim_employee['employee_full_name'].astype(str).str.strip()
    dim_employee.loc[dim_employee['employee_full_name'] == '', 'employee_full_name'] = 'Unknown Employee'

    dim_activity = (
        df[['activity_category', 'activity_type', 'project_id', 'project_name', 'title']]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    return dim_date, dim_employee, dim_activity


def load_star_schema(dim_date, dim_employee, dim_activity, fact_df):
    conn = oracledb.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute('DELETE FROM fact_employee_day')
    cur.execute('DELETE FROM dim_activities')
    cur.execute('DELETE FROM dim_employee')
    cur.execute('DELETE FROM dim_date')

    cur.executemany(
        '''
        INSERT INTO dim_date
        (date_key, full_date, day_number, day_name, month_number, month_name, quarter_num, year_num)
        VALUES (:1, :2, :3, :4, :5, :6, :7, :8)
        ''',
        df_to_rows(dim_date)
    )

    cur.executemany(
        '''
        INSERT INTO dim_employee (employee_id, employee_email, employee_full_name)
        VALUES (:1, :2, :3)
        ''',
        df_to_rows(dim_employee)
    )

    cur.executemany(
        '''
        INSERT INTO dim_activities (activity_category, activity_type, project_id, project_name, title)
        VALUES (:1, :2, :3, :4, :5)
        ''',
        df_to_rows(dim_activity)
    )

    conn.commit()

    cur.execute('SELECT employee_key, employee_id FROM dim_employee')
    employee_lookup = {employee_id: employee_key for employee_key, employee_id in cur.fetchall()}

    cur.execute('SELECT activity_key, activity_category, activity_type, project_id, project_name, title FROM dim_activities')
    activity_lookup = {
        (activity_category, activity_type, project_id, project_name, title): activity_key
        for activity_key, activity_category, activity_type, project_id, project_name, title in cur.fetchall()
    }

    fact_df = fact_df.copy()
    fact_df['date_key'] = fact_df['activity_date'].dt.strftime('%Y%m%d').astype(int)

    fact_rows = []
    for _, row in fact_df.iterrows():
        employee_key = employee_lookup.get(row['employee_bk'])
        activity_key = activity_lookup.get((
            row['activity_category'],
            row['activity_type'],
            row['project_id'],
            row['project_name'],
            row['title']
        ))

        if employee_key is None or activity_key is None:
            continue

        fact_rows.append((
            int(row['date_key']),
            int(employee_key),
            int(activity_key),
            float(row['hours'])
        ))

    cur.executemany(
        '''
        INSERT INTO fact_employee_day (date_key, employee_key, activity_key, hours)
        VALUES (:1, :2, :3, :4)
        ''',
        fact_rows
    )

    conn.commit()
    cur.close()
    conn.close()
    print('Star schema loaded into Oracle.')


timesheets = prepare_source('timesheets_clean.csv', 'TIMESHEET')
absences = prepare_source('absences_clean.csv', 'ABSENCE')
confluence = prepare_source('confluence_clean.csv', 'CONFLUENCE')

all_data = check_data(pd.concat([timesheets, absences, confluence], ignore_index=True))
dim_date, dim_employee, dim_activity = build_dimensions(all_data)
load_star_schema(dim_date, dim_employee, dim_activity, all_data)