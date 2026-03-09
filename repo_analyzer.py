"""
Repository Analyzer — computes commit statistics, contributor insights,
and development phase detection from commit metadata.
"""

from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


# ------------------------------------------------------------------ #
#  Commit Statistics
# ------------------------------------------------------------------ #

def compute_commit_statistics(df: pd.DataFrame) -> Dict:
    """
    Compute high-level commit statistics.

    Returns dict with total_commits, date_range, commits_per_month, etc.
    """
    if df.empty:
        return {
            "total_commits": 0,
            "first_commit": None,
            "last_commit": None,
            "total_authors": 0,
            "total_files_changed": 0,
            "total_lines_added": 0,
            "total_lines_deleted": 0,
            "total_merges": 0,
        }

    return {
        "total_commits": len(df),
        "first_commit": df["date"].min(),
        "last_commit": df["date"].max(),
        "total_authors": df["author"].nunique(),
        "total_files_changed": int(df["files_changed"].sum()),
        "total_lines_added": int(df["lines_added"].sum()),
        "total_lines_deleted": int(df["lines_deleted"].sum()),
        "total_merges": int(df["is_merge"].sum()),
    }


# ------------------------------------------------------------------ #
#  Commits Per Month
# ------------------------------------------------------------------ #

def commits_per_month(df: pd.DataFrame) -> pd.DataFrame:
    """Return a DataFrame with month and commit count."""
    if df.empty:
        return pd.DataFrame(columns=["month", "commits"])

    monthly = (
        df.set_index("date")
        .resample("ME")
        .size()
        .reset_index(name="commits")
    )
    monthly.rename(columns={"date": "month"}, inplace=True)
    return monthly


# ------------------------------------------------------------------ #
#  Contributor Analysis
# ------------------------------------------------------------------ #

