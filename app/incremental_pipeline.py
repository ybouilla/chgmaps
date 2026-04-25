import argparse
import csv
import os

import pandas as pd
from transformation import transform_pipeline
from logger import  set_logging, logger
from datetime import datetime, timedelta, timezone
from typing import List, Dict

from incremental_pipeline_tools.state_manager import parse_ts, load_checkpoint, save_checkpoint


# ----------------------------
# Config
# ----------------------------


LOOKBACK_MINUTES = 0  # lookback

N_BATCH = 10  # number of batches
MAX_RETRIES = 3  # number of retries to process when a batch of data fails

# ----------------------------
# Mock source
# ----------------------------
def mock_fetch_source_data(start_ts: datetime, end_ts: datetime, **args) -> List[Dict]:
    logger.info(f"Fetching data from {start_ts} to {end_ts}")

    mock_data = [
        {"id": 1, "value": "A", "date": "2026-04-25T10:00:00"},
        {"id": 2, "value": "B", "date": "2026-04-25T10:30:00"},
        {"id": 3, "value": "C", "date": "2026-04-25T10:45:00"},
        {"id": 1, "value": "A_updated", "date": "2026-04-25T11:00:00"},
    ]

    data = [
        r for r in mock_data
        if start_ts <= parse_ts(r["date"]) <= end_ts
    ]

    logger.info(f"Fetched {len(data)} records")
    return data


def fetch_source_data(start_ts: datetime, end_ts: datetime, init_file: str,
                      changed_file: str, folder_name: str) -> List[Dict]:
    logger.info(f"Fetching data from {start_ts} to {end_ts}")
        

    created_csv = pd.read_csv(os.path.join(folder_name, init_file), index_col=False)
    changed_csv = pd.read_csv(os.path.join(folder_name, changed_file), index_col=False)
    created_csv["creation_date"] = pd.to_datetime(created_csv["creation_date"], utc=True)
    changed_csv["date"] = pd.to_datetime(changed_csv["date"], utc=True)

    created_csv = created_csv[
        (created_csv["creation_date"] >= pd.Timestamp(start_ts).tz_convert("UTC")) &
        (created_csv["creation_date"] <= pd.Timestamp(end_ts).tz_convert("UTC"))
    ]
    changed_csv = changed_csv[
        (changed_csv["date"] >= pd.Timestamp(start_ts).tz_convert("UTC")) &
        (changed_csv["date"] <= pd.Timestamp(end_ts).tz_convert("UTC"))
    ]
    # data = data[
    #     (data["date"] >= pd.Timestamp(start_ts).tz_convert("UTC")) &
    #     (data["date"] <= pd.Timestamp(end_ts).tz_convert("UTC"))
    # ]
    logger.info(f"Fetched {len(created_csv)} from {init_file} records")
    logger.info(f"Fetched {len(changed_csv)} from {changed_file} records")
    return created_csv, changed_csv

# ----------------------------
# Target store (idempotent)
# ----------------------------
def load_target(folder_name: str, output_file: str, variables:List[str], date_entry: str) -> pd.DataFrame:
    folder = os.path.join(folder_name, output_file)
    if not os.path.exists(folder):
        return pd.DataFrame(columns=variables)

    df = pd.read_csv(folder)
    df[date_entry] = pd.to_datetime(df[date_entry], utc=True)
    return df


def save_target(df: pd.DataFrame, output_file: str, folder_name: str):
    print("data saved", df)

    df.to_csv(os.path.join(folder_name, output_file), index=False)


def upsert_batch(records: pd.DataFrame, target: pd.DataFrame) -> pd.DataFrame:
    if len(records) == 0:
        return target

    # incoming = pd.DataFrame(records)
    # incoming["date"] = pd.to_datetime(incoming["date"], utc=True)

    # combine old + new
    
    combined = pd.concat([target, records], ignore_index=True)
    combined = combined.drop_duplicates(subset="id", keep="last")  # remove duplicates if any

    return combined


