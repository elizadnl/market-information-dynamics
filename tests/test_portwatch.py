from __future__ import annotations

import pandas as pd

from market_information_dynamics.data.portwatch import (
    PortWatchClient,
    build_chokepoint_feature_panel,
    portwatch_features_to_releases,
)


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self):
        self.calls = []

    def get(self, url, params, timeout):
        self.calls.append((url, params, timeout))
        if "PortWatch_chokepoints_database" in url:
            return FakeResponse(
                {
                    "features": [
                        {"attributes": {"portid": "chokepoint1", "portname": "Suez Canal"}},
                        {
                            "attributes": {
                                "portid": "chokepoint6",
                                "portname": "Strait of Hormuz",
                            }
                        },
                        {
                            "attributes": {
                                "portid": "chokepoint10",
                                "portname": "Malacca Strait",
                            }
                        },
                    ],
                    "exceededTransferLimit": False,
                }
            )

        offset = int(params["resultOffset"])
        if offset == 0:
            return FakeResponse(
                {
                    "features": [
                        {
                            "attributes": {
                                "date": 1_546_300_800_000,
                                "portid": "chokepoint1",
                                "portname": "Suez Canal",
                                "capacity": 4_000_000,
                                "n_total": 80,
                            }
                        },
                        {
                            "attributes": {
                                "date": 1_546_387_200_000,
                                "portid": "chokepoint1",
                                "portname": "Suez Canal",
                                "capacity": 4_100_000,
                                "n_total": 82,
                            }
                        },
                    ],
                    "exceededTransferLimit": True,
                }
            )
        return FakeResponse({"features": [], "exceededTransferLimit": False})


def test_portwatch_client_resolves_and_paginates():
    session = FakeSession()
    client = PortWatchClient(session=session, page_size=2)
    frame = client.chokepoints(names=["Suez Canal"], metrics=["capacity", "n_total"])

    assert list(frame["portname"].unique()) == ["Suez Canal"]
    assert len(frame) == 2
    assert len(session.calls) == 3  # tiny catalog + first page + terminating empty page
    assert "PortWatch_chokepoints_database" in session.calls[0][0]


def test_chokepoint_features_are_future_invariant():
    dates = pd.date_range("2020-01-01", periods=500, freq="D")
    raw = pd.DataFrame(
        {
            "date": dates,
            "portname": "Suez Canal",
            "capacity": 1_000_000 + pd.Series(range(500)).to_numpy() * 1_000,
            "n_total": 50 + (pd.Series(range(500)) % 7).to_numpy(),
        }
    )
    base = build_chokepoint_feature_panel(raw, min_periods=30)

    changed = raw.copy()
    changed.loc[changed.index >= 450, "capacity"] *= 100
    alt = build_chokepoint_feature_panel(changed, min_periods=30)

    pd.testing.assert_frame_equal(base.loc[: dates[449]], alt.loc[: dates[449]])


def test_portwatch_release_lag_is_explicit():
    features = pd.DataFrame(
        {"pw_suez_capacity_z": [0.2, 0.3]},
        index=pd.to_datetime(["2026-01-01", "2026-01-02"]),
    )
    releases = portwatch_features_to_releases(features, availability_lag_days=7)
    assert releases.loc[0, "available_at"] == pd.Timestamp("2026-01-08")
    assert releases.loc[0, "source"] == "IMF PortWatch"


def test_portwatch_name_resolution_handles_word_order_alias():
    session = FakeSession()
    client = PortWatchClient(session=session, page_size=2)
    resolved = client.resolve_chokepoints(["Strait of Malacca"])
    assert resolved.loc[0, "portname"] == "Malacca Strait"


def test_seasonal_yoy_features_are_future_invariant():
    dates = pd.date_range("2019-01-01", periods=900, freq="D")
    raw = pd.DataFrame(
        {
            "date": dates,
            "portname": "Suez Canal",
            "capacity": 2_000_000 + 200_000 * pd.Series(range(900)).map(lambda x: __import__('math').sin(2 * __import__('math').pi * x / 364)).to_numpy(),
            "n_total": 80 + (pd.Series(range(900)) % 7).to_numpy(),
        }
    )
    base = build_chokepoint_feature_panel(
        raw, method="seasonal_yoy", seasonal_lag_days=364, min_periods=30
    )
    changed = raw.copy()
    changed.loc[changed.index >= 850, "capacity"] *= 3
    alt = build_chokepoint_feature_panel(
        changed, method="seasonal_yoy", seasonal_lag_days=364, min_periods=30
    )
    pd.testing.assert_frame_equal(base.loc[: dates[849]], alt.loc[: dates[849]])


class FlakySession(FakeSession):
    def __init__(self):
        super().__init__()
        self.failures_remaining = 1

    def get(self, url, params, timeout):
        import requests

        self.calls.append((url, params, timeout))
        if self.failures_remaining:
            self.failures_remaining -= 1
            raise requests.exceptions.ReadTimeout("temporary ArcGIS timeout")
        if "PortWatch_chokepoints_database" in url:
            return FakeResponse(
                {
                    "features": [
                        {"attributes": {"portid": "chokepoint1", "portname": "Suez Canal"}}
                    ],
                    "exceededTransferLimit": False,
                }
            )
        return FakeResponse({"features": [], "exceededTransferLimit": False})


def test_portwatch_retries_transient_timeouts():
    session = FlakySession()
    client = PortWatchClient(session=session, max_retries=2, retry_backoff_seconds=0)
    catalog = client.list_chokepoints()
    assert catalog.loc[0, "portname"] == "Suez Canal"
    assert len(session.calls) == 2


def test_portwatch_chunked_download_is_resumable(tmp_path):
    session = FakeSession()
    client = PortWatchClient(session=session, page_size=2)
    first = client.chokepoints(
        names=["Suez Canal"],
        observation_start="2019-01-01",
        observation_end="2019-12-31",
        metrics=["capacity", "n_total"],
        cache_dir=tmp_path,
    )
    assert len(first) == 2
    cache_files = list(tmp_path.glob("*.csv"))
    assert len(cache_files) == 1
    first_call_count = len(session.calls)
    assert first_call_count == 3  # catalog + data page + terminating page

    # A second run still resolves the tiny live catalog but reuses the completed
    # historical year chunk instead of querying the large daily service again.
    session.calls.clear()
    second = client.chokepoints(
        names=["Suez Canal"],
        observation_start="2019-01-01",
        observation_end="2019-12-31",
        metrics=["capacity", "n_total"],
        cache_dir=tmp_path,
    )
    pd.testing.assert_frame_equal(first, second)
    assert len(session.calls) == 1
    assert "PortWatch_chokepoints_database" in session.calls[0][0]
