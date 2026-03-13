# 📖 Git History Storyteller

**AI-Powered Repository Evolution Analyzer**

A Streamlit web application that analyses the complete Git commit history of any public repository and generates a chronological narrative describing how the project evolved.

---

## ✨ Features

| Feature | Description |
|---|---|
| **GitHub API Integration** | Fetches commit data directly via GitHub REST API — no cloning needed for GitHub URLs (runs in seconds) |
| **Git Clone Fallback** | Falls back to shallow git clone for non-GitHub URLs |
| **Commit Classification** | Automatically categorise commits into 9 types: feat, fix, perf, refactor, test, docs, build/CI, deps, chore |
| **Development Phase Detection** | Identify phases like initial setup, feature development, rapid expansion, stabilisation, refactoring, maintenance |
| **Milestone Detection** | Detect first commit, releases, large refactors, new modules, testing frameworks, infrastructure changes, dependency transitions, contributor growth |
| **Contributor Insights** | Rank contributors, show commit distribution, and analyse collaboration intensity per development phase |
| **Branch Structure** | Extract and display all repository branches |
| **Inactivity Detection** | Identify periods of inactivity (gaps with no commits) in the project timeline |
| **Narrative Generation** | High-quality template narrative by default, with optional Hugging Face AI enhancement when token + provider permissions are available |
| **Interactive Visualisations** | Commit activity charts, contributor bar charts, commit type pie charts, code churn over time |

---

## 🏗️ Architecture

```
User Interface (Streamlit)
        │
        ▼
Data Fetching
  ├── GitHub REST API  (fast, no clone — for github.com URLs)
  └── Git Clone        (fallback for other Git URLs)
        │
        ▼
Data Extraction (commits, authors, timestamps, diffs, branches, tags)
        │
        ▼
Repository Analysis Engine
        ├── Commit Activity Analysis
        ├── Commit Type Classification (9 categories)
        ├── Contributor Analysis & Collaboration Intensity
        ├── Development Phase Detection
        ├── Milestone Detection (10 signal types)
        ├── Branch Structure Extraction
        └── Inactivity Period Detection
        │
        ▼
Structured Repository Summary
        │
        ▼
Narrative Generator
        ├── Template Narrative (default, fast, reliable)
        └── Hugging Face Inference API (optional enhancement)
        │
        ▼
Visualisation + Dashboard (Streamlit)
```

---

## 📂 Project Structure

```
git-history-storyteller/
├── app.py                  # Streamlit main application
├── repo_analyzer.py        # Statistics, phases, summary builder
├── commit_classifier.py    # Keyword-based commit classification
├── milestone_detector.py   # Milestone detection engine
├── narrative_generator.py  # HuggingFace AI narrative generation
├── visualization.py        # matplotlib/seaborn chart generators
├── utils/
│   ├── __init__.py
│   └── git_helpers.py      # GitHub API, git clone, metadata extraction
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Git** installed and available in PATH

### Installation

```bash
# Clone this project
git clone https://github.com/AryaKayastha/git-history-storyteller.git
cd git-history-storyteller

# Create a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### Running the App

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`.

### Stopping the App

Press `Ctrl+C` in the terminal, or force-kill with:
```powershell
Get-Process -Id (Get-NetTCPConnection -LocalPort 8501).OwningProcess | Stop-Process -Force
```

### Usage

1. Enter a **public Git repository URL** in the sidebar (e.g. `https://github.com/psf/requests`)
2. (Recommended) Provide a **GitHub personal access token** for full stats (lines added/deleted) and higher rate limits
3. (Optional) Provide a **Hugging Face API token** for better AI narratives
4. Click **🚀 Analyze Repository**
5. Explore the narrative, milestones, contributor insights, and charts

---

## 🔑 Tokens

### GitHub Token (Recommended)

A GitHub token increases the API rate limit from 60 to 5,000 requests/hour and enables per-commit file/line statistics.

1. Go to **github.com → Settings → Developer settings → Personal access tokens → Fine-grained tokens**
2. Click "Generate new token" — no special permissions needed for public repos
3. Paste the token into the **"GitHub Token"** field in the sidebar

### Hugging Face Token (Optional)

Enables optional AI enhancement via Hugging Face Inference Providers.

Use a **Fine-grained token** and enable:
- **Make calls to Inference Providers**

Without this permission, you may see `403 Forbidden` for provider calls.

---

## 🤖 Narrative Generation Configuration

The app uses this strategy:

| Priority | Method | Requirement |
|---|---|---|
| 1 | Template-based narrative | Always available (default) |
| 2 | Hugging Face Inference API | HF token with provider permissions |

**Model options in UI:**
- `Qwen/Qwen3-8B` (default)
- `Qwen/Qwen3-Coder-Next`
- `meta-llama/Llama-3.1-8B`

Notes:
- Provider/model availability can change over time.
- If API fails or is slow, the app automatically falls back to the template narrative.

---

## 📊 Example Output

After analysing a repository you will see:

- **Key Metrics** — total commits, contributors, lines added/deleted, merges
- **AI Narrative** — a documentary-style chronological story with beginning, development journey, turning points, collaboration patterns, and current state
- **Development Phases** — detected phases with date ranges and commit counts
- **Timeline** — key milestones including releases, module introductions, testing frameworks, infrastructure changes, and dependency transitions
- **Contributor Insights** — ranked table + bar chart + collaboration intensity per phase
- **Inactivity Periods** — detected gaps with no development activity
- **Branch Structure** — all repository branches listed
- **Visualisations** — commit activity over time, commit type distribution (9 categories), code churn charts

---

## 🛠️ Technology Stack

- **Python** — core language
- **Streamlit** — interactive web UI
- **GitHub REST API** — fast commit data fetching (no clone needed)
- **GitPython** — fallback Git repository interaction
- **pandas / numpy** — data processing
- **matplotlib / seaborn** — visualisations
- **huggingface_hub (InferenceClient)** — optional AI narrative enhancement

---

## 📝 License

This project is provided for educational purposes.
