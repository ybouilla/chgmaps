import os
import pandas as pd

# files
file_name_init_licenses = "initial_licenses.csv"
file_name_changed_licenses = "license_changes.csv"
file_name_transformation = "transformed.csv"
folder_name = "csv"

created_csv = pd.read_csv(os.path.join(folder_name, file_name_init_licenses), index_col=False, header=0)
changed_csv = pd.read_csv(os.path.join(folder_name, file_name_changed_licenses), index_col=False, header=0)

created_csv["creation_date"] = pd.to_datetime(created_csv["creation_date"], format="%Y-%m-%d").dt.date
changed_csv["date"] = pd.to_datetime(changed_csv["date"],  format="%Y-%m-%d").dt.date
# merged = pd.merge(changed_csv, created_csv, left_on="license_id", right_on="id", how="left")

transformed_csv = ("date", "type", "active_license_count", "active_license_price", "inactive_license_count",
                   "daily_active_diff", "daily_price_diff", "daily_inactive_diff",)


# -------------------------
# 1. Build unified state table
# -------------------------

changed_clean = (
    changed_csv
    .sort_values(["license_id", "date", "id"])
    .groupby(["license_id", "date"])
    .tail(1)
)

initial_state = (
    created_csv
    .rename(columns={"id": "license_id", "creation_date": "date"})
    [["license_id", "date", "renewable", "price", "type"]]
)

initial_state["id"] = -1

states = (
    pd.concat([changed_clean, initial_state])
    .sort_values(["license_id", "date", "id"])
)


# -------------------------
# 2. State transitions
# -------------------------

states["prev"] = states.groupby("license_id")["renewable"].shift()

states["activated"] = (states["renewable"] & states["prev"].ne(True))
states["deactivated"] = (~states["renewable"] & states["prev"].eq(True))

# -------------------------
# 3. Daily event aggregation
# -------------------------

all_dates = pd.date_range(states["date"].min(), states["date"].max())

daily_events = (
    states.groupby(["date", "type"])
    .agg(
        activated_licenses=("activated", "sum"),
        deactivated_licenses=("deactivated", "sum")
    )
    .reindex(pd.MultiIndex.from_product(
            [all_dates, states["type"].unique()],
            names=["date", "type"]
        ), fill_value=0)
    # .rename_axis("date")
    .reset_index()
)

# -------------------------
# 4. Active / inactive licenses
# -------------------------

daily_events["active_license_count"] = (
    daily_events.groupby("type")["activated_licenses"].cumsum() -
    daily_events.groupby("type")["deactivated_licenses"].cumsum()
)

created_daily = (
    created_csv.groupby("creation_date")
    .size()
    .reindex(all_dates, fill_value=0)
    .cumsum()
)

daily_events["total_licenses"] = daily_events["date"].map(created_daily)
daily_events["inactive_license_count"] = (
    daily_events["total_licenses"] - daily_events["active_license_count"]
)

daily_events["daily_active_diff"] = daily_events["active_license_count"].diff().fillna(0)
daily_events["daily_inactive_diff"] = daily_events["inactive_license_count"].diff().fillna(0)

# -------------------------
# 5. Price flow
# -------------------------

states["price_in"] = states["activated"] * states["price"]
states["price_out"] = states["deactivated"] * states["price"]

daily_price = (
    states.groupby(["date", "type"])[["price_in", "price_out"]]
    .sum()
    .reindex(pd.MultiIndex.from_product(
            [all_dates, states["type"].unique()],
            names=["date", "type"]), fill_value=0)
)
# price_series = (
#     (daily_price["price_in"] - daily_price["price_out"])
#     .cumsum()
# )

daily_events = daily_events.set_index("date")
daily_events["active_license_price"] = (
    daily_price["price_in"].groupby(level="type").cumsum()
    - daily_price["price_out"].groupby(level="type").cumsum()
).values
daily_events = daily_events.reset_index()
# daily_events["active_price"] = (
#     daily_price["price_in"] - daily_price["price_out"]
# ).cumsum()

daily_events["daily_price_diff"] = daily_events["active_license_price"].diff().fillna(0)

# data saving into *.csv

daily_events[list(transformed_csv)].to_csv(os.path.join(folder_name, file_name_transformation), index=False)
print("data now transformed and saved at ", os.path.join(folder_name, file_name_transformation))
