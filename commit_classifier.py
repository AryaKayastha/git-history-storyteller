"""
Commit Classifier — categorises each commit message into a development
activity type (feat, fix, refactor, test, docs, chore, other).
"""

import re
from typing import Dict, List

import pandas as pd

# ------------------------------------------------------------------ #
#  Keyword rules  (order matters — first match wins)
# ------------------------------------------------------------------ #

_CLASSIFICATION_RULES: List[Dict] = [
    {
        "type": "feat",
        "label": "Feature",
        "patterns": [
            r"\bfeat\b", r"\badd\b", r"\bnew\b", r"\bimplement\b",
            r"\bintroduc", r"\bcreate\b", r"\bsupport\b",
        ],
    },
    {
        "type": "fix",
        "label": "Bug Fix",
        "patterns": [
            r"\bfix\b", r"\bbug\b", r"\bpatch\b", r"\bresolve\b",
            r"\bhotfix\b", r"\bcorrect\b", r"\brepair\b",
        ],
    },
    {
        "type": "perf",
        "label": "Performance",
        "patterns": [
            r"\bperf\b", r"\bperformance\b", r"\boptimiz", r"\bspeed\b",
            r"\bfaster\b", r"\bcache\b", r"\bcaching\b", r"\bmemory\b",
            r"\bbenchmark", r"\blatency\b", r"\bthroughput\b",
        ],
    },
    {
        "type": "refactor",
        "label": "Refactor",
        "patterns": [
            r"\brefactor\b", r"\brestructur", r"\bclean\s?up\b",
            r"\breorganiz", r"\bsimplif", r"\bmoderniz",
        ],
    },
    {
        "type": "test",
        "label": "Test",
        "patterns": [
            r"\btest\b", r"\bspec\b", r"\bcoverage\b",
            r"\bassert\b", r"\bmock\b", r"\bpytest\b", r"\bjest\b",
            r"\bunittest\b", r"\be2e\b",
        ],
    },
    {
        "type": "docs",
        "label": "Documentation",
        "patterns": [
            r"\bdoc\b", r"\bdocs\b", r"\breadme\b", r"\bchangelog\b",
            r"\bcomment\b", r"\btypedoc\b", r"\bjsdoc\b",
        ],
    },
    {
        "type": "build",
        "label": "Build / CI",
        "patterns": [
            r"\bci\b", r"\bbuild\b", r"\bgithub.actions\b", r"\bjenkins\b",
            r"\bdocker\b", r"\btravis\b", r"\bcircle\s?ci\b",
            r"\bmakefile\b", r"\bwebpack\b", r"\bgulp\b", r"\bpipeline\b",
            r"\bworkflow\b", r"\binfra\b", r"\bdeploy\b",
        ],
    },
    {
        "type": "deps",
        "label": "Dependency",
        "patterns": [
            r"\bdep\b", r"\bdeps\b", r"\bdependenc", r"\bbump\b",
            r"\bupgrade\b", r"\bpackage\b", r"\bnpm\b", r"\bpip\b",
            r"\byarn\b", r"\brequirements?\.txt\b",
        ],
    },
    {
        "type": "chore",
        "label": "Maintenance / Chore",
        "patterns": [
            r"\bchore\b", r"\bversion\b",
            r"\bconfig\b", r"\bsetup\b", r"\binit\b", r"\bmerge\b",
            r"\bupdate\b", r"\bmiscellaneous\b", r"\bmisc\b",
        ],
    },
]


def classify_commit(message: str) -> str:
    """
    Classify a single commit message into a type string.

    Returns one of: feat, fix, refactor, test, docs, chore, other.
    """
    msg_lower = message.lower()
    for rule in _CLASSIFICATION_RULES:
        for pattern in rule["patterns"]:
            if re.search(pattern, msg_lower):
                return rule["type"]
    return "other"


def classify_commits(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a 'type' and 'type_label' column to the commits DataFrame.

    Args:
        df: DataFrame with a 'message' column.

    Returns:
        A copy of the DataFrame with 'type' and 'type_label' columns.
    """
    if df.empty:
        return df.assign(type=pd.Series(dtype=str), type_label=pd.Series(dtype=str))

    label_map = {rule["type"]: rule["label"] for rule in _CLASSIFICATION_RULES}
    label_map["other"] = "Other"

    result = df.copy()
    result["type"] = result["message"].apply(classify_commit)
    result["type_label"] = result["type"].map(label_map)
    return result


def commit_type_counts(df: pd.DataFrame) -> Dict[str, int]:
    """
    Return a dict mapping commit type → count.

    Args:
        df: DataFrame that already has a 'type' column (output of classify_commits).
    """
    if df.empty or "type" not in df.columns:
        return {}
    return df["type"].value_counts().to_dict()
