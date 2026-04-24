import tempfile
import os
import pandas as pd
import pytest
from app.main_data_generation import generate_data

@pytest.fixture(scope="class")
def df_data():
    """Generates dataset from generate_data"""
    
    with tempfile.TemporaryDirectory() as tmpdirname:
        print('created temporary directory', tmpdirname)
        _foler_name = os.path.join("tests", tmpdirname)
        _init_file, _chgd_file = "init.csv", "chgd.csv"
        generate_data(10, 20, 321,
                       file_name_init_licenses=_init_file,
                       file_name_changed_licenses=_chgd_file,
                       folder_name=_foler_name)
        init_data = pd.read_csv(os.path.join(_foler_name, _init_file), parse_dates=["creation_date"])
        chgd_data = pd.read_csv(os.path.join(_foler_name, _chgd_file), parse_dates=["date"])
    #request.cls.df_init = init_data
    yield init_data, chgd_data
    # request.cls.df_chgd = chgd_data



class TestDataIntegrityInitialLicenses:
    # data consistency for generated initial_licenses.csv file
    def test_01_no_missing_values(self, df_data):
        df_init, df_chgd = df_data
        assert not df_init.isnull().any().any(), "There are missing values"
        assert not df_chgd.isnull().any().any(), "There are missing values"

    def test_02_unique_id(self, df_data):
        df_init, df_chgd = df_data
        assert df_init["id"].is_unique, "IDs must be unique"
        assert df_chgd["id"].is_unique, "IDs must be unique"

    def test_03_positive_price(self, df_data):
        df_init, df_chgd = df_data
        assert (df_init["price"] > 0).all(), "Prices must be positive"
        assert (df_chgd["price"] > 0).all(), "Prices must be positive"

    def test_04_valid_types(self, df_data):
        df_init, df_chgd = df_data
        valid_types = {"SIM", "PASS", "SUPERVISION"}
        assert set(df_init["type"]).issubset(valid_types), "Invalid types found"

    def test_05_price_by_type(self, df_data):
        df_init, df_chgd = df_data
        expected_prices = {
            "SIM": 1000,
            "PASS": 100,
            "SUPERVISION": 5000
        }
        for t, price in expected_prices.items():
            subset_init = df_init[df_init["type"] == t]
            subset_chgd = df_chgd[df_chgd["type"] == t]
            assert (subset_init["price"] == price).all(), f"Wrong price for {t}"
            assert (subset_chgd["price"] == price).all(), f"Wrong price for {t}"
    
    def test_06_creation_date_not_future(self, df_data):
        df_init, df_chgd = df_data
        today = pd.Timestamp.today()
        assert (df_init["creation_date"] <= today).all(), "Future dates found"
        assert (df_chgd["date"] <= today).all(), "Future dates found"


    def test_07_id_positive(self, df_data):
        df_init, df_chgd = df_data
        assert (df_init["customer_id"] > 0).all(), "Customer IDs must be positive"
        assert (df_chgd["license_id"] > 0).all(), "Customer IDs must be positive"

    def test_08_renewable_boolean(self, df_data):
        df_init, df_chgd = df_data
        assert df_init["renewable"].isin([True, False]).all(), "Renewable must be boolean"
        assert df_chgd["renewable"].isin([True, False]).all(), "Renewable must be boolean"