import pandas as pd
from unittest.mock import MagicMock
import pytest
import os
import app.validate_csv as m
from app.validate_csv import (
    rule_creation_date,
    rule_non_duplicate_id,
    rule_id_exist,
    rule_type_ok,
    rule_prices,

)


class TestRules:
        # simple test for rules
    def test_01_rule_creation_date(self):
        df = pd.DataFrame({
            "date": pd.to_datetime(["2024-01-10", "2024-02-01"]),
            "creation_date": pd.to_datetime(["2024-01-01", "2024-02-05"]),
        })

        result = rule_creation_date(df)
        assert result.tolist() == [True, False]

    def test_02_rule_non_duplicate_id(self):
        df = pd.DataFrame({
            "id": [1, 2, 2, 3]
        })

        result = rule_non_duplicate_id(df)
        assert result.tolist() == [True, True, False, True]

    def test_03_rule_id_exist(self):
        chgd = pd.DataFrame({"id": [1, 2, 3, 4]})
        init = pd.DataFrame({"license_id": [1, 3, 5]})

        result = rule_id_exist(chgd, init)
        assert result.tolist() == [True, False, True, False]

    def test_04_rule_type_ok(self):
        df = pd.DataFrame({
            "type": ["PASS", "SIM", "INVALID", "SUPERVISION"]
        })

        result = rule_type_ok(df)
        assert result.tolist() == [True, True, False, True]

    def test_05_rule_prices(self):
        df = pd.DataFrame({
            "price": [-10, 0, 2500, 5000, 6000]
        })

        result = rule_prices(df)
        assert result.tolist() == [False, True, True, True, False]


class TestMain:
    # test validate main script
    @pytest.fixture
    def csv_files(tmp_path):
        folder = os.path.join(tmp_path, "csv")
        folder.mkdir()

        init_file = folder / "init.csv"
        changed_file = folder / "changed.csv"

        init_df = pd.DataFrame({
            "id": [1, 2],
            "renew": [True, True],
            "customer": ["A", "B"]
        })

        changed_df = pd.DataFrame({
            "license_id": [1, 2],
            "customer_id": ["A", "B"],
            "price": [10, 20]
        })

        init_df.to_csv(init_file, index=False)
        changed_df.to_csv(changed_file, index=False)

        return init_file.name, changed_file.name, folder.name

    def setup_method(self):
        """Runs before each test"""
        self.mock_info = MagicMock()
        self.mock_warning = MagicMock()

    def patch_logging(self, monkeypatch):
        monkeypatch.setattr(m.logging, "info", self.mock_info)
        monkeypatch.setattr(m.logging, "warning", self.mock_warning)
    
    def test_row_level_failure(self, monkeypatch, csv_files):
        init_name, changed_name, folder = csv_files

        self.patch_logging(monkeypatch)

        monkeypatch.setattr(
            m,
            "rule_creation_date",
            lambda *a: pd.Series([True, False])
        )

        monkeypatch.setattr(m, "rule_non_duplicate_id", lambda *a: True)
        monkeypatch.setattr(m, "rule_id_exist", lambda *a: True)
        monkeypatch.setattr(m, "rule_type_ok", lambda *a: True)
        monkeypatch.setattr(m, "rule_prices", lambda *a: True)

        m.main(init_name, changed_name, folder)

        self.mock_warning.assert_called()