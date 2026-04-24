import pandas as pd
import pytest
from unittest.mock import MagicMock
import app.transformation as m  


@pytest.fixture
def created_csv():
    return pd.DataFrame({
        "id": [1, 2],
        "creation_date": ["2024-01-01", "2024-01-02"],
        "renewable": [True, True],
        "price": [10, 20],
        "type": ["A", "A"]
    })


@pytest.fixture
def changed_csv():
    return pd.DataFrame({
        "license_id": [1],
        "date": ["2024-01-03"],
        "id": [100],
        "renewable": [False],
        "price": [10],
        "type": ["A"]
    })

class TestPipeline:
    def test_01_load_data(self, monkeypatch, created_csv, changed_csv):

        def fake_read_csv(path, *args, **kwargs):
            if "initial" in path:
                return created_csv.copy()
            return changed_csv.copy()

        monkeypatch.setattr(m.pd, "read_csv", fake_read_csv)

        created, changed = m.load_data("folder", "initial.csv", "changed.csv")

        assert "creation_date" in created.columns
        assert "date" in changed.columns
    
    def test_02_build_states(self, created_csv, changed_csv):

        states = m.build_states(created_csv.copy(), changed_csv.copy())

        assert "license_id" in states.columns
        assert not states.empty


    def test_04_compute_daily_events(self):

        states = pd.DataFrame({
            "date": pd.to_datetime(["2024-01-01"]).date,
            "type": ["ABC"],
            "activated": [1],
            "deactivated": [0]
        })

        all_dates = pd.date_range("2024-01-01", "2024-01-02")

        out = m.compute_daily_events(states, all_dates)

        assert "activated_licenses" in out.columns
        assert "deactivated_licenses" in out.columns

    def test_05_compute_counts(self, created_csv):

        daily_states = pd.DataFrame({
            "date": pd.to_datetime(["2024-01-01", "2024-01-02"]),
            "type": ["A", "A"],
            "renewable": [True, False]
        })

        all_dates = pd.to_datetime(["2024-01-01", "2024-01-02"])

        result = m.compute_counts(daily_states, created_csv, all_dates)

        # basic sanity checks
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert "active_license_count" in result.columns

    def test_06_compute_price(self):

         # -----------------------
        # Input: daily_states
        # -----------------------
        daily_states = pd.DataFrame({
            "date": pd.to_datetime([
                "2024-01-01",
                "2024-01-01",
                "2024-01-02"
            ]),
            "type": ["A", "A", "A"],
            "renewable": [True, False, True],
            "price": [10, 20, 30]
        })

        # -----------------------
        # Input: all_dates
        # -----------------------
        all_dates = pd.to_datetime([
            "2024-01-01",
            "2024-01-02"
        ])

        # -----------------------
        # Run function
        # -----------------------
        result = m.compute_price(daily_states, all_dates)

        # -----------------------
        # Assertions
        # -----------------------

        # shape: 2 dates × 1 type = 2 rows
        assert len(result) == 2

        # check columns exist
        assert "active_license_price" in result.columns

        # check type consistency
        assert result["type"].unique().tolist() == ["A"]

        # -----------------------
        # Expected values
        # -----------------------
        # active_value = renewable * price
        # 2024-01-01: 10 + 0 = 10
        # 2024-01-02: 30
        expected = {
            pd.Timestamp("2024-01-01"): 10,
            pd.Timestamp("2024-01-02"): 30
        }

        actual = dict(zip(result["date"], result["active_license_price"]))

        assert actual == expected
