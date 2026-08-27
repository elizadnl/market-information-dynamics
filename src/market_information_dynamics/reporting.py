from __future__ import annotations

from pathlib import Path

import pandas as pd


def write_empirical_markdown(
    metrics: pd.DataFrame,
    forecast_tests: pd.DataFrame,
    edge_stability: pd.DataFrame,
    *,
    output: str | Path,
    availability_lag_days: int | None = None,
) -> Path:
    """Write a concise machine-generated results note without promotional language."""
    if "segment" in metrics.columns:
        report_segment = "final_holdout" if (metrics["segment"] == "final_holdout").any() else "oos_all"
        report_metrics = metrics.loc[metrics["segment"] == report_segment].copy()
    else:
        report_segment = "oos_all"
        report_metrics = metrics
    pivot = report_metrics.pivot(index="variable", columns="model", values="rmse")
    incremental = pd.Series(dtype=float)
    if {"financial_sparse_var", "full_sparse_var"}.issubset(pivot.columns):
        incremental = (1.0 - pivot["full_sparse_var"] / pivot["financial_sparse_var"]).sort_values(
            ascending=False
        )

    lines = [
        "# Empirical v1 results",
        "",
        "This file is generated from the walk-forward outputs. It reports predictive evidence,",
        "not causal effects and not a claim of deployable alpha.",
        "",
    ]
    if availability_lag_days is not None:
        lines += [f"**Assumed PortWatch availability lag:** {availability_lag_days} calendar days.", ""]

    lines += [f"**Forecast reporting segment:** {report_segment}.", ""]

    if len(incremental):
        lines += ["## Incremental physical-data forecast skill", ""]
        lines += [
            "Positive values mean the full financial+physical model has lower RMSE than the",
            "financial-only sparse VAR on the same OOS dates.",
            "",
            "| target | incremental RMSE skill |",
            "|---|---:|",
        ]
        for variable, skill in incremental.items():
            lines.append(f"| {variable} | {skill:.2%} |")
        lines.append("")

    if not forecast_tests.empty:
        lines += ["## Paired forecast tests", "", "| target | DM stat | p-value | FDR reject | full better |", "|---|---:|---:|:---:|:---:|"]
        for row in forecast_tests.itertuples(index=False):
            lines.append(
                f"| {row.variable} | {row.dm_stat:.3f} | {row.p_value:.4f} | "
                f"{'yes' if row.fdr_reject else 'no'} | {'yes' if row.challenger_better else 'no'} |"
            )
        lines.append("")

    if not edge_stability.empty:
        top = edge_stability.head(15)
        lines += ["## Most persistent predictive edges", "", "| source | target | selection freq. | mean strength | sign stability |", "|---|---|---:|---:|---:|"]
        for row in top.itertuples(index=False):
            sign_stability = row.sign_stability
            sign_text = "NA" if pd.isna(sign_stability) else f"{sign_stability:.2f}"
            lines.append(
                f"| {row.source} | {row.target} | {row.selection_frequency:.2f} | "
                f"{row.mean_strength:.3f} | {sign_text} |"
            )
        lines.append("")

    lines += [
        "## Interpretation rule",
        "",
        "A positive physical-data result is treated as interesting only if it is paired,",
        "out-of-sample, survives the pre-specified availability-lag sensitivity, and is not",
        "driven by a single target or short episode. Otherwise it is reported as weak/negative evidence.",
        "",
    ]
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
