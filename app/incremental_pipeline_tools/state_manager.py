from datetime import datetime, timezone
import os
from logger import logger
import csv

dir_path = os.path.dirname(os.path.realpath(__file__))
STATE_FILE = os.path.join(dir_path, "..", "states", "state.csv")
EPOCH_UTC = datetime(1970, 1, 1, tzinfo=timezone.utc)
# ----------------------------
# Helpers
# ----------------------------
def parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts).replace(tzinfo=timezone.utc)


def format_ts(dt: datetime) -> str:
    return dt.isoformat()


# ----------------------------
# State (checkpoint)
# ----------------------------
def load_checkpoint():
    if not os.path.exists(STATE_FILE):
        return {
            "last_data_timestamp": EPOCH_UTC,
            "last_processed_timestamp": EPOCH_UTC,
        }

    with open(STATE_FILE, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

        if not rows:
            return {
                "last_data_timestamp": EPOCH_UTC,
                "last_processed_timestamp": EPOCH_UTC,
            }

        row = rows[0]

        return {
            "last_data_timestamp": datetime.fromisoformat(row["last_data_timestamp"]),
            "last_processed_timestamp": datetime.fromisoformat(row["last_processed_timestamp"]),
        }


def save_checkpoint(last_data_ts: datetime, last_processed_ts: datetime):

    if last_data_ts.tzinfo is None:
        last_data_ts = last_data_ts.replace(tzinfo=timezone.utc)
    else:
        last_data_ts = last_data_ts.astimezone(timezone.utc)

    if last_processed_ts.tzinfo is None:
        last_processed_ts = last_processed_ts.replace(tzinfo=timezone.utc)
    else:
        last_processed_ts = last_processed_ts.astimezone(timezone.utc)

    with open(STATE_FILE, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["last_data_timestamp", "last_processed_timestamp"]
        )
        writer.writeheader()
        writer.writerow({
            "last_data_timestamp": last_data_ts.isoformat(),
            "last_processed_timestamp": last_processed_ts.isoformat(),
        })
