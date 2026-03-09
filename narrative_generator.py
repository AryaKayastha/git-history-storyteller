"""
Narrative Generator — uses a Hugging Face summarisation / text-generation
model to convert the structured repository summary into a human-readable
chronological narrative about the project's evolution.

Supports two back-ends:
  1. Hugging Face Inference API  (free, requires HF_TOKEN env var)
  2. Local transformers pipeline (fallback, uses facebook/bart-large-cnn)
"""

import os
import textwrap
from typing import Optional

# ------------------------------------------------------------------ #
#  Hugging Face Inference API
# ------------------------------------------------------------------ #

_HF_API_URL = "https://api-inference.huggingface.co/models/"
_DEFAULT_MODEL = "facebook/bart-large-cnn"


def _call_hf_api(prompt: str, model: str, token: str, max_length: int = 512) -> str:
    """Call the Hugging Face Inference API."""
    import requests

    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_length": max_length,
            "min_length": 80,
            "do_sample": False,
        },
    }
    response = requests.post(
        _HF_API_URL + model,
        headers=headers,
        json=payload,
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()

    if isinstance(data, list) and data:
        return data[0].get("summary_text", data[0].get("generated_text", str(data)))
    return str(data)


# ------------------------------------------------------------------ #
#  Local transformers pipeline (fallback)
# ------------------------------------------------------------------ #

def _run_local_pipeline(prompt: str, model: str, max_length: int = 512) -> str:
    """Run a local Hugging Face pipeline."""
    from transformers import pipeline

    summarizer = pipeline("summarization", model=model)
    # BART-large-cnn has a 1024 token limit — truncate
    truncated = prompt[:3000]
    result = summarizer(
        truncated,
        max_length=max_length,
        min_length=80,
        do_sample=False,
    )
    if result and isinstance(result, list):
        return result[0].get("summary_text", "")
    return str(result)


# ------------------------------------------------------------------ #
#  Smart template-based narrative (always available, no API needed)
# ------------------------------------------------------------------ #

def _template_narrative(summary: str) -> str:
    """
    Generate a rich, documentary-style narrative from the structured summary.
    Produces a chronological story with beginning, middle, turning points,
    collaboration insights, and current state summary.
    """
    lines = summary.strip().split("\n")
    sections = {
        "meta": [],
        "contributors": [],
        "types": [],
        "phases": [],
        "milestones": [],
        "collaboration": [],
        "inactivity": [],
        "branches": [],
    }
    current = "meta"
    for line in lines:
        lower = line.strip().lower()
        if lower.startswith("top contributor"):
            current = "contributors"
            continue
        elif lower.startswith("commit type"):
            current = "types"
            continue
        elif lower.startswith("development phase"):
            current = "phases"
            continue
        elif lower.startswith("major milestone"):
            current = "milestones"
            continue
        elif lower.startswith("collaboration intensity"):
            current = "collaboration"
            continue
        elif lower.startswith("periods of inactivity") or lower.startswith("period of inactivity"):
            current = "inactivity"
            continue
        elif lower.startswith("branches detected"):
            current = "branches"
            continue
        stripped = line.strip()
        if stripped:
            sections[current].append(stripped)

    paragraphs = []

    # ── Beginning: Project Origin ──
    meta_text = ". ".join(sections["meta"])
    paragraphs.append(
        f"**The Beginning** — {meta_text}. "
        "The repository was initialized, laying the groundwork for what would become "
        "a multi-phase software development effort. The first commits established the "
        "foundational project structure, configuration, and core architecture."
    )

    # ── Branch context ──
    if sections["branches"]:
        branch_list = ", ".join(sections["branches"][:5])
        paragraphs.append(
            f"The repository's branching structure includes: {branch_list}. "
            "These branches reflect the development workflow, feature isolation, "
            "and release management strategies adopted by the team."
        )

    # ── Contributor introduction ──
    if sections["contributors"]:
        contribs = "; ".join(sections["contributors"][:5])
        remaining = len(sections["contributors"]) - 5
        extra = f" and {remaining} other contributors" if remaining > 0 else ""
        paragraphs.append(
            f"**The Team** — The project was shaped by several key contributors. "
            f"The most active include: {contribs}{extra}. "
            "Their combined efforts — across features, bug fixes, refactoring, "
            "and maintenance — drove the repository through each stage of its lifecycle."
        )

    # ── Middle: Development Phases ──
    if sections["phases"]:
        paragraphs.append("**Development Journey** — The repository's evolution "
                          "can be broken down into the following phases:")
        for phase_line in sections["phases"]:
            paragraphs.append(f"  • {phase_line}")
        paragraphs.append(
            "Each phase reflects a distinct period of activity where the team "
            "shifted its focus — from building new features, to stabilizing "
            "the codebase, to refactoring and improving code quality."
        )

    # ── Commit type analysis ──
    if sections["types"]:
        types_text = ", ".join(sections["types"][:8])
        paragraphs.append(
            f"**Activity Breakdown** — Analysing the commit messages reveals: "
            f"{types_text}. This distribution illustrates the balance between "
            "new feature work, bug fixing, performance optimization, dependency "
            "management, testing, and general maintenance."
        )

    # ── Collaboration intensity ──
    if sections["collaboration"]:
        paragraphs.append(
            "**Collaboration Patterns** — The intensity of collaboration varied "
            "across development phases:"
        )
        for ci_line in sections["collaboration"]:
            paragraphs.append(f"  • {ci_line}")
        paragraphs.append(
            "This shows how the team expanded and contracted at different "
            "stages — from solo early development to collaborative feature "
            "sprints and focused maintenance periods."
        )

    # ── Turning points: Milestones ──
    if sections["milestones"]:
        paragraphs.append(
            "**Key Turning Points** — Several milestones marked significant "
            "moments in the project's history:"
        )
        for ms in sections["milestones"][:12]:
            paragraphs.append(f"  • {ms}")
        paragraphs.append(
            "These events represent the introduction of major features, "
            "architectural changes, infrastructure updates, testing frameworks, "
            "and scaling milestones that shaped the project's trajectory."
        )

    # ── Inactivity periods ──
    if sections["inactivity"]:
        paragraphs.append(
            "**Periods of Inactivity** — The repository experienced notable "
            "quiet periods:"
        )
        for gap_line in sections["inactivity"][:5]:
            paragraphs.append(f"  • {gap_line}")
        paragraphs.append(
            "These gaps may reflect planning phases, team transitions, "
            "or stable production periods with minimal code changes."
        )

    # ── Current State ──
    paragraphs.append(
        "**Current State** — Looking at the repository today, the commit history "
        "tells a compelling story of iterative development, collaboration, and "
        "continuous improvement. The project has evolved through distinct phases "
        "of growth and stabilization, with contributions from multiple developers "
        "shaping its architecture and functionality. The repository remains a "
        "living record of the engineering decisions, trade-offs, and innovations "
        "that brought the software to its current form."
    )

    return "\n\n".join(paragraphs)


# ------------------------------------------------------------------ #
#  Public API
# ------------------------------------------------------------------ #

def generate_narrative(
    structured_summary: str,
    model: str = _DEFAULT_MODEL,
    hf_token: Optional[str] = None,
    use_api: bool = True,
) -> str:
    """
    Generate a chronological narrative from the structured summary.

    Strategy:
      1. If hf_token is available ⇒ try Hugging Face Inference API.
      2. Else try local transformers pipeline.
      3. If both fail ⇒ fall back to template narrative.

    Args:
        structured_summary: Plain-text repository summary.
        model: Hugging Face model ID.
        hf_token: Optional Hugging Face API token.
        use_api: Whether to try the API first.

    Returns:
        A narrative string.
    """
    prompt = textwrap.dedent(f"""\
        Convert the following repository analysis into a structured chronological
        narrative describing how the software project evolved over time.

        DATA:
        {structured_summary}
    """)

    token = hf_token or os.environ.get("HF_TOKEN", "")

    # --- Attempt 1: API ---
    if use_api and token:
        try:
            return _call_hf_api(prompt, model, token)
        except Exception as e:
            print(f"[narrative_generator] API call failed: {e}")

    # --- Attempt 2: local pipeline ---
    try:
        return _run_local_pipeline(prompt, model)
    except Exception as e:
        print(f"[narrative_generator] Local pipeline failed: {e}")

    # --- Attempt 3: template ---
    return _template_narrative(structured_summary)