# ----------------------------
# Batch helper
# ----------------------------
def chunk(data: List[Dict], size: int):
    return [(i // size, data[i:i + size]) for i in range(0, len(data), size)]
        


# ----------------------------
# Retry batch processing
# ----------------------------
def process_batch(batch_id: int, batch: pd.DataFrame,
                  target: pd.DataFrame, output_file: str, folder_name: str, date_str: str ) -> bool:
    for attempt in range(1, MAX_RETRIES + 1):
        try:

            
            logger.info(f"Batch {batch_id} | attempt {attempt} | size {len(batch)}")

            target = upsert_batch(batch, target)
            target = target.sort_values(date_str)
            
            save_target(target, output_file, folder_name)
            
            logger.info(f"Batch {batch_id} SUCCESS")
            return True, target

        except Exception as e:
            # change Exception to another exception
            logger.warning(f"Batch {batch_id} failed attempt {attempt}: {e}")

    logger.error(f"Batch {batch_id} FAILED permanently")
    return False, target

def run_backfill_pipeline(inital_license_file: str, changed_license_file: str,
                          output_init_license: str, output_changed_license: str,
                          folder_name: str, days: int=5, ):
    """Runs backfill for data coming very late"""
    now = datetime.now(timezone.utc)

    start_ts = now - timedelta(days=days)


    logger.info(f"BACKFILL START | window={start_ts} -> {now}")

    run_pipeline(start_ts, None, inital_license_file, changed_license_file,
                 output_init_license, output_changed_license, folder_name)

    logger.info("BACKFILL COMPLETE")

# ----------------------------
# Pipeline
# ----------------------------
def run_pipeline(start: str, end: str, inital_license_file: str,
                 changed_license_file: str, created_output_file: str,
                 changed_output_file: str, folder_name: str) : 
    logger.info("PIPELINE START")

    # ----------------------------
    # 1. Load state (watermark)
    # ----------------------------
    state = load_checkpoint()

    last_data_ts = state["last_data_timestamp"]
    last_processed_ts = state["last_processed_timestamp"]

    logger.info(f"Loaded state | data_ts={last_data_ts} | processed_ts={last_processed_ts}")

    if isinstance(start, str):
        start = parse_ts(start)
    # ----------------------------
    # 2. Define processing window
    # ----------------------------
    
    end_ts = datetime.now(timezone.utc) if end is None else parse_ts(end)
    start_ts = ( start or last_processed_ts) - timedelta(minutes=LOOKBACK_MINUTES)
    

    logger.info(f"Processing window | start={start_ts} | end={end_ts}")

    # ----------------------------
    # 3. Fetch data
    # ----------------------------
    created_csv, changed_csv = fetch_source_data(start_ts, end_ts ,
                                                 inital_license_file,
                                                 changed_license_file,
                                                 folder_name)

    created_target = load_target(folder_name, created_output_file, 
                                 ["id", "customer_id", "type", "creation_date","price", "renewable"],
                                 "creation_date")
    changed_target = load_target(folder_name, changed_output_file,
                                 ["license_id", "date" , "price", "type", "renewable"],
                                  "date")
    # ----------------------------
    # 4. Track watermarks
    # ----------------------------
    max_data_ts = last_data_ts
    max_processed_ts = last_processed_ts

    failed_batches = 0

    # ----------------------------
    # 5. Batch processing
    # ----------------------------
    
    create_batches = chunk(created_csv, N_BATCH)
    chgd_batches = chunk(changed_csv, N_BATCH)

    max_len = max(len(create_batches), len(chgd_batches))
    for batch_id in range(max_len):
        create_batch = create_batches[batch_id][1] if batch_id < len(create_batches) else pd.DataFrame(columns=created_csv.columns)
        chgd_batch = chgd_batches[batch_id][1] if batch_id < len(chgd_batches) else pd.DataFrame(columns=changed_csv.columns)
        logger.info(f"Batch {batch_id} | create={len(create_batch)} | change={len(chgd_batch)}")

        success_1, created_target = process_batch(batch_id, create_batch,  created_target,
                                  created_output_file, folder_name, "creation_date")
        success_2, changed_target = process_batch(batch_id, chgd_batch,  changed_target,
                                  changed_output_file, folder_name, "date")
        batch_max_ts = max(create_batch["creation_date"].max() if len(create_batch) else start_ts,
                            chgd_batch["date"].max() if len(chgd_batch) else start_ts)

        # update DATA watermark 
        if batch_max_ts > max_data_ts:
            max_data_ts = batch_max_ts

        # Only update PROCESSED watermark on success
        if all((success_1, success_2,)):
            if batch_max_ts > max_processed_ts:
                max_processed_ts = batch_max_ts
        else:
            failed_batches += 1
            logger.warning(f"Batch {batch_id} FAILED")

    # ----------------------------
    # 6. Persist final state
    # ----------------------------
    save_checkpoint(
        last_data_ts=max_data_ts,
        last_processed_ts=max_processed_ts
    )

    # ----------------------------
    # 7. Summary
    # ----------------------------
    logger.info(
        "PIPELINE END | "
        f"data_ts={max_data_ts} | "
        f"processed_ts={max_processed_ts} | "
        f"failed_batches={failed_batches}"
    )


if __name__ == "__main__":
    initial_license_file = "initial_licenses.csv"
    licence_changed_file = "license_changes.csv"
    folder_name = "csv"
    dir_path = os.path.dirname(os.path.realpath(__file__))
    folder_name = os.path.join(dir_path, folder_name)
    
    set_logging("incremental.log")

    parser = argparse.ArgumentParser()

    parser.add_argument("--mode", choices=["incremental", "backfill"], default="incremental")
    parser.add_argument("--days", type=int, default=5)

    args = parser.parse_args()

    if args.mode == "incremental":

        start, end = "2023-04-25T10:00:00", "2023-04-30T10:10:00"
        run_pipeline(start, end, initial_license_file, licence_changed_file, "target1.csv", "target2.csv", folder_name)

        start, end = "2023-04-25T10:00:00", "2023-05-10T10:10:00"
        run_pipeline(start, end, initial_license_file, licence_changed_file, "target1.csv", "target2.csv", folder_name)
        chck = pd.read_csv("target2.csv", index_col=False)
        assert len(chck["id"]) == len(chck["id"].unique())

    elif args.mode == "backfill":
        run_backfill_pipeline(initial_license_file, licence_changed_file, "target1.csv", "target2.csv", folder_name, days=args.days)
    
    