def contributor_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a DataFrame ranked by number of commits per contributor.
    Columns: author, commits, lines_added, lines_deleted, first_commit, last_commit
    """
    if df.empty:
        return pd.DataFrame()

    grouped = df.groupby("author").agg(
        commits=("hash", "count"),
        lines_added=("lines_added", "sum"),
        lines_deleted=("lines_deleted", "sum"),
        first_commit=("date", "min"),
        last_commit=("date", "max"),
    ).reset_index()

    grouped = grouped.sort_values("commits", ascending=False).reset_index(drop=True)
    return grouped


def collaboration_intensity_per_phase(
    df: pd.DataFrame, phases: List[Dict]
) -> List[Dict]:
    """
    Compute the number of unique contributors active in each development phase.

    Returns list of dicts with phase_number, phase, active_contributors, top_contributor.
    """
    results = []
    for p in phases:
        mask = (df["date"] >= p["start_date"]) & (df["date"] <= p["end_date"])
        phase_df = df[mask]
        if phase_df.empty:
            continue
        author_counts = phase_df["author"].value_counts()
        results.append({
            "phase_number": p["phase_number"],
            "phase": p["phase"],
            "active_contributors": int(phase_df["author"].nunique()),
            "top_contributor": author_counts.index[0] if len(author_counts) > 0 else "N/A",
            "top_contributor_commits": int(author_counts.iloc[0]) if len(author_counts) > 0 else 0,
        })
    return results


# ------------------------------------------------------------------ #
#  Development Phase Detection
# ------------------------------------------------------------------ #

_PHASE_LABELS = {
    "initial_setup": "Initial Setup",
    "feature_dev": "Feature Development",
    "rapid_expansion": "Rapid Expansion",
    "refactoring": "Refactoring & Cleanup",
    "stabilization": "Stabilization",
    "maintenance": "Maintenance",
}


def detect_development_phases(
    df: pd.DataFrame, commit_types: pd.DataFrame
) -> List[Dict]:
    """
    Detect development phases by analyzing commit density and type
    distribution over monthly windows.

    Args:
        df: Full commit DataFrame.
        commit_types: DataFrame with a 'type' column from commit_classifier.

    Returns:
        List of dicts with phase name, start_date, end_date, description.
    """
    if df.empty:
        return []

    # Merge type info
    merged = df.copy()
    if not commit_types.empty and "type" in commit_types.columns:
        merged["type"] = commit_types["type"].values[: len(merged)]
    else:
        merged["type"] = "other"

    merged["month"] = merged["date"].dt.to_period("M")

    phases: List[Dict] = []
    month_groups = merged.groupby("month")

    monthly_stats = []
    for period, group in month_groups:
        type_counts = group["type"].value_counts(normalize=True).to_dict()
        monthly_stats.append({
            "period": period,
            "start": group["date"].min(),
            "end": group["date"].max(),
            "count": len(group),
            "types": type_counts,
            "files_changed": int(group["files_changed"].sum()),
        })

    if not monthly_stats:
        return phases

    # Compute median commit count
    counts = [m["count"] for m in monthly_stats]
    median_count = float(np.median(counts)) if counts else 1.0

    for i, m in enumerate(monthly_stats):
        dominant_type = max(m["types"], key=m["types"].get) if m["types"] else "other"
        ratio = m["count"] / max(median_count, 1)

        if i == 0 and dominant_type in ("chore", "other", "docs"):
            phase_label = "initial_setup"
        elif ratio >= 2.0:
            phase_label = "rapid_expansion"
        elif dominant_type == "feat":
            phase_label = "feature_dev"
        elif dominant_type == "fix":
            phase_label = "stabilization"
        elif dominant_type == "refactor":
            phase_label = "refactoring"
        elif ratio <= 0.3:
            phase_label = "maintenance"
        else:
            phase_label = "feature_dev"

        # Merge with previous if same phase
        if phases and phases[-1]["phase_key"] == phase_label:
            phases[-1]["end_date"] = m["end"]
            phases[-1]["commit_count"] += m["count"]
        else:
            phases.append({
                "phase_key": phase_label,
                "phase": _PHASE_LABELS.get(phase_label, phase_label),
                "start_date": m["start"],
                "end_date": m["end"],
                "commit_count": m["count"],
            })

    # Number the phases
    for idx, p in enumerate(phases, 1):
        p["phase_number"] = idx

    return phases


# ------------------------------------------------------------------ #
#  Structured Summary Builder
# ------------------------------------------------------------------ #

def build_structured_summary(
    stats: Dict,
    contributors: pd.DataFrame,
    phases: List[Dict],
    milestones: List[Dict],
    type_counts: Dict,
    branches: List[Dict] | None = None,
    inactivity_periods: List[Dict] | None = None,
    collab_intensity: List[Dict] | None = None,
) -> str:
    """
    Build a plain-text structured summary suitable for feeding into the
    narrative generator.
    """
    lines = []

    # Basic info
    if stats["first_commit"]:
        lines.append(f"Repository created: {stats['first_commit'].strftime('%B %Y')}")
    if stats["last_commit"]:
        lines.append(f"Latest commit: {stats['last_commit'].strftime('%B %Y')}")
    lines.append(f"Total commits: {stats['total_commits']}")
    lines.append(f"Total contributors: {stats['total_authors']}")
    lines.append(f"Total files changed: {stats['total_files_changed']}")
    lines.append(f"Total lines added: {stats['total_lines_added']}")
    lines.append(f"Total lines deleted: {stats['total_lines_deleted']}")
    lines.append(f"Total merge commits: {stats['total_merges']}")
    lines.append("")

    # Branch info
    if branches:
        lines.append(f"Branches detected: {len(branches)}")
        for b in branches[:10]:
            lines.append(f"  {b['name']}")
        lines.append("")

    # Top contributors
    lines.append("Top contributors:")
    top = contributors.head(10)
    for _, row in top.iterrows():
        lines.append(
            f"  {row['author']} ({int(row['commits'])} commits, "
            f"+{int(row['lines_added'])} / -{int(row['lines_deleted'])} lines)"
        )
    lines.append("")

    # Commit type breakdown
    lines.append("Commit type breakdown:")
    for ctype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        lines.append(f"  {ctype}: {count}")
    lines.append("")

    # Development phases
    lines.append("Development phases detected:")
    for p in phases:
        start = p["start_date"].strftime("%b %Y")
        end = p["end_date"].strftime("%b %Y")
        lines.append(
            f"  Phase {p['phase_number']}: {p['phase']} "
            f"({start} – {end}, {p['commit_count']} commits)"
        )
    lines.append("")

    # Collaboration intensity per phase
    if collab_intensity:
        lines.append("Collaboration intensity per phase:")
        for ci in collab_intensity:
            lines.append(
                f"  Phase {ci['phase_number']} ({ci['phase']}): "
                f"{ci['active_contributors']} contributors, "
                f"top: {ci['top_contributor']} ({ci['top_contributor_commits']} commits)"
            )
        lines.append("")

    # Inactivity periods
    if inactivity_periods:
        lines.append("Periods of inactivity:")
        for gap in inactivity_periods[:5]:
            start = gap["start"].strftime("%b %d, %Y")
            end = gap["end"].strftime("%b %d, %Y")
            lines.append(f"  {start} – {end} ({gap['duration_days']} days)")
        lines.append("")

    # Milestones
    lines.append("Major milestones:")
    for m in milestones:
        date_str = m["date"].strftime("%b %d, %Y")
        lines.append(f"  [{date_str}] {m['description']}")

    return "\n".join(lines)
