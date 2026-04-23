from typing import Iterable

import pandas as pd
import logging
import os

# logging configuration

logging.basicConfig(
    filename="validation.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# files
file_name_init_licenses = "initial_licenses.csv"
file_name_changed_licenses = "license_changes.csv"
folder_name = "csv"
created_csv = pd.read_csv(os.path.join(folder_name, file_name_init_licenses), index_col=False, header=0)
changed_csv = pd.read_csv(os.path.join(folder_name, file_name_changed_licenses), index_col=False, header=0)

merged = pd.merge(changed_csv, created_csv, left_on="license_id", right_on="id", how="left")

# rules

# Aucune modification avant la date de création d'une licence

rule_creation_date = lambda merged : merged["date"] >= merged["creation_date"]

# Pas d'identifiants dupliqués

rule_non_duplicate_id = lambda x: ~x["id"].duplicated()

# Tous les license_id existent dans initial_licenses.csv

rule_id_exist = lambda chgd, init: chgd["id"].isin(init["license_id"])
# Les types sont valides ( PASS ,SIM , SUPERVISION )

rule_type_ok = lambda x : x["type"].isin(["PASS", "SIM", "SUPERVISION"])
# Les prix sont dans la plage attendue
rule_prices = lambda x: (x["price"] >= 0) & (x["price"] <= 5000)
# Les distributions des caractéristiques
# check if there are less constumer than ids
rule_distr_1 = lambda chgd, init: chgd["customer_id"].nunique() < init["id"].nunique()
# check if renewable are all set to True in created_csv
rule_distr_2 = lambda x : x["renew"] == True

# check if there are any dates in the future

ruleset = {
    "date_modif": (rule_creation_date, (merged,),),
    "non_duplicated_id": (rule_non_duplicate_id,(created_csv,),),
    "id_exists": (rule_id_exist, (created_csv, changed_csv,),),
    "type_ok_changed_csv": (rule_type_ok, (changed_csv,),),
    "type_ok_created_csv": (rule_type_ok, (created_csv,),),
    "price_ok_changed_csv": (rule_prices, (changed_csv,),),
    "price_ok_created_csv": (rule_prices, (created_csv,),),
}

logging_df = pd.DataFrame()
logging_df["is_valid"] = True
for rule_name, (rule, args) in ruleset.items():

    result = rule(*args)
    
    logging_df[f"{rule_name}_valid"] = result
    logging_df["is_valid"] &= result
    
    if isinstance(result, Iterable):
        # row level checks
        invalid_count = (~result).sum()

        if invalid_count > 0:
            logging.warning(
                f"Rule '{rule_name}' failed for {invalid_count} rows "
                f"({invalid_count/len(logging_df):.2%})"
            )
        else:
            logging.info(f"Rule '{rule_name}' passed")
    else:
        # columns level checks
        if result:
            logging.warning(
                f"More unique IDs ({logging_df['id'].nunique()}) than customers ({logging_df['customer'].nunique()})"
            )
        else:
            
            logging.info(f"Rule '{rule_name}' passed")

