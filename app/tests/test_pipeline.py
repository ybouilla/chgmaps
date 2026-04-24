import subprocess
import sys
import os
import pytest
import pandas as pd

from app.transformation import load_data, transform_pipeline

# uv run python -m app.main_data_generation --nb_id 10 --nb_modif 500 --rand_seed 0101 --created_license_name test_initial_licenses.csv --changed_license_name test_chg_license.csv --folder_name tests/test_csv

class TestPipeline:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        # tmp_path: pytest's utility for temporay tests
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.folder_name = os.path.join(dir_path,"test_csv")
        self.init_data = "test_initial_licenses.csv"
        self.chgd_data = "test_chg_license.csv"
        if (not os.path.exists(os.path.join(self.folder_name, self.init_data))
            or not os.path.exists(os.path.join(self.folder_name, self.chgd_data))):
            pytest.skip("Input files do not exist — skipping test")
        self.transformed_data = os.path.join(tmp_path, "trsf.csv")

        self.prices = {"PASS": 100,
                       "SUPERVISION": 5000,
                       "SIM": 1000}

    @staticmethod
    def check_positivity(x: pd.Series | pd.DataFrame, name: str) -> bool:
        return (x[name] >= 0).all()

    def test_run_pipeline(self):
        folder_name=self.folder_name
        init_file=self.init_data
        changed_file=self.chgd_data
        output_file=self.transformed_data
        created_csv, changed_csv = load_data(folder_name, init_file, changed_file)
        trsf_data = transform_pipeline(created_csv, changed_csv)
        # Assert file was created
        # assert os.path.exists(self.transformed_data)

        # # Assert it's not empty
        # assert os.path.getsize(self.transformed_data) > 0

        # check data transformed_data file integrity

        # trsf_data = pd.read_csv(self.transformed_data, index_col=False)
        _expected_columns = set(("date", "type", "active_license_count", "active_license_price", "inactive_license_count",
                   "daily_active_diff", "daily_price_diff", "daily_inactive_diff",))
        
        assert _expected_columns == set(trsf_data.columns.values)

        assert set(trsf_data["type"]).issubset(set(self.prices))

        assert self.check_positivity(trsf_data, "active_license_count")
        
        assert self.check_positivity(trsf_data, "active_license_price")
        assert self.check_positivity(trsf_data, "inactive_license_count",)

        # check active_license_price = active_license_count * price
        assert (trsf_data["active_license_price"] == trsf_data["active_license_count"] * trsf_data["type"].map(self.prices)).all()
