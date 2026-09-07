from __future__ import annotations

import io
import os
from dataclasses import dataclass, field

import pandas as pd

from market_information_dynamics.http import activate_system_trust_store

activate_system_trust_store()

import requests


@dataclass
class FREDClient:
    """Small FRED client with an unauthenticated CSV fallback.

    ``mode='auto'`` uses the official JSON API when a FRED API key is available and
    otherwise falls back to FRED's public ``fredgraph.csv`` endpoint. The fallback keeps
    the repository runnable for reviewers without credentials, while the official API is
    preferred for reproducible research runs where metadata/release controls are needed.
    """

    api_key: str | None = None
    timeout: int = 30
    mode: str = "auto"
    session: requests.Session = field(default_factory=requests.Session)

    def __post_init__(self) -> None:
        self.api_key = self.api_key or os.getenv("FRED_API_KEY")
        if self.mode not in {"auto", "api", "csv"}:
            raise ValueError("mode must be one of: auto, api, csv")
        if self.mode == "api" and not self.api_key:
            raise ValueError("mode='api' requires FRED_API_KEY or api_key=...")

    @property
    def backend(self) -> str:
        if self.mode == "csv":
            return "fredgraph_csv"
        if self.mode == "api":
            return "fred_api"
        return "fred_api" if self.api_key else "fredgraph_csv"

    def series(
        self,
        series_id: str,
        observation_start: str | None = None,
        observation_end: str | None = None,
    ) -> pd.Series:
        if self.backend == "fred_api":
            return self._series_api(series_id, observation_start, observation_end)
        return self._series_csv(series_id, observation_start, observation_end)

    def _series_api(
        self,
        series_id: str,
        observation_start: str | None,
        observation_end: str | None,
    ) -> pd.Series:
        params: dict[str, str] = {
            "series_id": series_id,
            "api_key": str(self.api_key),
            "file_type": "json",
        }
        if observation_start:
            params["observation_start"] = observation_start
        if observation_end:
            params["observation_end"] = observation_end

        response = self.session.get(
            "https://api.stlouisfed.org/fred/series/observations",
            params=params,
            timeout=self.timeout,
        )
        response.raise_for_status()
        observations = response.json()["observations"]
        frame = pd.DataFrame(observations)
        return _frame_to_series(frame, series_id, observation_start, observation_end)

    def _series_csv(
        self,
        series_id: str,
        observation_start: str | None,
        observation_end: str | None,
    ) -> pd.Series:
        response = self.session.get(
            "https://fred.stlouisfed.org/graph/fredgraph.csv",
            params={"id": series_id},
            timeout=self.timeout,
        )
        response.raise_for_status()
        frame = pd.read_csv(io.StringIO(response.text))
        value_cols = [c for c in frame.columns if c.upper() == series_id.upper()]
        if not value_cols:
            raise RuntimeError(f"FRED CSV response did not contain {series_id!r}")
        frame = frame.rename(columns={frame.columns[0]: "date", value_cols[0]: "value"})
        return _frame_to_series(frame[["date", "value"]], series_id, observation_start, observation_end)


def _frame_to_series(
    frame: pd.DataFrame,
    series_id: str,
    observation_start: str | None,
    observation_end: str | None,
) -> pd.Series:
    data = frame.copy()
    data["date"] = pd.to_datetime(data["date"])
    data["value"] = pd.to_numeric(data["value"], errors="coerce")
    if observation_start:
        data = data.loc[data["date"] >= pd.Timestamp(observation_start)]
    if observation_end:
        data = data.loc[data["date"] <= pd.Timestamp(observation_end)]
    return data.set_index("date")["value"].rename(series_id).sort_index()
