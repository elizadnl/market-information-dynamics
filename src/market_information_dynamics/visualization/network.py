from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd


def save_network_plot(
    edge_table: pd.DataFrame,
    path: str | Path,
    *,
    top_n: int = 10,
    title: str = "Estimated predictive information network",
) -> None:
    """Save a simple directed network of the strongest estimated edges."""
    edges = edge_table.head(top_n)
    graph = nx.DiGraph()
    for row in edges.itertuples(index=False):
        graph.add_edge(row.source, row.target, weight=float(row.strength))

    fig, ax = plt.subplots(figsize=(9, 6))
    if graph.number_of_nodes() == 0:
        ax.text(0.5, 0.5, "No edges above threshold", ha="center", va="center")
        ax.axis("off")
    else:
        pos = nx.spring_layout(graph, seed=11)
        widths = [1.0 + 3.0 * graph[u][v]["weight"] for u, v in graph.edges]
        nx.draw_networkx(graph, pos=pos, ax=ax, width=widths, arrows=True, node_size=1800, font_size=9)
        ax.axis("off")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
