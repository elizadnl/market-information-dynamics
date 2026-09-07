from __future__ import annotations

from pathlib import Path
import pandas as pd


def write_empirical_v4_markdown(
    metrics: pd.DataFrame,
    tests: pd.DataFrame,
    latest_weights: pd.DataFrame,
    share_sensitivity: pd.DataFrame,
    *,
    output: str | Path,
) -> Path:
    segment = "reused_evaluation" if (metrics["segment"] == "reused_evaluation").any() else "oos_all"
    view = metrics.loc[metrics["segment"] == segment]
    mean_skill = view.groupby(["horizon", "model"], as_index=False)["rmse_skill_vs_ar"].mean()

    lines = [
        "# Empirical v4 — online expert aggregation",
        "",
        "v3 protected the financial core and allowed candidate data to act only as an overlay.",
        "That architecture prevented large failures, but the hand-built gate still turned on",
        "some overlays that later underperformed. v4 replaces the heuristic gate with a causal",
        "Fixed-Share expert aggregator: model weights are updated only after each forecast horizon",
        "has fully realised, and a small share term lets a previously weak expert recover after a",
        "regime change.",
        "",
        "**Evaluation status:** 2025+ is reused diagnostic history, not a pristine confirmatory",
        "holdout. The online aggregation rule is frozen for prospective monitoring from September",
        "2026 onward.",
        "",
        "## Mean skill by horizon",
        "",
        "| horizon | model | mean RMSE skill vs AR |",
        "|---:|---|---:|",
    ]
    for row in mean_skill.itertuples(index=False):
        lines.append(f"| {row.horizon} | {row.model} | {row.rmse_skill_vs_ar:.2%} |")

    lines += ["", "## Incremental forecast comparisons", ""]
    if tests.empty:
        lines.append("No comparison had enough paired forecasts.")
    else:
        summary = (
            tests.groupby("comparison")
            .agg(
                pairs=("p_value", "size"),
                challenger_better=("challenger_better", "sum"),
                fdr_rejections=("fdr_reject", "sum"),
            )
            .reset_index()
        )
        lines += [
            "| comparison | pairs | challenger better | FDR rejections |",
            "|---|---:|---:|---:|",
        ]
        for row in summary.itertuples(index=False):
            lines.append(
                f"| {row.comparison} | {row.pairs} | {row.challenger_better} | {row.fdr_rejections} |"
            )

    lines += ["", "## Current expert weights", ""]
    if latest_weights.empty:
        lines.append("No online weights available.")
    else:
        pivot = latest_weights.pivot_table(
            index=["horizon", "target"], columns="expert", values="weight", aggfunc="last"
        ).reset_index()
        experts = [c for c in pivot.columns if c not in {"horizon", "target"}]
        lines.append("| h | target | " + " | ".join(experts) + " |")
        lines.append("|---:|---|" + "|".join(["---:"] * len(experts)) + "|")
        for row in pivot.itertuples(index=False):
            vals = [f"{getattr(row, e):.3f}" for e in experts]
            lines.append(f"| {row.horizon} | {row.target} | " + " | ".join(vals) + " |")

    lines += ["", "## Fixed-Share sensitivity", ""]
    if share_sensitivity.empty:
        lines.append("No share-parameter sensitivity available.")
    else:
        lines += [
            "| h | share | mean RMSE skill vs financial core | targets better |",
            "|---:|---:|---:|---:|",
        ]
        for row in share_sensitivity.itertuples(index=False):
            lines.append(
                f"| {row.horizon} | {row.share:.5f} | {row.mean_rmse_skill_vs_financial_core:.2%} | "
                f"{row.targets_better}/{row.n_targets} |"
            )

    lines += [
        "",
        "## Interpretation",
        "",
        "The online combiner is deliberately model-agnostic. It does not decide that shipping",
        "or any other candidate domain *should* matter. It treats the financial core and the",
        "survival-filtered candidate overlay as competing forecast experts, updates their weights",
        "only after losses are observable, and retains a small probability of switching back after",
        "a regime change. This is a sequential decision problem, not evidence of structural causality.",
        "",
        "The primary research claim remains methodological: in non-stationary systems, a model",
        "should learn not only predictive relationships but also when to stop trusting the model",
        "that generated them.",
        "",
    ]
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
