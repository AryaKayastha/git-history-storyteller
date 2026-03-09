"""
Git helper utilities for cloning repositories and extracting commit metadata.
"""

import os
import shutil
import tempfile
from datetime import datetime
from typing import Dict, List, Optional

from git import Repo, GitCommandError
import pandas as pd


def clone_repository(repo_url: str, clone_dir: Optional[str] = None) -> Repo:
    """
    Clone a public Git repository to a local temporary directory.

    Args:
        repo_url: URL of the public Git repository.
        clone_dir: Optional directory to clone into. Uses a temp dir if None.

    Returns:
        A GitPython Repo object.

    Raises:
        GitCommandError: If cloning fails.
    """
    if clone_dir is None:
        clone_dir = tempfile.mkdtemp(prefix="git_storyteller_")

    if os.path.exists(clone_dir) and os.listdir(clone_dir):
        shutil.rmtree(clone_dir)

    repo = Repo.clone_from(repo_url, clone_dir, depth=None)
    return repo


def extract_commit_metadata(repo: Repo, max_commits: int = 5000) -> pd.DataFrame:
    """
    Extract metadata from every commit in the repository.

    Args:
        repo: A GitPython Repo object.
        max_commits: Maximum number of commits to process.

    Returns:
        A pandas DataFrame with commit metadata.
    """
    commits_data: List[Dict] = []

    for i, commit in enumerate(repo.iter_commits("--all")):
        if i >= max_commits:
            break

        # Calculate files changed, lines added/deleted
        files_changed = 0
        lines_added = 0
        lines_deleted = 0

        try:
            stats = commit.stats.total
            files_changed = stats.get("files", 0)
            lines_added = stats.get("insertions", 0)
            lines_deleted = stats.get("deletions", 0)
        except Exception:
            pass

        # Check if commit is a merge
        is_merge = len(commit.parents) > 1

        commits_data.append({
            "hash": commit.hexsha,
            "short_hash": commit.hexsha[:7],
            "author": commit.author.name,
            "author_email": commit.author.email,
            "date": datetime.fromtimestamp(commit.committed_date),
            "message": commit.message.strip(),
            "files_changed": files_changed,
            "lines_added": lines_added,
            "lines_deleted": lines_deleted,
            "is_merge": is_merge,
        })

    df = pd.DataFrame(commits_data)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)

    return df


def get_tags(repo: Repo) -> List[Dict]:
    """
    Extract tag information from the repository.

    Returns:
        List of dicts with tag name, date, and associated commit hash.
    """
    tags_data = []
    for tag in repo.tags:
        try:
            commit = tag.commit
            tags_data.append({
                "name": tag.name,
                "date": datetime.fromtimestamp(commit.committed_date),
                "hash": commit.hexsha,
            })
        except Exception:
            pass

    return sorted(tags_data, key=lambda t: t["date"])


def cleanup_repo(repo: Repo):
    """Remove the cloned repository from disk."""
    repo_dir = repo.working_dir
    try:
        repo.close()
        shutil.rmtree(repo_dir, ignore_errors=True)
    except Exception:
        pass


def get_branches(repo: Repo) -> List[Dict]:
    """
    Extract branch information from the repository.

    Returns:
        List of dicts with branch name and latest commit hash.
    """
    branches_data = []
    try:
        for ref in repo.references:
            try:
                name = str(ref)
                if "HEAD" in name:
                    continue
                commit = ref.commit
                branches_data.append({
                    "name": name,
                    "latest_commit": commit.hexsha[:7],
                    "date": datetime.fromtimestamp(commit.committed_date),
                })
            except Exception:
                pass
    except Exception:
        pass

    return branches_data


def detect_inactivity_periods(df, threshold_days: int = 30) -> List[Dict]:
    """
    Detect periods of inactivity where no commits were made for
    more than `threshold_days` days.

    Args:
        df: Commit DataFrame sorted by date.
        threshold_days: Minimum gap in days to consider as inactivity.

    Returns:
        List of dicts with start, end, and duration_days.
    """
    if df is None or len(df) < 2:
        return []

    dates = df["date"].sort_values().reset_index(drop=True)
    gaps = []
    for i in range(1, len(dates)):
        delta = (dates.iloc[i] - dates.iloc[i - 1]).days
        if delta >= threshold_days:
            gaps.append({
                "start": dates.iloc[i - 1],
                "end": dates.iloc[i],
                "duration_days": delta,
            })

    return sorted(gaps, key=lambda g: -g["duration_days"])
