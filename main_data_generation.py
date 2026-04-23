
import os
import numpy as np
import pandas as pd

from utils.markov_chain import simulate_markov_single
from utils.data_generation import generate_creation_dates, generate_pareto, generate_type_licenses, generate_dates

# parameters
RANDOM_SEED = 1234

# files
file_name_init_licenses = "initial_licenses.csv"
file_name_changed_licenses = "license_changes.csv"
folder_name = "csv"

# data generation parameters
nb_id: int = 100 # number of license_id
nb_modif: int = 10_000

nb_customer_ids: int = 20  # number of different customer
prop_customer_1_license = .4
prop_customer_2_licenses = .4


min_param_date: str = '2023-01-01'
prop_contract_created_Q1: float = 0.5
# prop_contract_created_across_years: tuple = (3, .3, .3, .1,)

max_price = 5000
# let 's assume there are 3 different subscription prices:
# PASS : 100
# SIM : 1000
# SUPERVISION : 5000

type_license_available = ("PASS", "SIM", "SUPERVISION",)
type_prob_distr = (.5, .3, .2,)
mapping_price_type = {"PASS":100,  "SIM":1000, "SUPERVISION": 5000}

# using markov chain to generate several states
# transition matrix 
transition_matrix = np.array([[.2, .6, .1, .1, .0, .0  ],# type:PASS
                              [.1, .5, .2, .0, .2, .0],#type: SUPERVISION
                              [.3, .3, .3, .0, .0, .1], # type: SIM
                              [1., .0, .0, .0,.0 , .0, ], # type : renew_pass
                              [.0, 1., .0, .0 ,.0, .0, ], # type: renew_supervision
                              [.0, .0, 1., .0, .0, .0] # type: renew sim
                              ])

state_labels = np.array(["PASS", "SUPERVISION", "SIM", "RENEW_PASS", "RENEW_SUPERVISION", "RENEW_SIM",])

if __name__ == '__main__':

    np.random.seed(RANDOM_SEED)
    # buiding csv 1: 
    license_id = np.arange(1, nb_id+1)
    start = np.datetime64(min_param_date)
    dates = generate_creation_dates(nb_id, start, q1_ratio=prop_contract_created_Q1)
    # prices = generate_subscription(subscription_prices, subscription_prob, nb_id)
    types = generate_type_licenses(type_license_available, type_prob_distr, nb_id)
    prices = np.array([mapping_price_type[t] for t in types])  # associate each price to a given sbscription
    customer_id = generate_pareto(license_id, total_size=nb_id, alpha=1.5)
    print(dates)

    init_licenses = {"id": license_id, "customer_id": customer_id, "type": types, "creation_date": dates, 
        "price": prices, "renewable": np.array(nb_id*[True])}


    df = pd.DataFrame(init_licenses)
    df.to_csv(os.path.join(folder_name, file_name_init_licenses), index=False)


    # building csv 2
    # date

    license_changed = generate_pareto(license_id, total_size=nb_modif, alpha=2.1)
    print("modif")

    license_changed_mapped = {v: license_changed.count(v) for v in license_changed}


    print("test gen dates", generate_creation_dates(1,start))

    dates, changed_types, changed_renewed_states, changed_prices = {}, {}, {}, {}
    # changed_licensed = {}
    created_licenses = {"license_id": [], "date": [], "price": [], "type":[], "renewable": []}
    for k,v in license_changed_mapped.items():
        idx = np.argwhere(init_licenses["id"] ==k)
        start_d = init_licenses["creation_date"][idx]
        # import pdb; pdb.set_trace()
        dates[k] = generate_dates(start_d[0][0], v)
        t, r = simulate_markov_single(dates[k], init_licenses["type"][int(idx[0][0])], transition_matrix,
                                    np.array(["PASS", "SUPERVISION", "SIM", "RENEW_PASS", "RENEW_SUPERVISION", "RENEW_SIM",]))
        changed_types[k] = t
        changed_renewed_states[k] = r
        changed_prices[k] = [mapping_price_type[u] for u in t]
        # changed_licensed[k]= v*[k]
        created_licenses["license_id"].extend(v*[k])
        created_licenses["date"].extend(dates[k])
        created_licenses["price"].extend(changed_prices[k])
        created_licenses["type"].extend(t)
        created_licenses["renewable"].extend(r)
    print(dates)

    print("checks", [len(v) for v in created_licenses.values()])

    df2 = pd.DataFrame(created_licenses)

    df2.to_csv(os.path.join(folder_name, file_name_changed_licenses), index=False)

    print("Data generation completed")
