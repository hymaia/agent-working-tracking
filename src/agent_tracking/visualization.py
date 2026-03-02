"""Visualization utilities for codebase health metrics.

This module provides functions to plot different aspects of a project's
quality and activity using simulated data. The charts are prepared with
matplotlib and seaborn and are designed so that real data from CSVs or
APIs can be substituted easily.

Functions:
    - generate_hotspot_scatter(df): scatter plot of churn vs complexity
    - generate_quality_radar(df): radar chart of quality dimensions
    - generate_evolution_dual_axis(df): dual-axis line chart for coverage
      and technical debt over time

Sample data generation helpers are included; they can be replaced with
real inputs later.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Optional

# Set a professional palette
sns.set_palette("viridis")
sns.set_style("whitegrid")


def _generate_sample_hotspot_data(n: int = 30) -> pd.DataFrame:
    """Create a sample DataFrame for hotspot calculations.

    Columns:
        filename: str
        churn: float (changes per month)
        complexity: float (cyclomatic complexity)
        loc: int (lines of code)
    """
    np.random.seed(0)
    data = {
        "filename": [f"module_{i}.py" for i in range(n)],
        "churn": np.random.gamma(shape=2, scale=1.5, size=n),
        "complexity": np.random.normal(loc=10, scale=5, size=n).clip(1),
        "loc": np.random.randint(50, 2000, size=n),
    }
    return pd.DataFrame(data)


def _generate_sample_quality_data() -> pd.DataFrame:
    """Create a single-row DataFrame with quality metrics in percent.

    Dimensions: maintainability, coverage, security, reliability, docs
    """
    values = np.random.uniform(50, 100, size=5)
    return pd.DataFrame(
        [values],
        columns=[
            "maintainability",
            "coverage",
            "security",
            "reliability",
            "documentation",
        ],
    )


def _generate_sample_evolution_data(months: int = 12) -> pd.DataFrame:
    """Simulate coverage (%) and technical debt (days) over a series of months."""
    idx = pd.date_range(end=pd.Timestamp.today(), periods=months, freq="M")
    coverage = np.linspace(60, 90, months) + np.random.normal(0, 2, months)
    debt = np.linspace(30, 10, months) + np.random.normal(0, 3, months)
    return pd.DataFrame({"coverage": coverage, "debt": debt}, index=idx)


def generate_hotspot_scatter(
    df: Optional[pd.DataFrame] = None,
    save_path: Optional[Path] = None,
    show: bool = True,
) -> None:
    """Plot a scatter of churn vs cyclomatic complexity.

    Bubble size corresponds to lines of code. File names are annotated.

    Args:
        df: DataFrame providing `filename`, `churn`, `complexity`, `loc`.
        save_path: if provided, figure is saved to this path.
        show: whether to call ``plt.show()`` (disable for automated testing).
    """
    if df is None:
        df = _generate_sample_hotspot_data()

    plt.figure(figsize=(10, 6))
    scatter = plt.scatter(
        df["churn"],
        df["complexity"],
        s=df["loc"] / 10,
        alpha=0.6,
        cmap="viridis",
    )
    plt.colorbar(scatter, label="Lines of Code (scaled)")
    plt.xlabel("Churn (changes/month)")
    plt.ylabel("Cyclomatic Complexity")
    plt.title("Hotspot Analysis: Churn vs Complexity")

    # annotate a few points
    for _, row in df.iterrows():
        plt.text(row["churn"], row["complexity"], row["filename"], fontsize=8)

    if save_path:
        plt.savefig(save_path, bbox_inches="tight")
    if show:
        plt.show()


def generate_quality_radar(
    df: Optional[pd.DataFrame] = None,
    save_path: Optional[Path] = None,
    show: bool = True,
) -> None:
    """Create a radar/spider chart for quality dimensions.

    Args:
        df: one-row DataFrame with quality metrics.
        save_path: file to save figure.
        show: if True, call ``plt.show()``.
    """
    if df is None:
        df = _generate_sample_quality_data()

    categories = list(df.columns)
    values = df.iloc[0].values.tolist()
    # close the loop by repeating the first category/value
    categories += categories[:1]
    values += values[:1]
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=True)

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={"projection": "polar"})
    ax.plot(angles, values, "o-", linewidth=2)
    ax.fill(angles, values, alpha=0.25)
    ax.set_thetagrids(angles * 180 / np.pi, categories)
    ax.set_title("Quality Profile")
    ax.set_ylim(0, 100)

    if save_path:
        fig.savefig(save_path, bbox_inches="tight")
    if show:
        plt.show()


def generate_evolution_dual_axis(
    df: Optional[pd.DataFrame] = None,
    save_path: Optional[Path] = None,
    show: bool = True,
) -> None:
    """Plot coverage (%) and debt (days) over time with dual y axes.

    Args:
        df: DataFrame indexed by date with "coverage" and "debt" columns.
        save_path: optional file to save the figure.
        show: whether to display the plot interactively.
    """
    if df is None:
        df = _generate_sample_evolution_data()

    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx()

    sns.lineplot(data=df, x=df.index, y="coverage", ax=ax1, label="Coverage %")
    sns.lineplot(data=df, x=df.index, y="debt", ax=ax2,
                 color="orange", label="Debt (days)")

    ax1.set_xlabel("Month")
    ax1.set_ylabel("Coverage %")
    ax2.set_ylabel("Technical Debt (days)")
    ax1.set_title("Coverage and Technical Debt Over Time")

    ax1.legend(loc="upper left")
    ax2.legend(loc="upper right")

    if save_path:
        fig.savefig(save_path, bbox_inches="tight")
    if show:
        plt.show()
