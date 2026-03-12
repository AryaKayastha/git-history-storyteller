"""
Visualization — generates matplotlib/seaborn charts for commit activity
and contributor distribution, returning figures suitable for Streamlit.
"""

from typing import Dict, List

import matplotlib
matplotlib.use("Agg")  # non-interactive backend for Streamlit

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd


sns.set_theme(style="whitegrid", palette="viridis")


# ------------------------------------------------------------------ #
#  Chart 1 — Commits per Month
# ------------------------------------------------------------------ #

def plot_commits_per_month(monthly_df: pd.DataFrame) -> plt.Figure:
    """
    Bar chart of commits per month.

    Args:
        monthly_df: DataFrame with columns ['month', 'commits'].

    Returns:
        matplotlib Figure.
    """
    fig, ax = plt.subplots(figsize=(12, 4))

    if monthly_df.empty:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        return fig

    ax.bar(
        monthly_df["month"],
        monthly_df["commits"],
        width=25,
        color=sns.color_palette("viridis", 1)[0],
        edgecolor="white",
        linewidth=0.5,
    )
    ax.set_xlabel("Month")
    ax.set_ylabel("Commits")
    ax.set_title("Commit Activity Over Time")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    fig.autofmt_xdate(rotation=45)
    fig.tight_layout()
    return fig


# ------------------------------------------------------------------ #
#  Chart 2 — Commits per Contributor (top N)
# ------------------------------------------------------------------ #

def plot_contributor_commits(contributors_df: pd.DataFrame, top_n: int = 15) -> plt.Figure:
    """
    Horizontal bar chart of commits per contributor.

    Args:
        contributors_df: DataFrame with columns ['author', 'commits'].
        top_n: Maximum number of contributors to show.

    Returns:
        matplotlib Figure.
    """
    fig, ax = plt.subplots(figsize=(10, max(4, top_n * 0.4)))

    if contributors_df.empty:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        return fig

    top = contributors_df.head(top_n).sort_values("commits")
    colors = sns.color_palette("viridis", len(top))

    ax.barh(top["author"], top["commits"], color=colors, edgecolor="white", linewidth=0.5)
    ax.set_xlabel("Commits")
    ax.set_title(f"Top {len(top)} Contributors by Commit Count")
    fig.tight_layout()
    return fig


# ------------------------------------------------------------------ #
#  Chart 3 — Commit Type Pie Chart
# ------------------------------------------------------------------ #

def plot_commit_types(type_counts: Dict[str, int]) -> plt.Figure:
    """
    Pie chart of commit type distribution.

    Args:
        type_counts: Dict mapping type label → count.

    Returns:
        matplotlib Figure.
    """
    fig, ax = plt.subplots(figsize=(6, 6))

    if not type_counts:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        return fig

    labels = list(type_counts.keys())
    sizes = list(type_counts.values())
    colors = sns.color_palette("viridis", len(labels))

    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        autopct="%1.1f%%",
        colors=colors,
        startangle=140,
        pctdistance=0.85,
    )
    for t in autotexts:
        t.set_fontsize(8)

    ax.set_title("Commit Type Distribution")
    fig.tight_layout()
    return fig


# ------------------------------------------------------------------ #
#  Chart 4 — Lines Added vs Deleted Over Time
# ------------------------------------------------------------------ #

def plot_lines_over_time(df: pd.DataFrame) -> plt.Figure:
    """
    Area chart of cumulative lines added / deleted per month.

    Args:
        df: Full commits DataFrame with columns ['date', 'lines_added', 'lines_deleted'].

    Returns:
        matplotlib Figure.
    """
    fig, ax = plt.subplots(figsize=(12, 4))

    if df.empty or (df["lines_added"].sum() == 0 and df["lines_deleted"].sum() == 0):
        ax.text(0.5, 0.5, "No line-level data available", ha="center", va="center",
                transform=ax.transAxes, fontsize=12, color="gray")
        ax.set_title("Code Churn Over Time")
        fig.tight_layout()
        return fig

    monthly = df.set_index("date").resample("ME").agg(
        lines_added=("lines_added", "sum"),
        lines_deleted=("lines_deleted", "sum"),
    ).reset_index()

    ax.fill_between(
        monthly["date"], monthly["lines_added"],
        alpha=0.5, label="Lines Added", color="#2ecc71",
    )
    ax.fill_between(
        monthly["date"], -monthly["lines_deleted"],
        alpha=0.5, label="Lines Deleted", color="#e74c3c",
    )
    ax.axhline(0, color="gray", linewidth=0.5)
    ax.set_xlabel("Month")
    ax.set_ylabel("Lines")
    ax.set_title("Code Churn Over Time")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    fig.autofmt_xdate(rotation=45)
    fig.tight_layout()
    return fig
