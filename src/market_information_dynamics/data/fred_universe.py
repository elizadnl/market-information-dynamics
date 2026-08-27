from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from market_information_dynamics.data.fred import FREDClient
from market_information_dynamics.data.transforms import transform_series


def load_fred_universe(
    config_path: str | Path,
    *,
    observation_start: str | None = None,
    observation_end: str | None = None,
    client: FREDClient | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Download and transform FRED nodes declared in a YAML universe config.

    Returns `(panel, metadata)`. The panel uses the intersection of transformed
    observations; no unrestricted forward filling is performed.
    """
    config = yaml.safe_load(Path(config_path).read_text())
    nodes = [n for n in config.get("financial", []) if n.get("source") == "FRED"]
    if not nodes:
        raise ValueError("No FRED financial nodes found in config")
    client = client or FREDClient()

    series = []
    metadata = []
    for node in nodes:
        raw = client.series(
            node["series_id"],
            observation_start=observation_start,
            observation_end=observation_end,
        ).rename(node["id"])
        transformed = transform_series(raw, node.get("transform", "level"))
        series.append(transformed)
        metadata.append(
            {
                "id": node["id"],
                "source": "FRED",
                "series_id": node["series_id"],
                "family": node.get("family"),
                "transform": node.get("transform", "level"),
                "role": node.get("role"),
            }
        )

    panel = pd.concat(series, axis=1).sort_index().dropna(how="any")
    return panel, pd.DataFrame(metadata)
