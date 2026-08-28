from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import yaml

from market_information_dynamics.compute.lagged import native_available
from market_information_dynamics.data.audit import panel_audit
from market_information_dynamics.data.fred_universe import load_fred_universe
from market_information_dynamics.data.public_panel import combine_financial_and_physical
from market_information_dynamics.data.portwatch import (
    PortWatchClient,
    build_chokepoint_feature_panel,
    portwatch_features_to_releases,
)
from market_information_dynamics.demo import run_demo
from market_information_dynamics.demo_survival import run_survival_demo
from market_information_dynamics.evaluation.empirical import run_empirical_v1
from market_information_dynamics.evaluation.empirical_v2 import run_empirical_v2
from market_information_dynamics.reporting import write_empirical_markdown
from market_information_dynamics.reporting_v2 import write_empirical_v2_markdown
from market_information_dynamics.visualization.empirical import (
    plot_oos_skill,
    plot_physical_incremental_skill,
)
from market_information_dynamics.visualization.survival import (
    plot_horizon_skill,
    plot_survival_lifecycle,
)


def _financial_ids(config_path: str) -> list[str]:
    config = yaml.safe_load(Path(config_path).read_text())
    return [node["id"] for node in config.get("financial", []) if node.get("source") == "FRED"]


def _download_public_inputs(
    financial_config: str,
    portwatch_config: str,
    *,
    start: str,
    end: str | None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    financial, metadata = load_fred_universe(
        financial_config,
        observation_start=start,
        observation_end=end,
    )
    pw_config = yaml.safe_load(Path(portwatch_config).read_text())
    feature_cfg = pw_config.get("features", {})
    raw = PortWatchClient().chokepoints(
        names=pw_config["chokepoints"],
        observation_start=start,
        observation_end=end,
        metrics=pw_config.get("metrics", ["capacity", "n_total"]),
        cache_dir=pw_config.get("cache_dir", "data/cache/portwatch"),
    )
    physical_features = build_chokepoint_feature_panel(
        raw,
        metrics=pw_config.get("metrics", ["capacity", "n_total"]),
        smooth_days=int(feature_cfg.get("smooth_days", 7)),
        baseline_days=int(feature_cfg.get("baseline_days", 365)),
        min_periods=int(feature_cfg.get("min_periods", 90)),
        method=str(feature_cfg.get("method", "rolling")),
        seasonal_lag_days=int(feature_cfg.get("seasonal_lag_days", 364)),
    )
    return financial, metadata, raw, physical_features, pw_config


def _save_public_inputs(
    financial: pd.DataFrame,
    metadata: pd.DataFrame,
    raw: pd.DataFrame,
    physical_features: pd.DataFrame,
    releases: pd.DataFrame,
    panel: pd.DataFrame,
    *,
    out: Path,
) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(out)
    financial.to_csv(out.with_name(out.stem + "_financial.csv"))
    metadata.to_csv(out.with_name(out.stem + "_financial_metadata.csv"), index=False)
    raw.to_csv(out.with_name(out.stem + "_portwatch_raw.csv"), index=False)
    physical_features.to_csv(out.with_name(out.stem + "_physical_features.csv"))
    releases.to_csv(out.with_name(out.stem + "_physical_releases.csv"), index=False)


def _run_empirical_from_panel(
    panel: pd.DataFrame,
    *,
    financial_config: str,
    experiment_config: str,
    out_dir: str,
    availability_lag_days: int | None = None,
) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    financial_columns = _financial_ids(financial_config)
    result = run_empirical_v1(
        panel,
        financial_columns=financial_columns,
        config_path=experiment_config,
    )
    result.metrics.to_csv(out / "metrics.csv", index=False)
    result.actuals.to_csv(out / "actuals.csv")
    for model_name, frame in result.predictions.items():
        frame.to_csv(out / f"predictions_{model_name}.csv")
    result.full_edges.to_csv(out / "edge_snapshots.csv", index=False)
    result.edge_stability.to_csv(out / "edge_stability.csv", index=False)
    result.forecast_tests.to_csv(out / "physical_incremental_forecast_tests.csv", index=False)
    audit_table, audit_summary = panel_audit(panel)
    audit_table.to_csv(out / "panel_audit.csv")
    (out / "panel_audit_summary.json").write_text(json.dumps(audit_summary, indent=2))
    plot_oos_skill(result.metrics, out / "oos_skill_vs_ar.png")
    plot_physical_incremental_skill(result.metrics, out / "physical_incremental_skill.png")
    write_empirical_markdown(
        result.metrics,
        result.forecast_tests,
        result.edge_stability,
        output=out / "RESULTS.md",
        availability_lag_days=availability_lag_days,
    )
    print(f"Wrote empirical v1 outputs to {out}")


def _run_empirical_v2_from_panel(
    panel: pd.DataFrame,
    *,
    financial_config: str,
    experiment_config: str,
    out_dir: str,
) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    financial_columns = _financial_ids(financial_config)
    result = run_empirical_v2(
        panel, financial_columns=financial_columns, config_path=experiment_config
    )
    result.metrics.to_csv(out / "metrics.csv", index=False)
    result.forecast_tests.to_csv(out / "nested_forecast_tests.csv", index=False)
    result.latest_survival.to_csv(out / "latest_edge_survival.csv", index=False)

    for horizon, h_result in result.horizon_results.items():
        h_dir = out / f"h{horizon}"
        h_dir.mkdir(parents=True, exist_ok=True)
        h_result.actuals.to_csv(h_dir / "actuals.csv")
        for model_name, frame in h_result.predictions.items():
            frame.to_csv(h_dir / f"predictions_{model_name}.csv")
        h_result.edge_snapshots.to_csv(h_dir / "edge_snapshots.csv", index=False)
        h_result.edge_contributions.to_csv(h_dir / "edge_contributions.csv", index=False)
        h_result.survival_history.to_csv(h_dir / "survival_history.csv", index=False)

    for segment in ["oos_all", "development", "reused_holdout"]:
        if (result.metrics["segment"] == segment).any():
            plot_horizon_skill(result.metrics, out / f"horizon_skill_{segment}.png", segment=segment)

    if not result.latest_survival.empty:
        config = yaml.safe_load(Path(experiment_config).read_text())
        n_edges = int(config.get("report", {}).get("lifecycle_edges", 6))
        top = result.latest_survival.sort_values("survival_score", ascending=False).head(n_edges)
        for row in top.itertuples(index=False):
            history = result.horizon_results[int(row.horizon)].survival_history
            safe_source = str(row.source).replace("/", "_")
            safe_target = str(row.target).replace("/", "_")
            plot_survival_lifecycle(
                history,
                source=row.source,
                target=row.target,
                horizon=int(row.horizon),
                output=out / f"lifecycle_h{int(row.horizon)}_{safe_source}__{safe_target}.png",
            )

    write_empirical_v2_markdown(
        result.metrics,
        result.forecast_tests,
        result.latest_survival,
        output=out / "RESULTS.md",
    )
    print(f"Wrote empirical v2 signal-survival outputs to {out}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="market-information-dynamics")
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="Run the leakage-safe synthetic walk-forward demo")
    demo.add_argument("--out", default="artifacts")
    demo.add_argument("--n-obs", type=int, default=1800)

    survival_demo = sub.add_parser(
        "survival-demo", help="Run the controlled predictive-edge death demonstration"
    )
    survival_demo.add_argument("--out", default="artifacts")

    fred = sub.add_parser("fred-pilot", help="Download the configured public FRED pilot panel")
    fred.add_argument("--config", default="configs/universe_v0.yaml")
    fred.add_argument("--start", default="2019-01-01")
    fred.add_argument("--end", default=None)
    fred.add_argument("--out", default="data/processed/fred_pilot.csv")

    portwatch = sub.add_parser(
        "portwatch-pilot", help="Download and transform public IMF PortWatch chokepoint data"
    )
    portwatch.add_argument("--config", default="configs/portwatch_v1.yaml")
    portwatch.add_argument("--out", default="data/processed/portwatch_chokepoints.csv")

    public = sub.add_parser(
        "public-pilot", help="Build the joined financial + physical public-data panel"
    )
    public.add_argument("--financial-config", default="configs/universe_v1.yaml")
    public.add_argument("--portwatch-config", default="configs/portwatch_v1.yaml")
    public.add_argument("--start", default="2019-01-01")
    public.add_argument("--end", default=None)
    public.add_argument("--out", default="data/processed/public_pilot.csv")

    empirical = sub.add_parser(
        "empirical-v1", help="Run the pre-specified ablation on an existing public panel"
    )
    empirical.add_argument("--panel", default="data/processed/public_pilot.csv")
    empirical.add_argument("--financial-config", default="configs/universe_v1.yaml")
    empirical.add_argument("--experiment-config", default="configs/empirical_v1.yaml")
    empirical.add_argument("--out", default="artifacts/empirical_v1")

    empirical_v2 = sub.add_parser(
        "empirical-v2",
        help="Run multi-horizon predictive-edge survival research on an existing public panel",
    )
    empirical_v2.add_argument("--panel", default="data/processed/public_pilot.csv")
    empirical_v2.add_argument("--financial-config", default="configs/universe_v1.yaml")
    empirical_v2.add_argument("--experiment-config", default="configs/empirical_v2.yaml")
    empirical_v2.add_argument("--out", default="artifacts/empirical_v2")

    research = sub.add_parser(
        "public-research", help="Download public data and run primary + lag-sensitivity research"
    )
    research.add_argument("--financial-config", default="configs/universe_v1.yaml")
    research.add_argument("--portwatch-config", default="configs/portwatch_v1.yaml")
    research.add_argument("--experiment-config", default="configs/empirical_v1.yaml")
    research.add_argument("--start", default="2019-01-01")
    research.add_argument("--end", default=None)
    research.add_argument("--data-out", default="data/processed/public_pilot.csv")
    research.add_argument("--out", default="artifacts/empirical_v1")

    sub.add_parser("backend-info", help="Report whether the optional C++ kernel is available")

    args = parser.parse_args()

    if args.command == "demo":
        paths = run_demo(out_dir=args.out, n_obs=args.n_obs)
        print("Demo complete:")
        for key, value in paths.items():
            print(f"  {key}: {value}")
    elif args.command == "survival-demo":
        paths = run_survival_demo(out_dir=args.out)
        print("Signal-survival demo complete:")
        for key, value in paths.items():
            print(f"  {key}: {value}")
    elif args.command == "fred-pilot":
        panel, metadata = load_fred_universe(
            args.config,
            observation_start=args.start,
            observation_end=args.end,
        )
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        panel.to_csv(out)
        metadata.to_csv(out.with_name(out.stem + "_metadata.csv"), index=False)
        print(f"Wrote {len(panel):,} aligned observations to {out}")
    elif args.command == "portwatch-pilot":
        config = yaml.safe_load(Path(args.config).read_text())
        feature_cfg = config.get("features", {})
        raw = PortWatchClient().chokepoints(
            names=config["chokepoints"],
            observation_start=config.get("observation_start"),
            observation_end=config.get("observation_end"),
            metrics=config.get("metrics", ["capacity", "n_total"]),
            cache_dir=config.get("cache_dir", "data/cache/portwatch"),
        )
        features = build_chokepoint_feature_panel(
            raw,
            metrics=config.get("metrics", ["capacity", "n_total"]),
            smooth_days=int(feature_cfg.get("smooth_days", 7)),
            baseline_days=int(feature_cfg.get("baseline_days", 365)),
            min_periods=int(feature_cfg.get("min_periods", 90)),
        )
        releases = portwatch_features_to_releases(
            features,
            availability_lag_days=int(config.get("availability_lag_days", 10)),
        )
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        features.to_csv(out)
        releases.to_csv(out.with_name(out.stem + "_releases.csv"), index=False)
        raw.to_csv(out.with_name(out.stem + "_raw.csv"), index=False)
        print(f"Wrote {len(features):,} PortWatch feature dates to {out}")
    elif args.command in {"public-pilot", "public-research"}:
        financial, metadata, raw, physical_features, pw_config = _download_public_inputs(
            args.financial_config,
            args.portwatch_config,
            start=args.start,
            end=args.end,
        )
        primary_lag = int(pw_config.get("availability_lag_days", 10))
        releases = portwatch_features_to_releases(
            physical_features, availability_lag_days=primary_lag
        )
        panel = combine_financial_and_physical(financial, releases)
        data_out = Path(args.out if args.command == "public-pilot" else args.data_out)
        _save_public_inputs(
            financial, metadata, raw, physical_features, releases, panel, out=data_out
        )
        print(f"Wrote {len(panel):,} joined public-data observations to {data_out}")

        if args.command == "public-research":
            _run_empirical_from_panel(
                panel,
                financial_config=args.financial_config,
                experiment_config=args.experiment_config,
                out_dir=args.out,
                availability_lag_days=primary_lag,
            )
            sensitivity_rows: list[dict[str, object]] = []
            for lag in pw_config.get("availability_lag_sensitivity_days", []):
                lag = int(lag)
                lag_releases = portwatch_features_to_releases(
                    physical_features, availability_lag_days=lag
                )
                lag_panel = combine_financial_and_physical(financial, lag_releases)
                result = run_empirical_v1(
                    lag_panel,
                    financial_columns=_financial_ids(args.financial_config),
                    config_path=args.experiment_config,
                )
                metric_view = result.metrics
                if "segment" in metric_view.columns:
                    preferred = (
                        "final_holdout"
                        if (metric_view["segment"] == "final_holdout").any()
                        else "oos_all"
                    )
                    metric_view = metric_view.loc[metric_view["segment"] == preferred]
                pivot = metric_view.pivot(index="variable", columns="model", values="rmse")
                skill = 1.0 - pivot["full_sparse_var"] / pivot["financial_sparse_var"]
                sensitivity_rows.append(
                    {
                        "availability_lag_days": lag,
                        "mean_incremental_rmse_skill": float(skill.mean()),
                        "median_incremental_rmse_skill": float(skill.median()),
                        "targets_improved": int((skill > 0).sum()),
                        "targets_total": int(skill.notna().sum()),
                        "fdr_significant_improvements": int(
                            (
                                result.forecast_tests["fdr_reject"]
                                & result.forecast_tests["challenger_better"]
                            ).sum()
                        ),
                    }
                )
            pd.DataFrame(sensitivity_rows).to_csv(
                Path(args.out) / "availability_lag_sensitivity.csv", index=False
            )
    elif args.command == "empirical-v1":
        panel = pd.read_csv(args.panel, index_col=0, parse_dates=True)
        _run_empirical_from_panel(
            panel,
            financial_config=args.financial_config,
            experiment_config=args.experiment_config,
            out_dir=args.out,
        )
    elif args.command == "empirical-v2":
        panel = pd.read_csv(args.panel, index_col=0, parse_dates=True)
        _run_empirical_v2_from_panel(
            panel,
            financial_config=args.financial_config,
            experiment_config=args.experiment_config,
            out_dir=args.out,
        )
    elif args.command == "backend-info":
        print("native C++ backend:", "available" if native_available() else "not built")


if __name__ == "__main__":
    main()
