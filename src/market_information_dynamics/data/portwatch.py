from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
import time

import numpy as np
import pandas as pd

from market_information_dynamics.http import activate_system_trust_store

activate_system_trust_store()

import requests

CHOKEPOINT_QUERY_URL = (
    "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/"
    "Daily_Chokepoints_Data/FeatureServer/0/query"
)
CHOKEPOINT_CATALOG_QUERY_URL = (
    "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/"
    "PortWatch_chokepoints_database/FeatureServer/0/query"
)


def _normalise_name(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", text.casefold()).strip()


def _slug(value: str) -> str:
    return _normalise_name(value).replace(" ", "_")


@dataclass
class PortWatchClient:
    """Minimal client for IMF PortWatch's public ArcGIS chokepoint feed.

    The endpoint is public and does not require authentication. Pagination is handled
    explicitly because ArcGIS services cap the number of returned records per request.
    """

    timeout: int = 90
    page_size: int = 1000
    max_retries: int = 4
    retry_backoff_seconds: float = 1.5
    session: requests.Session = field(default_factory=requests.Session)

    def _query(
        self,
        *,
        where: str,
        out_fields: Iterable[str],
        order_by: str | None = None,
        return_distinct: bool = False,
        url: str = CHOKEPOINT_QUERY_URL,
    ) -> pd.DataFrame:
        offset = 0
        rows: list[dict] = []
        fields = ",".join(out_fields)

        while True:
            params: dict[str, object] = {
                "where": where,
                "outFields": fields,
                "returnGeometry": "false",
                "f": "json",
                "resultOffset": offset,
                "resultRecordCount": self.page_size,
            }
            if order_by:
                params["orderByFields"] = order_by
            if return_distinct:
                params["returnDistinctValues"] = "true"

            last_error: Exception | None = None
            for attempt in range(self.max_retries + 1):
                try:
                    response = self.session.get(url, params=params, timeout=self.timeout)
                    response.raise_for_status()
                    break
                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
                    last_error = exc
                    if attempt >= self.max_retries:
                        raise
                    time.sleep(self.retry_backoff_seconds * (2**attempt))
            else:  # pragma: no cover - defensive; loop either breaks or raises
                assert last_error is not None
                raise last_error
            payload = response.json()
            if "error" in payload:
                raise RuntimeError(f"PortWatch ArcGIS error: {payload['error']}")

            features = payload.get("features", [])
            rows.extend(feature.get("attributes", {}) for feature in features)

            if not features:
                break
            if "exceededTransferLimit" in payload:
                if not bool(payload["exceededTransferLimit"]):
                    break
            elif len(features) < self.page_size:
                break
            offset += len(features)

        return pd.DataFrame(rows)

    def list_chokepoints(self) -> pd.DataFrame:
        # Use the tiny 28-row PortWatch chokepoint catalogue rather than asking the
        # 78k+ row daily table to compute a DISTINCT scan. The latter can time out on
        # ArcGIS Online even though only two fields are requested.
        frame = self._query(
            where="1=1",
            out_fields=["portid", "portname"],
            order_by="portname ASC",
            url=CHOKEPOINT_CATALOG_QUERY_URL,
        )
        if frame.empty:
            return pd.DataFrame(columns=["portid", "portname"])
        return frame[["portid", "portname"]].drop_duplicates().sort_values("portname").reset_index(
            drop=True
        )

    def resolve_chokepoints(self, names: Iterable[str]) -> pd.DataFrame:
        catalog = self.list_chokepoints()
        if catalog.empty:
            raise RuntimeError("PortWatch returned no chokepoint metadata")

        normalised = catalog["portname"].map(_normalise_name)
        resolved: list[pd.Series] = []
        for requested in names:
            key = _normalise_name(requested)
            exact = catalog.loc[normalised == key]
            if len(exact) == 1:
                resolved.append(exact.iloc[0])
                continue

            partial = catalog.loc[normalised.map(lambda x: key in x or x in key)]
            if len(partial) == 1:
                resolved.append(partial.iloc[0])
                continue

            # PortWatch naming can change word order (for example "Strait of Malacca"
            # versus "Malacca Strait"). Token overlap + sequence similarity is used only
            # for resolution; the canonical live PortWatch name is retained in the data.
            requested_tokens = set(key.split()) - {"of", "the"}
            scored = []
            for idx, candidate in normalised.items():
                candidate_tokens = set(candidate.split()) - {"of", "the"}
                union = requested_tokens | candidate_tokens
                jaccard = len(requested_tokens & candidate_tokens) / len(union) if union else 0.0
                sequence = SequenceMatcher(None, key, candidate).ratio()
                scored.append((0.7 * jaccard + 0.3 * sequence, idx))
            scored.sort(reverse=True)
            if not scored or scored[0][0] < 0.70 or (len(scored) > 1 and scored[0][0] - scored[1][0] < 0.10):
                matches = catalog.iloc[[idx for _, idx in scored[:5]]]["portname"].tolist() if scored else []
                raise ValueError(
                    f"Could not uniquely resolve chokepoint {requested!r}; candidates={matches}"
                )
            resolved.append(catalog.loc[scored[0][1]])

        return pd.DataFrame(resolved).reset_index(drop=True)

    def _parse_observations(
        self,
        frame: pd.DataFrame,
        *,
        metrics: Iterable[str],
    ) -> pd.DataFrame:
        if frame.empty:
            return frame
        frame = frame.copy()
        raw_dates = frame["date"]
        numeric_dates = pd.to_numeric(raw_dates, errors="coerce")
        if numeric_dates.notna().mean() > 0.95:
            frame["date"] = pd.to_datetime(numeric_dates, unit="ms", utc=True).dt.tz_convert(None)
        else:
            frame["date"] = pd.to_datetime(raw_dates, errors="coerce", utc=True).dt.tz_convert(None)
        if frame["date"].isna().all():
            raise RuntimeError("PortWatch returned an unparseable date field")
        for metric in metrics:
            frame[metric] = pd.to_numeric(frame[metric], errors="coerce")
        return frame

    def chokepoints(
        self,
        *,
        names: Iterable[str],
        observation_start: str | None = None,
        observation_end: str | None = None,
        metrics: Iterable[str] = ("capacity", "n_total"),
        cache_dir: str | Path | None = "data/cache/portwatch",
    ) -> pd.DataFrame:
        """Download daily chokepoint observations using small resumable chunks.

        ArcGIS Online can time out on one large multi-port historical query. When a
        date range is supplied, this client instead requests one chokepoint-year at a
        time (normally <= 366 rows), writes each completed chunk to a local cache, and
        reuses those files on the next run. This makes public-research restartable after
        transient network failures without weakening TLS verification.
        """
        metrics = tuple(metrics)
        resolved = self.resolve_chokepoints(names)
        fields = ["date", "portid", "portname", *metrics]

        start_ts = pd.Timestamp(observation_start) if observation_start else None
        end_ts = pd.Timestamp(observation_end) if observation_end else pd.Timestamp.today().normalize()

        # Without a lower boundary preserve the generic paginated path. The empirical
        # configuration always supplies a start date, so real research uses the safer
        # per-port/year downloader below.
        if start_ts is None:
            port_ids = resolved["portid"].astype(str).tolist()
            clauses = [f"portid='{port_id.replace(chr(39), chr(39) * 2)}'" for port_id in port_ids]
            where = "(" + " OR ".join(clauses) + ")"
            frame = self._query(where=where, out_fields=fields, order_by="date ASC")
            frame = self._parse_observations(frame, metrics=metrics)
            if observation_end:
                frame = frame.loc[frame["date"] <= end_ts]
            return frame.sort_values(["date", "portname"]).reset_index(drop=True)

        cache_root = Path(cache_dir) if cache_dir is not None else None
        if cache_root is not None:
            cache_root.mkdir(parents=True, exist_ok=True)

        chunks: list[pd.DataFrame] = []
        for row in resolved.itertuples(index=False):
            port_id = str(row.portid)
            canonical_name = str(row.portname)
            escaped_id = port_id.replace("'", "''")
            for year in range(start_ts.year, end_ts.year + 1):
                cache_path = None
                if cache_root is not None:
                    cache_path = cache_root / f"{_slug(canonical_name)}__{_slug(port_id)}__{year}.csv"
                if cache_path is not None and cache_path.exists():
                    chunk = pd.read_csv(cache_path)
                else:
                    where = f"portid='{escaped_id}' AND year = {year}"
                    try:
                        chunk = self._query(
                            where=where,
                            out_fields=fields,
                            order_by="date ASC",
                        )
                    except Exception as exc:
                        raise RuntimeError(
                            f"PortWatch download failed for {canonical_name} ({port_id}), year {year}. "
                            "Completed year chunks are cached; rerun the same command to resume."
                        ) from exc
                    if cache_path is not None:
                        chunk.to_csv(cache_path, index=False)
                if not chunk.empty:
                    chunks.append(chunk)

        if not chunks:
            return pd.DataFrame(columns=fields)
        frame = pd.concat(chunks, ignore_index=True)
        frame = self._parse_observations(frame, metrics=metrics)
        frame = frame.loc[(frame["date"] >= start_ts) & (frame["date"] <= end_ts)]
        frame = frame.drop_duplicates(subset=["date", "portid"], keep="last")
        return frame.sort_values(["date", "portname"]).reset_index(drop=True)


def trailing_anomaly(
    series: pd.Series,
    *,
    smooth_days: int = 7,
    baseline_days: int = 365,
    min_periods: int = 90,
    log1p: bool = True,
) -> pd.Series:
    """Past-only rolling anomaly suitable for positive physical-flow data.

    The current smoothed observation is compared with a baseline whose mean and standard
    deviation are shifted by one observation, so the benchmark never sees the current or
    future value.
    """
    s = pd.to_numeric(series, errors="coerce").astype(float)
    if log1p:
        if (s.dropna() < 0).any():
            raise ValueError("log1p anomaly requires non-negative observations")
        s = np.log1p(s)

    smooth = s.rolling(smooth_days, min_periods=max(2, smooth_days // 2)).mean()
    history = smooth.shift(1)
    mean = history.rolling(baseline_days, min_periods=min_periods).mean()
    std = history.rolling(baseline_days, min_periods=min_periods).std(ddof=1)
    return ((smooth - mean) / std.replace(0.0, np.nan)).rename(series.name)


def seasonal_yoy_anomaly(
    series: pd.Series,
    *,
    smooth_days: int = 7,
    seasonal_lag_days: int = 364,
    standardize_days: int = 365,
    min_periods: int = 90,
    log1p: bool = True,
) -> pd.Series:
    """Past-only year-over-year anomaly for strongly seasonal daily physical flows.

    A trailing seven-day smooth is differenced against 52 weeks earlier (364 days, which
    preserves weekday alignment), then standardised using only *previous* year-over-year
    residuals. This removes much of the annual/weekday shipping seasonality without using
    a centred smoother or future observations.
    """
    s = pd.to_numeric(series, errors="coerce").astype(float)
    if log1p:
        if (s.dropna() < 0).any():
            raise ValueError("log1p anomaly requires non-negative observations")
        s = np.log1p(s)
    smooth = s.rolling(smooth_days, min_periods=max(2, smooth_days // 2)).mean()
    yoy = smooth - smooth.shift(seasonal_lag_days)
    history = yoy.shift(1)
    mean = history.rolling(standardize_days, min_periods=min_periods).mean()
    std = history.rolling(standardize_days, min_periods=min_periods).std(ddof=1)
    return ((yoy - mean) / std.replace(0.0, np.nan)).rename(series.name)


def build_chokepoint_feature_panel(
    raw: pd.DataFrame,
    *,
    metrics: Iterable[str] = ("capacity", "n_total"),
    smooth_days: int = 7,
    baseline_days: int = 365,
    min_periods: int = 90,
    method: str = "rolling",
    seasonal_lag_days: int = 364,
) -> pd.DataFrame:
    required = {"date", "portname", *metrics}
    missing = required.difference(raw.columns)
    if missing:
        raise KeyError(f"Missing PortWatch columns: {sorted(missing)}")

    pieces: list[pd.Series] = []
    frame = raw.copy()
    frame["date"] = pd.to_datetime(frame["date"])

    for portname, group in frame.groupby("portname", sort=True):
        group = group.sort_values("date").set_index("date")
        for metric in metrics:
            name = f"pw_{_slug(portname)}_{metric}_z"
            base_series = group[metric].rename(name)
            if method == "rolling":
                feature = trailing_anomaly(
                    base_series,
                    smooth_days=smooth_days,
                    baseline_days=baseline_days,
                    min_periods=min_periods,
                )
            elif method == "seasonal_yoy":
                feature = seasonal_yoy_anomaly(
                    base_series,
                    smooth_days=smooth_days,
                    seasonal_lag_days=seasonal_lag_days,
                    standardize_days=baseline_days,
                    min_periods=min_periods,
                )
            else:
                raise ValueError("method must be 'rolling' or 'seasonal_yoy'")
            pieces.append(feature)

    if not pieces:
        return pd.DataFrame()
    return pd.concat(pieces, axis=1).sort_index()


def portwatch_features_to_releases(
    features: pd.DataFrame,
    *,
    availability_lag_days: int = 7,
) -> pd.DataFrame:
    """Convert a feature panel to the project's point-in-time long-form schema.

    PortWatch does not expose historical publication vintages through this endpoint, so the
    lag is an explicit research assumption rather than a claim about exact historical
    release timestamps. The default seven-day lag is intentionally conservative for the
    first pilot and must be sensitivity-tested before any trading claim.
    """
    if availability_lag_days < 0:
        raise ValueError("availability_lag_days must be >= 0")

    long = features.rename_axis("observation_time").stack(future_stack=True).rename("value").dropna().reset_index()
    long = long.rename(columns={"level_1": "feature"})
    long["observation_time"] = pd.to_datetime(long["observation_time"])
    long["available_at"] = long["observation_time"] + pd.to_timedelta(
        availability_lag_days, unit="D"
    )
    long["source"] = "IMF PortWatch"
    long["frequency"] = "daily"
    long["transform"] = "trailing_log_anomaly"
    return long[
        [
            "observation_time",
            "available_at",
            "feature",
            "value",
            "source",
            "frequency",
            "transform",
        ]
    ]
