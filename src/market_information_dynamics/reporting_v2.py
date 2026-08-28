from __future__ import annotations

from pathlib import Path

import pandas as pd


def write_empirical_v2_markdown(
    metrics: pd.DataFrame,
    tests: pd.DataFrame,
    latest_survival: pd.DataFrame,
    *,
    output: str | Path,
) -> Path:
    segment = "reused_holdout" if (metrics["segment"] == "reused_holdout").any() else "oos_all"
    view = metrics.loc[metrics["segment"] == segment]
    mean_skill = (
        view.groupby(["horizon", "model"], as_index=False)["rmse_skill_vs_ar"].mean()
    )

    lines = [
        "# Empirical v2 — predictive edge survival",
        "",
        "This release was motivated by the empirical-v1 null result: coefficient persistence",
        "alone was not a reliable proxy for genuine out-of-sample forecast value.",
        "",
        "**Important evaluation caveat:** the 2025+ segment was already inspected during v1.",
        "It is therefore labelled a *reused holdout*, not a pristine confirmatory test. The",
        "v2 method is assessed with pre-2025 walk-forward evidence and transparent secondary",
        "evaluation; genuinely prospective validation begins with future observations.",
        "",
        "## Mean skill by horizon",
        "",
        "| horizon | model | mean RMSE skill vs AR |",
        "|---:|---|---:|",
    ]
    for row in mean_skill.itertuples(index=False):
        lines.append(f"| {row.horizon} | {row.model} | {row.rmse_skill_vs_ar:.2%} |")

    lines += ["", "## Nested forecast comparisons", ""]
    if tests.empty:
        lines.append("No comparison had enough paired forecasts.")
    else:
        summary = (
            tests.groupby("comparison")
            .agg(
                tests=("p_value", "size"),
                challenger_better=("challenger_better", "sum"),
                fdr_rejections=("fdr_reject", "sum"),
            )
            .reset_index()
        )
        lines += ["| comparison | pairs | challenger better | FDR rejections |", "|---|---:|---:|---:|"]
        for row in summary.itertuples(index=False):
            lines.append(
                f"| {row.comparison} | {row.tests} | {row.challenger_better} | {row.fdr_rejections} |"
            )

    lines += ["", "## Highest current survival scores", ""]
    if latest_survival.empty:
        lines.append("No edge survival table was available.")
    else:
        top = latest_survival.sort_values("survival_score", ascending=False).head(20)
        lines += [
            "| h | source | target | survival | sel. freq | OOS loss improvement | n |",
            "|---:|---|---|---:|---:|---:|---:|",
        ]
        for row in top.itertuples(index=False):
            loss = row.weighted_mean_loss_improvement
            loss_text = "NA" if pd.isna(loss) else f"{loss:.3g}"
            lines.append(
                f"| {row.horizon} | {row.source} | {row.target} | {row.survival_score:.3f} | "
                f"{row.weighted_selection_frequency:.2f} | {loss_text} | {row.n_contributions} |"
            )

    lines += [
        "",
        "## Interpretation",
        "",
        "An edge is not trusted merely because LASSO repeatedly selects it. Survival requires",
        "recent structural persistence *and* positive realised OOS marginal forecast contribution.",
        "Old evidence decays exponentially. Final survivor forecasts are refitted with Ridge",
        "conditional on the surviving source set rather than created by zeroing LASSO coefficients.",
        "",
    ]
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
