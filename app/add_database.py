import argparse
from pathlib import Path

import pandas as pd
import sqlite3

## to be used in docker only

parser = argparse.ArgumentParser(
        description="Load CSV data into an SQLite database."
    )

parser.add_argument(
    "--initial-licenses",
    required=False,
    default = Path("/app/app/csv/initial_licenses.csv"),
    type=Path,
    help="Path to initial_licenses.csv",
)

parser.add_argument(
    "--license-changes",
    required=False,
    default=Path("/app/app/csv/license_changes.csv"),
    type=Path,
    help="Path to license_changes.csv",
)

parser.add_argument(
    "--db",
    default="data.db",
    type=Path,
    help="Path to SQLite database (default: data.db)",
)

args = parser.parse_args()

init_licenses_path = args.initial_licenses
license_changes_path = args.license_changes
# Load CSV
init_licenses = pd.read_csv(init_licenses_path, header=0, index_col=False)
license_changed = pd.read_csv(license_changes_path, header=0, index_col=False)
# Connect to SQLite
sql_db_path = args.db
conn = sqlite3.connect(sql_db_path)

# Append into existing table (IMPORTANT: table already exists)
init_licenses.to_sql("initial_licenses", conn, if_exists="append", index=False)

license_changed.to_sql("license_changes", conn, if_exists="append", index=False)

conn.close()
print("data stored!")