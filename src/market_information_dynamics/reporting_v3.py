from __future__ import annotations

from pathlib import Path

import pandas as pd


def write_empirical_v3_markdown(
    metrics: pd.DataFrame,
    tests: pd.DataFrame,
    latest_survival: pd.DataFrame,
    latest_gates: pd.DataFrame,
    *,
    output: str | Path,
) -> Path:
    segment = (
        "reused_evaluation"
        if (metrics["segment"] == "reused_evaluation").any()
        else "oos_all"
    )
    view = metrics.loc[metrics["segment"] == segment]
    mean_skill = view.groupby(["horizon", "model"], as_index=False)["rmse_skill_vs_ar"].mean()

    lines = [
        "# Empirical v3 — protected-core candidate overlay",
        "",
        "v2 showed that filtering persistent edges could reduce damage from the full",
        "physical+financial system, but it still usually failed to beat the financial-only",
        "model. v3 changes the question: candidate data must explain realised out-of-sample",
        "errors left by a protected financial core.",
        "",
        "**Evaluation status:** 2025+ has already informed earlier project iterations and is",
        "therefore a reused diagnostic period, not a pristine confirmatory holdout. The method",
        "is intended to be frozen before prospective observations from September 2026 onward.",
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
                tests=("p_value", "size"),
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
                f"| {row.comparison} | {row.tests} | {row.challenger_better} | "
                f"{row.fdr_rejections} |"
            )

    lines += ["", "## Current candidate-edge survival", ""]
    if latest_survival.empty:
        lines.append("No candidate edge currently has enough history for a survival table.")
    else:
        top = latest_survival.sort_values("survival_score", ascending=False).head(15)
        lines += [
            "| h | candidate source | target | survival | selection | OOS edge value | n |",
            "|---:|---|---|---:|---:|---:|---:|",
        ]
        for row in top.itertuples(index=False):
            loss = row.weighted_mean_loss_improvement
            loss_text = "NA" if pd.isna(loss) else f"{loss:.3g}"
            lines.append(
                f"| {row.horizon} | {row.source} | {row.target} | {row.survival_score:.3f} | "
                f"{row.weighted_selection_frequency:.2f} | {loss_text} | {row.n_contributions} |"
            )

    lines += ["", "## Current model-level overlay gates", ""]
    if latest_gates.empty:
        lines.append("No adaptive overlay gate is available yet.")
    else:
        topg = latest_gates.sort_values(["horizon", "gate"], ascending=[True, False])
        lines += [
            "| h | target | gate | recent OOS value | t-stat | n |",
            "|---:|---|---:|---:|---:|---:|",
        ]
        for row in topg.itertuples(index=False):
            mean = row.weighted_mean_loss_improvement
            mean_text = "NA" if pd.isna(mean) else f"{mean:.3g}"
            t = row.contribution_t_stat
            t_text = "NA" if pd.isna(t) else f"{t:.2f}"
            lines.append(
                f"| {row.horizon} | {row.target} | {row.gate:.3f} | {mean_text} | {t_text} | {row.n} |"
            )

    lines += [
        "",
        "## Interpretation",
        "",
        "The financial model is the protected core. Candidate data are not allowed to replace",
        "it. The sparse overlay is trained only on fully realised out-of-sample core residuals.",
        "Candidate edges are scored by whether adding that edge to the core would have reduced",
        "realised forecast loss. Surviving edges are refitted, then the entire overlay is shrunk",
        "toward zero unless its own recent realised OOS performance is positive.",
        "",
        "This is an online model-augmentation problem, not a claim of structural causality.",
        "",
    ]
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
