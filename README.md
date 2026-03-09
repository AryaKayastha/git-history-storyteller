# 📖 Git History Storyteller

**AI-Powered Repository Evolution Analyzer**

A Streamlit web application that analyses the complete Git commit history of any public repository and generates a chronological narrative describing how the project evolved — powered by Hugging Face AI models.

---

## ✨ Features

| Feature | Description |
|---|---|
| **Repository Ingestion** | Clone any public Git repo and extract full commit metadata, branches, and tags |
| **Commit Classification** | Automatically categorise commits into 9 types: feat, fix, perf, refactor, test, docs, build/CI, deps, chore |
| **Development Phase Detection** | Identify phases like initial setup, feature development, rapid expansion, stabilisation, refactoring, maintenance |
| **Milestone Detection** | Detect first commit, releases, large refactors, new modules, testing frameworks, infrastructure changes, dependency transitions, contributor growth |
| **Contributor Insights** | Rank contributors, show commit distribution, and analyse collaboration intensity per development phase |
| **Branch Structure** | Extract and display all repository branches |
| **Inactivity Detection** | Identify periods of inactivity (gaps with no commits) in the project timeline |
| **AI Narrative Generation** | Hugging Face–powered documentary-style chronological story with beginning, turning points, collaboration evolution, and current state |
| **Interactive Visualisations** | Commit activity charts, contributor bar charts, commit type pie charts, code churn over time |

---

## 🏗️ Architecture

```
User Interface (Streamlit)
        │
        ▼
Repository Ingestion (GitPython)
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
Narrative Generator (Hugging Face)
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
│   └── git_helpers.py      # Git clone, metadata extraction, cleanup
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
git clone <this-repo-url>
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

### Usage

1. Enter a **public Git repository URL** in the sidebar (e.g. `https://github.com/psf/requests`)
2. (Optional) Provide a **Hugging Face API token** for better AI narratives
3. Click **🚀 Analyze Repository**
4. Explore the narrative, milestones, contributor insights, and charts

---

## 🤖 AI Model Configuration

The narrative generator supports three strategies (tried in order):

| Priority | Method | Requirement |
|---|---|---|
| 1 | Hugging Face Inference API | Set `HF_TOKEN` env var or provide token in UI |
| 2 | Local `transformers` pipeline | `transformers` + `torch` installed |
| 3 | Template-based narrative | Always works — no API / GPU needed |

**Supported models:**
- `facebook/bart-large-cnn` (default — best for summarisation)
- `t5-small` (lightweight alternative)
- `sshleifer/distilbart-cnn-12-6` (distilled, faster)

To set your Hugging Face token as an environment variable:

```bash
# Windows
set HF_TOKEN=hf_your_token_here

# macOS/Linux
export HF_TOKEN=hf_your_token_here
```

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

- **Python**
- **Streamlit** — interactive web UI
- **GitPython** — Git repository interaction
- **pandas / numpy** — data processing
- **matplotlib / seaborn** — visualisations
- **Hugging Face transformers** — AI narrative generation

---

## 📝 License

This project is provided for educational purposes.
