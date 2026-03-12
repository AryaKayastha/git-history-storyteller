"""
Git helper utilities for cloning repositories and extracting commit metadata.

Supports two back-ends:
  1. GitHub REST API  (fast, no clone needed — used for github.com URLs)
  2. Local git clone  (fallback for non-GitHub URLs)
"""

import os
import re
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import requests as _requests
from git import Repo, GitCommandError
import pandas as pd


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GitHub REST API helpers  (no clone required — runs in seconds)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_GITHUB_API = "https://api.github.com"


def parse_github_url(url: str) -> Optional[Tuple[str, str]]:
    """Return (owner, repo) if *url* points to a GitHub repository, else None."""
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$", url.strip())
    return (m.group(1), m.group(2)) if m else None


def _gh_headers(token: Optional[str] = None) -> Dict[str, str]:
    h: Dict[str, str] = {"Accept": "application/vnd.github+json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def fetch_github_commits(
    owner: str,
    repo: str,
    max_commits: int = 500,
    token: Optional[str] = None,
) -> pd.DataFrame:
    """Fetch commit metadata via the GitHub REST API (paginated, very fast).

    Uses only the commit-list endpoint (one call per 100 commits), so 500
    commits need just 5 API calls — well within unauthenticated rate limits.
    """
    headers = _gh_headers(token)
    per_page = 100
    raw_commits: List[Dict] = []
    page = 1

    while len(raw_commits) < max_commits:
        r = _requests.get(
            f"{_GITHUB_API}/repos/{owner}/{repo}/commits",
            headers=headers,
            params={"per_page": per_page, "page": page},
            timeout=30,
        )
        if r.status_code == 403:
            # Rate-limited — return whatever we have so far.
            break
        r.raise_for_status()
        data = r.json()
        if not data:
            break
        raw_commits.extend(data)
        if len(data) < per_page:
            break
        page += 1

    raw_commits = raw_commits[:max_commits]

    # ── Per-commit stats (only when authenticated — 5000 req/hr) ──
    stats_map: Dict[str, Tuple[int, int, int]] = {}
    if token:
        def _fetch_one(sha: str) -> Tuple[str, int, int, int]:
            try:
                resp = _requests.get(
                    f"{_GITHUB_API}/repos/{owner}/{repo}/commits/{sha}",
                    headers=headers,
                    timeout=15,
                )
                if resp.status_code == 200:
                    d = resp.json()
                    s = d.get("stats", {})
                    return sha, s.get("additions", 0), s.get("deletions", 0), len(d.get("files", []))
            except Exception:
                pass
            return sha, 0, 0, 0

        with ThreadPoolExecutor(max_workers=20) as pool:
            futures = {pool.submit(_fetch_one, c["sha"]): c["sha"] for c in raw_commits}
            for fut in as_completed(futures):
                sha, added, deleted, files = fut.result()
                stats_map[sha] = (added, deleted, files)

    # ── Build DataFrame ──────────────────────────────────────────
    rows: List[Dict] = []
    for c in raw_commits:
        ci = c.get("commit", {})
        ai = ci.get("author") or {}
        sha = c["sha"]
        s = stats_map.get(sha, (0, 0, 0))
        try:
            dt = datetime.strptime(ai.get("date", ""), "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            dt = datetime.utcnow()
        rows.append({
            "hash": sha,
            "short_hash": sha[:7],
            "author": ai.get("name", "Unknown"),
            "author_email": ai.get("email", ""),
            "date": dt,
            "message": ci.get("message", "").strip().split("\n")[0],
            "files_changed": s[2],
            "lines_added": s[0],
            "lines_deleted": s[1],
            "is_merge": len(c.get("parents", [])) > 1,
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
    return df


def fetch_github_tags(
    owner: str, repo: str, token: Optional[str] = None
) -> List[Dict]:
    """Fetch tags via the GitHub REST API."""
    headers = _gh_headers(token)
    tags: List[Dict] = []
    try:
        r = _requests.get(
            f"{_GITHUB_API}/repos/{owner}/{repo}/tags",
            headers=headers,
            params={"per_page": 100},
            timeout=15,
        )
        if r.status_code != 200:
            return tags
        for t in r.json():
            sha = t["commit"]["sha"]
            tags.append({"name": t["name"], "date": datetime.utcnow(), "hash": sha})
    except Exception:
        pass
    return tags


def fetch_github_branches(
    owner: str, repo: str, token: Optional[str] = None
) -> List[Dict]:
    """Fetch branches via the GitHub REST API."""
    headers = _gh_headers(token)
    branches: List[Dict] = []
    try:
        r = _requests.get(
            f"{_GITHUB_API}/repos/{owner}/{repo}/branches",
            headers=headers,
            params={"per_page": 100},
            timeout=15,
        )
        r.raise_for_status()
        for b in r.json():
            branches.append({
                "name": b["name"],
                "latest_commit": b["commit"]["sha"][:7],
            })
    except Exception:
        pass
    return branches


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Local git-clone helpers  (fallback for non-GitHub URLs)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def clone_repository(repo_url: str, clone_dir: Optional[str] = None, depth: Optional[int] = None) -> Repo:
    """
    Clone a public Git repository to a local temporary directory.

    Args:
        repo_url: URL of the public Git repository.
        clone_dir: Optional directory to clone into. Uses a temp dir if None.
        depth: If set, perform a shallow clone limited to this many commits.

    Returns:
        A GitPython Repo object.

    Raises:
        GitCommandError: If cloning fails.
    """
    if clone_dir is None:
        clone_dir = tempfile.mkdtemp(prefix="git_storyteller_")

    if os.path.exists(clone_dir) and os.listdir(clone_dir):
        shutil.rmtree(clone_dir)

    clone_kwargs: Dict = {}
    if depth:
        clone_kwargs["depth"] = depth

    # --single-branch + --no-tags fetches only the default branch and skip tag objects,
    # which is the biggest speedup for large repos. We intentionally skip
    # --filter=blob:none because that causes lazy blob fetches when computing
    # per-commit stats, making extraction slower than a plain shallow clone.
    clone_kwargs["multi_options"] = ["--single-branch", "--no-tags"]

    try:
        repo = Repo.clone_from(repo_url, clone_dir, **clone_kwargs)
    except GitCommandError:
        # Fallback: plain clone without any extra options.
        fallback_kwargs: Dict = {}
        if depth:
            fallback_kwargs["depth"] = depth
        repo = Repo.clone_from(repo_url, clone_dir, **fallback_kwargs)
    return repo


def extract_commit_metadata(repo: Repo, max_commits: int = 500) -> pd.DataFrame:
    """
    Extract metadata from every commit using a single ``git log --numstat``
    invocation.  This is orders of magnitude faster than iterating GitPython
    commit objects because it avoids per-commit Python overhead and does not
    require lazy blob fetches.

    Args:
        repo: A GitPython Repo object.
        max_commits: Maximum number of commits to process.

    Returns:
        A pandas DataFrame with commit metadata.
    """
    # Custom separator unlikely to appear in commit messages.
    SEP = "\x00COMMIT\x00"
    # Format: SEP + fields delimited by |
    log_format = f"{SEP}%H|%h|%an|%ae|%ct|%s|%P"

    try:
        raw = repo.git.log(
            "--all",
            f"--max-count={max_commits}",
            f"--format={log_format}",
            "--numstat",
        )
    except Exception:
        return pd.DataFrame()

    commits_data: List[Dict] = []
    current: Optional[Dict] = None

    for line in raw.splitlines():
        if line.startswith(SEP):
            if current is not None:
                commits_data.append(current)
            parts = line[len(SEP):].split("|", 6)
            if len(parts) < 6:
                current = None
                continue
            parents_raw = parts[6].split() if len(parts) > 6 else []
            try:
                ts = int(parts[4])
                commit_date = datetime.fromtimestamp(ts)
            except (ValueError, OSError):
                commit_date = datetime.utcnow()
            current = {
                "hash": parts[0],
                "short_hash": parts[1],
                "author": parts[2],
                "author_email": parts[3],
                "date": commit_date,
                "message": parts[5].strip(),
                "files_changed": 0,
                "lines_added": 0,
                "lines_deleted": 0,
                "is_merge": len(parents_raw) > 1,
            }
        elif current is not None and line.strip():
            # numstat line: "<added>\t<deleted>\t<filename>"
            # Binary files are shown as "-\t-\t<filename>"
            parts = line.split("\t", 2)
            if len(parts) >= 2:
                try:
                    current["lines_added"] += int(parts[0])
                    current["lines_deleted"] += int(parts[1])
                    current["files_changed"] += 1
                except ValueError:
                    # Binary file — count file but skip line numbers
                    current["files_changed"] += 1

    if current is not None:
        commits_data.append(current)

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
