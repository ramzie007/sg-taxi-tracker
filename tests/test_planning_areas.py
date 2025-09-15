import os
import pytest
import typer
from typer.testing import CliRunner
import pandas as pd
print(os.getcwd())
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/../'))
import planning_areas
from dotenv import load_dotenv

# Set up environment variables for testing (use dummy or real tokens)
load_dotenv()
ONE_MAP_API_TOKEN = os.getenv("ONE_MAP_API_TOKEN", "dummy_token")
DATA_SG_API = os.getenv("DATA_SG_API", "dummy_token")

@pytest.mark.skipif(
    ONE_MAP_API_TOKEN == "dummy_token" or DATA_SG_API == "dummy_token",
    reason="API tokens not set for integration test."
)
def test_fetch_planning_areas():
    df = planning_areas.fetch_planning_areas(ONE_MAP_API_TOKEN)
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "geojson" in df.columns

@pytest.mark.skipif(
    DATA_SG_API == "dummy_token",
    reason="API token not set for integration test."
)
def test_fetch_taxi_availability():
    df = planning_areas.fetch_taxi_availability(DATA_SG_API)
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert set(["lat", "long"]).issubset(df.columns)

def test_main_top_k_1(monkeypatch):
    # Monkeypatch environment variables for CLI
    monkeypatch.setenv("ONE_MAP_API_TOKEN", ONE_MAP_API_TOKEN)
    monkeypatch.setenv("DATA_SG_API", DATA_SG_API)
    runner = CliRunner()
    result = runner.invoke(planning_areas.app, ["--top-k", "1"])
    assert "Total Available Taxis" in result.output
