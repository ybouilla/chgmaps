import os
import pandas as pd

import os
import pandas as pd


# -------------------------
# 1. Load data
# -------------------------
def load_data(folder_name, init_file, changed_file):
    created_csv = pd.read_csv(os.path.join(folder_name, init_file), index_col=False)
    changed_csv = pd.read_csv(os.path.join(folder_name, changed_file), index_col=False)

    created_csv["creation_date"] = pd.to_datetime(created_csv["creation_date"])
    changed_csv["date"] = pd.to_datetime(changed_csv["date"])

    return created_csv, changed_csv


# -------------------------
# 2. Build unified state table
# -------------------------
def build_states(created_csv, changed_csv):

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

    changed_index = changed_clean.set_index(["license_id", "date"]).index
    initial_state = initial_state[
        ~initial_state.set_index(["license_id", "date"]).index.isin(changed_index)
    ]

    states = (
        pd.concat([changed_clean, initial_state])
        .sort_values(["license_id", "date", "id"])
    )

    return states

def build_daily_states(states):
    states = states.copy()
    states["date"] = pd.to_datetime(states["date"])

    states = states.sort_values(["license_id", "date", "id"])
    states = states.drop_duplicates(["license_id", "date"], keep="last")

    daily = (
        states.set_index("date")
        .groupby("license_id")[["renewable", "type", "price"]]
        .apply(lambda df: df.resample("D").ffill())
        .reset_index()
    )

    return daily, pd.date_range(states["date"].min(), states["date"].max())
# -------------------------
# 3. State transitions
# -------------------------
def compute_counts(daily_states, created_csv, all_dates):

    created_daily = (
        created_csv.groupby("creation_date")
        .size()
        .reindex(all_dates, fill_value=0)
        .cumsum()
    )

    # type grouping
    active = (
        daily_states[daily_states["renewable"]]
        .groupby(["date", "type"])
        .size()
    )

    inactive = (
        daily_states[daily_states["renewable"] == False]
        .groupby(["date", "type"])
        .size()
    )

    df = pd.DataFrame(index=pd.MultiIndex.from_product(
        [all_dates, daily_states["type"].unique()],
        names=["date", "type"]
    )).reset_index()

    df["active_license_count"] = df.set_index(["date", "type"]).index.map(active).fillna(0).values
    df["inactive_license_count"] = df.set_index(["date", "type"]).index.map(inactive).fillna(0).values

    df["active_license_count"] = df["active_license_count"].astype(int)
    df["inactive_license_count"] = df["inactive_license_count"].astype(int)

    df["total_licenses"] = df["date"].map(created_daily)

    df["inactive_license_count"] = df["total_licenses"] - df["active_license_count"]

    df["daily_active_diff"] = df.groupby("type")["active_license_count"].diff().fillna(0)
    df["daily_inactive_diff"] = df.groupby("type")["inactive_license_count"].diff().fillna(0)

    return df


# -------------------------
# 4. Daily event aggregation
# -------------------------
def compute_daily_events(states, all_dates):
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
        .reset_index()
    )

    return daily_events


# -------------------------
# 5. Active / inactive calculations
# -------------------------


def expand_license_daily(df):
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    return (
        df.set_index("date")["renewable"]
        .resample("D")
        .ffill()
    )
# -------------------------
# 6. Price computation
# -------------------------
def compute_price(daily_states, all_dates):
    df = daily_states.copy()

    df["active_value"] = df["renewable"] * df["price"]

    daily_price = (
        df.groupby(["date", "type"])["active_value"]
        .sum()
        .reindex(
            pd.MultiIndex.from_product([all_dates, df["type"].unique()],
            names=["date", "type"]),
            fill_value=0
        )
        .reset_index(name="active_license_price")
    )

    return daily_price

def compute_daily_price_diff(df):
    # df = df.copy()

    # ensure correct order for diff computation
    df = df.sort_values(["type", "date"])

    df["daily_price_diff"] = (
        df.groupby("type")["active_license_price"]
        .diff()
        .fillna(0)
    )

    # final display order
    df = df.sort_values(["date", "type"])

    return df
# -------------------------
# 7. Full pipeline
# -------------------------
def transform_pipeline(init: pd.DataFrame, changed: pd.DataFrame) -> pd.DataFrame:
    

    states = build_states(init, changed)

    daily_states, all_dates = build_daily_states(states)

    daily_events = compute_counts(daily_states, init, all_dates)

    daily_price = compute_price(daily_states, all_dates)

    daily_events = daily_events.merge(daily_price, on=["date", "type"], how="left")

    
    daily_events = compute_daily_price_diff(daily_events)
    transformed_col = ("date", "type", "active_license_count", "active_license_price", "inactive_license_count",
                   "daily_active_diff", "daily_price_diff", "daily_inactive_diff",)
    
    return daily_events[list(transformed_col)]


