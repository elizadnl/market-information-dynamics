import pandas as pd

from market_information_dynamics.data.fred import FREDClient


class FakeResponse:
    text = "DATE,AAA\n2026-01-01,1.0\n2026-01-02,.\n2026-01-03,1.2\n"

    def raise_for_status(self):
        return None


class FakeSession:
    def get(self, url, params=None, timeout=None):
        assert "fredgraph.csv" in url
        assert params == {"id": "AAA"}
        return FakeResponse()


def test_fred_csv_fallback_without_api_key():
    client = FREDClient(api_key=None, mode="csv", session=FakeSession())
    s = client.series("AAA", observation_start="2026-01-02")
    assert s.index.min() == pd.Timestamp("2026-01-02")
    assert pd.isna(s.loc[pd.Timestamp("2026-01-02")])
    assert s.loc[pd.Timestamp("2026-01-03")] == 1.2
