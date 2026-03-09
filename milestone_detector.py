"""
Milestone Detector — identifies significant events in the repository
history such as initial commit, large refactors, new modules, releases,
and contributor growth spikes.
"""

from typing import Dict, List

import numpy as np
import pandas as pd


def detect_milestones(
    df: pd.DataFrame,
    tags: List[Dict],
    classified_df: pd.DataFrame | None = None,
) -> List[Dict]:
    """
    Detect important repository milestones.

    Signals used:
      - Initial commit
      - Release tags
      - Commits with an unusually large number of files changed
      - Sudden commit-density spikes
      - Large additions / deletions in a single commit
      - Contributor growth (first commit by a new contributor)

    Args:
        df: Commit metadata DataFrame (sorted by date ascending).
        tags: List of tag dicts from git_helpers.get_tags().
        classified_df: Optional classified DataFrame with 'type' column.

    Returns:
        List of milestone dicts sorted by date, each with:
          date, description, commit_hash, milestone_type
    """
    milestones: List[Dict] = []

    if df.empty:
        return milestones

    # ---- 1. Initial commit ----
    first = df.iloc[0]
    milestones.append({
        "date": first["date"],
        "description": "Repository initialized – first commit",
        "commit_hash": first["hash"],
        "milestone_type": "initial_commit",
    })

    # ---- 2. Release tags ----
    for tag in tags:
        milestones.append({
            "date": tag["date"],
            "description": f"Release tag: {tag['name']}",
            "commit_hash": tag["hash"],
            "milestone_type": "release",
        })

    # ---- 3. Large file-change commits (> 3× median) ----
    if len(df) > 5:
        median_files = df["files_changed"].median()
        threshold = max(median_files * 3, 10)
        big_changes = df[df["files_changed"] >= threshold]
        for _, row in big_changes.iterrows():
            first_line = row["message"].split("\n")[0][:80]
            milestones.append({
                "date": row["date"],
                "description": (
                    f"Large change ({int(row['files_changed'])} files): {first_line}"
                ),
                "commit_hash": row["hash"],
                "milestone_type": "large_change",
            })

    # ---- 4. Major addition bursts (> 3× median lines added) ----
    if len(df) > 5:
        median_add = df["lines_added"].median()
        threshold_add = max(median_add * 4, 200)
        big_adds = df[df["lines_added"] >= threshold_add]
        for _, row in big_adds.iterrows():
            first_line = row["message"].split("\n")[0][:80]
            milestones.append({
                "date": row["date"],
                "description": (
                    f"Major code addition (+{int(row['lines_added'])} lines): "
                    f"{first_line}"
                ),
                "commit_hash": row["hash"],
                "milestone_type": "major_addition",
            })

    # ---- 5. Commit-density spikes (weekly) ----
    if len(df) > 20:
        weekly = df.set_index("date").resample("W").size()
        if len(weekly) > 4:
            median_weekly = weekly.median()
            spike_threshold = max(median_weekly * 3, 10)
            spikes = weekly[weekly >= spike_threshold]
            for week_end, count in spikes.items():
                milestones.append({
                    "date": week_end,
                    "description": f"Commit spike: {int(count)} commits this week",
                    "commit_hash": "",
                    "milestone_type": "commit_spike",
                })

    # ---- 6. New contributor milestones ----
    seen_authors = set()
    contributor_count = 0
    contributor_thresholds = {5, 10, 20, 50, 100}
    for _, row in df.iterrows():
        if row["author"] not in seen_authors:
            seen_authors.add(row["author"])
            contributor_count += 1
            if contributor_count in contributor_thresholds:
                milestones.append({
                    "date": row["date"],
                    "description": (
                        f"Contributor milestone: {contributor_count} contributors"
                    ),
                    "commit_hash": row["hash"],
                    "milestone_type": "contributor_growth",
                })

    # ---- 7. Testing framework introduction ----
    test_patterns = [
        r"\bpytest\b", r"\bjest\b", r"\bunittest\b", r"\bmocha\b",
        r"\btest suite\b", r"\bcoverage\b", r"\be2e\b", r"\bspec\b",
        r"\bci.*test", r"\btest.*framework",
    ]
    _detect_pattern_milestone(
        df, test_patterns, milestones,
        desc_prefix="Testing framework introduced",
        milestone_type="testing_introduction",
        max_hits=3,
    )

    # ---- 8. New module / component introduction ----
    module_patterns = [
        r"\bnew module\b", r"\badd.*module\b", r"\bintroduc.*component\b",
        r"\bnew package\b", r"\badd.*package\b", r"\badd.*service\b",
        r"\bnew.*api\b", r"\bcreate.*module\b", r"\binitial.*module\b",
    ]
    _detect_pattern_milestone(
        df, module_patterns, milestones,
        desc_prefix="New module/component introduced",
        milestone_type="module_introduction",
        max_hits=5,
    )

    # ---- 9. Infrastructure / build system changes ----
    infra_patterns = [
        r"\bdocker\b", r"\bci\b.*\bcd\b", r"\bgithub.actions\b",
        r"\bjenkins\b", r"\btravis\b", r"\bcircle\s?ci\b",
        r"\bkubernetes\b", r"\bterraform\b", r"\bwebpack\b",
        r"\bmakefile\b", r"\bbuild system\b", r"\binfra\b",
        r"\bdeploy\b", r"\bpipeline\b",
    ]
    _detect_pattern_milestone(
        df, infra_patterns, milestones,
        desc_prefix="Infrastructure/build change",
        milestone_type="infrastructure_change",
        max_hits=5,
    )

    # ---- 10. Major dependency transitions ----
    deps_patterns = [
        r"\bmigrat\b", r"\bupgrade.*major\b", r"\bmajor.*upgrade\b",
        r"\bswitch.*from\b", r"\breplace.*with\b", r"\bdep.*major\b",
        r"\bbreaking.*change\b",
    ]
    _detect_pattern_milestone(
        df, deps_patterns, milestones,
        desc_prefix="Major dependency transition",
        milestone_type="dependency_transition",
        max_hits=3,
    )

    # ---- Deduplicate & sort ----
    milestones = _deduplicate_milestones(milestones)
    milestones.sort(key=lambda m: m["date"])

    return milestones


def _detect_pattern_milestone(
    df: pd.DataFrame,
    patterns: List[str],
    milestones: List[Dict],
    desc_prefix: str,
    milestone_type: str,
    max_hits: int = 3,
):
    """Helper: scan commit messages for regex patterns and add milestones."""
    import re
    hits = 0
    for _, row in df.iterrows():
        if hits >= max_hits:
            break
        msg = row["message"].lower()
        for pat in patterns:
            if re.search(pat, msg):
                first_line = row["message"].split("\n")[0][:80]
                milestones.append({
                    "date": row["date"],
                    "description": f"{desc_prefix}: {first_line}",
                    "commit_hash": row["hash"],
                    "milestone_type": milestone_type,
                })
                hits += 1
                break


def _deduplicate_milestones(milestones: List[Dict]) -> List[Dict]:
    """Remove duplicate milestones by commit_hash + milestone_type."""
    seen = set()
    unique = []
    for m in milestones:
        key = (m.get("commit_hash", ""), m["milestone_type"])
        if key not in seen:
            seen.add(key)
            unique.append(m)
    return unique