if __name__ == "__main__":
    dir_path = os.path.dirname(os.path.realpath(__file__))
    folder_name=os.path.join(dir_path, "csv")
    init_file="initial_licenses.csv"
    changed_file="license_changes.csv"
    output_file="transformed.csv"
    created_csv, changed_csv = load_data(folder_name, init_file, changed_file)
    result = transform_pipeline(created_csv, changed_csv )
    result.to_csv(os.path.join(folder_name, output_file), index=False)
    print("data now transformed and saved at", os.path.join(folder_name, output_file))
# # files
# file_name_init_licenses = "initial_licenses.csv"
# file_name_changed_licenses = "license_changes.csv"
# file_name_transformation = "transformed.csv"
# folder_name = "csv"

# created_csv = pd.read_csv(os.path.join(folder_name, file_name_init_licenses), index_col=False, header=0)
# changed_csv = pd.read_csv(os.path.join(folder_name, file_name_changed_licenses), index_col=False, header=0)

# created_csv["creation_date"] = pd.to_datetime(created_csv["creation_date"], format="%Y-%m-%d").dt.date
# changed_csv["date"] = pd.to_datetime(changed_csv["date"],  format="%Y-%m-%d").dt.date
# # merged = pd.merge(changed_csv, created_csv, left_on="license_id", right_on="id", how="left")

# transformed_csv = ("date", "type", "active_license_count", "active_license_price", "inactive_license_count",
#                    "daily_active_diff", "daily_price_diff", "daily_inactive_diff",)


# # -------------------------
# # 1. Build unified state table
# # -------------------------

# changed_clean = (
#     changed_csv
#     .sort_values(["license_id", "date", "id"])
#     .groupby(["license_id", "date"])
#     .tail(1)
# )

# initial_state = (
#     created_csv
#     .rename(columns={"id": "license_id", "creation_date": "date"})
#     [["license_id", "date", "renewable", "price", "type"]]
# )

# initial_state["id"] = -1

# states = (
#     pd.concat([changed_clean, initial_state])
#     .sort_values(["license_id", "date", "id"])
# )


# # -------------------------
# # 2. State transitions
# # -------------------------

# states["prev"] = states.groupby("license_id")["renewable"].shift()

# states["activated"] = (states["renewable"] & states["prev"].ne(True))
# states["deactivated"] = (~states["renewable"] & states["prev"].eq(True))

# # -------------------------
# # 3. Daily event aggregation
# # -------------------------

# all_dates = pd.date_range(states["date"].min(), states["date"].max())

# daily_events = (
#     states.groupby(["date", "type"])
#     .agg(
#         activated_licenses=("activated", "sum"),
#         deactivated_licenses=("deactivated", "sum")
#     )
#     .reindex(pd.MultiIndex.from_product(
#             [all_dates, states["type"].unique()],
#             names=["date", "type"]
#         ), fill_value=0)
#     # .rename_axis("date")
#     .reset_index()
# )

# # -------------------------
# # 4. Active / inactive licenses
# # -------------------------

# daily_events["active_license_count"] = (
#     daily_events.groupby("type")["activated_licenses"].cumsum() -
#     daily_events.groupby("type")["deactivated_licenses"].cumsum()
# )

# created_daily = (
#     created_csv.groupby("creation_date")
#     .size()
#     .reindex(all_dates, fill_value=0)
#     .cumsum()
# )

# daily_events["total_licenses"] = daily_events["date"].map(created_daily)
# daily_events["inactive_license_count"] = (
#     daily_events["total_licenses"] - daily_events["active_license_count"]
# )

# daily_events["daily_active_diff"] = daily_events["active_license_count"].diff().fillna(0)
# daily_events["daily_inactive_diff"] = daily_events["inactive_license_count"].diff().fillna(0)

# # -------------------------
# # 5. Price flow
# # -------------------------

# states["price_in"] = states["activated"] * states["price"]
# states["price_out"] = states["deactivated"] * states["price"]

# daily_price = (
#     states.groupby(["date", "type"])[["price_in", "price_out"]]
#     .sum()
#     .reindex(pd.MultiIndex.from_product(
#             [all_dates, states["type"].unique()],
#             names=["date", "type"]), fill_value=0)
# )
# # price_series = (
# #     (daily_price["price_in"] - daily_price["price_out"])
# #     .cumsum()
# # )

# daily_events = daily_events.set_index("date")
# daily_events["active_license_price"] = (
#     daily_price["price_in"].groupby(level="type").cumsum()
#     - daily_price["price_out"].groupby(level="type").cumsum()
# ).values
# daily_events = daily_events.reset_index()
# # daily_events["active_price"] = (
# #     daily_price["price_in"] - daily_price["price_out"]
# # ).cumsum()

# daily_events["daily_price_diff"] = daily_events["active_license_price"].diff().fillna(0)

# # data saving into *.csv

# daily_events[list(transformed_csv)].to_csv(os.path.join(folder_name, file_name_transformation), index=False)
# print("data now transformed and saved at ", os.path.join(folder_name, file_name_transformation))
