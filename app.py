"""
Git History Storyteller — Streamlit Application

An AI-powered repository evolution analyzer that accepts a public Git
repository URL, analyses its complete commit history, detects patterns
and milestones, and generates a chronological narrative with interactive
visualisations.
"""

import os
import streamlit as st

# ── Local modules ──────────────────────────────────────────────────
from utils.git_helpers import clone_repository, extract_commit_metadata, get_tags, cleanup_repo, get_branches, detect_inactivity_periods
from commit_classifier import classify_commits, commit_type_counts
from repo_analyzer import (
    compute_commit_statistics,
    commits_per_month,
    contributor_analysis,
    detect_development_phases,
    build_structured_summary,
    collaboration_intensity_per_phase,
)
from milestone_detector import detect_milestones
from narrative_generator import generate_narrative
from visualization import (
    plot_commits_per_month,
    plot_contributor_commits,
    plot_commit_types,
    plot_lines_over_time,
)

# ── Page config ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Git History Storyteller",
    page_icon="📖",
    layout="wide",
)

# ── Custom CSS ─────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #6366f1, #8b5cf6, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        text-align: center;
        color: #9ca3af;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .milestone-card {
        background: #1e1e2e;
        border-left: 4px solid #8b5cf6;
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .milestone-date {
        color: #a78bfa;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .milestone-desc {
        color: #e2e8f0;
        font-size: 0.95rem;
    }
    .phase-badge {
        display: inline-block;
        background: #312e81;
        color: #c4b5fd;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 0.82rem;
        margin: 2px 4px;
    }
    .stat-card {
        background: #1e1e2e;
        padding: 16px;
        border-radius: 12px;
        text-align: center;
    }
    .stat-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #a78bfa;
    }
    .stat-label {
        color: #9ca3af;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────
st.markdown('<div class="main-title">📖 Git History Storyteller</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">AI-Powered Repository Evolution Analyzer</div>', unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Settings")
    repo_url = st.text_input(
        "GitHub Repository URL",
        placeholder="https://github.com/psf/requests",
        help="Enter any public Git repository URL",
    )
    hf_token = st.text_input(
        "Hugging Face Token (optional)",
        type="password",
        help="Provide a HF token to use the Inference API for better narratives",
    )
    hf_model = st.selectbox(
        "AI Model",
        [
            "facebook/bart-large-cnn",
            "t5-small",
            "sshleifer/distilbart-cnn-12-6",
        ],
        index=0,
    )
    max_commits = st.slider("Max commits to analyse", 100, 5000, 500, step=100)
    analyze_btn = st.button("🚀 Analyze Repository", type="primary", use_container_width=True)

    st.markdown("---")
    st.markdown(
        "**How it works**\n\n"
        "1. Clones the repository\n"
        "2. Extracts all commit metadata\n"
        "3. Classifies commits & detects milestones\n"
        "4. Generates a chronological narrative using AI\n"
        "5. Visualises patterns & insights"
    )

# ── Main analysis flow ────────────────────────────────────────────
if analyze_btn and repo_url:
    repo = None
    try:
        # ── Step 1: Clone ──────────────────────────────────────────
        with st.status("🔄 Analysing repository...", expanded=True) as status:
            st.write("📥 Cloning repository...")
            repo = clone_repository(repo_url)
            st.write("✅ Repository cloned successfully")

            # ── Step 2: Extract metadata ───────────────────────────
            st.write("📊 Extracting commit metadata...")
            df = extract_commit_metadata(repo, max_commits=max_commits)
            tags = get_tags(repo)
            branches = get_branches(repo)
            st.write(f"✅ Extracted **{len(df)}** commits, **{len(tags)}** tags, **{len(branches)}** branches")

            # ── Step 3: Classify commits ───────────────────────────
            st.write("🏷️ Classifying commits...")
            classified_df = classify_commits(df)
            type_counts = commit_type_counts(classified_df)
            st.write("✅ Commits classified")

            # ── Step 4: Compute statistics ─────────────────────────
            st.write("📈 Computing statistics...")
            stats = compute_commit_statistics(df)
            monthly = commits_per_month(df)
            contributors = contributor_analysis(df)
            st.write("✅ Statistics computed")

            # ── Step 5: Detect phases & milestones ─────────────────
            st.write("🔍 Detecting development phases & milestones...")
            phases = detect_development_phases(df, classified_df)
            milestones = detect_milestones(df, tags, classified_df)
            inactivity = detect_inactivity_periods(df)
            collab_intensity = collaboration_intensity_per_phase(df, phases)
            st.write(f"✅ Found **{len(phases)}** phases, **{len(milestones)}** milestones, **{len(inactivity)}** inactivity periods")

            # ── Step 6: Build summary & narrative ──────────────────
            st.write("🤖 Generating AI narrative...")
            summary_text = build_structured_summary(
                stats, contributors, phases, milestones, type_counts,
                branches=branches,
                inactivity_periods=inactivity,
                collab_intensity=collab_intensity,
            )
            narrative = generate_narrative(
                summary_text,
                model=hf_model,
                hf_token=hf_token if hf_token else None,
            )
            st.write("✅ Narrative generated")

            status.update(label="✅ Analysis complete!", state="complete")

        # ── Display Results ────────────────────────────────────────

        # ── Key Metrics ────────────────────────────────────────────
        st.markdown("## 📊 Key Metrics")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Commits", f"{stats['total_commits']:,}")
        with col2:
            st.metric("Contributors", f"{stats['total_authors']:,}")
        with col3:
            st.metric("Lines Added", f"{stats['total_lines_added']:,}")
        with col4:
            st.metric("Lines Deleted", f"{stats['total_lines_deleted']:,}")
        with col5:
            st.metric("Merge Commits", f"{stats['total_merges']:,}")

        st.markdown("---")

        # ── AI Narrative ───────────────────────────────────────────
        st.markdown("## 📖 Project Narrative")
        st.markdown(
            f'<div style="background:#1e1e2e; padding:20px; border-radius:12px; '
            f'line-height:1.8; color:#e2e8f0;">{narrative}</div>',
            unsafe_allow_html=True,
        )

        st.markdown("---")

        # ── Development Phases ─────────────────────────────────────
        st.markdown("## 🔄 Development Phases")
        if phases:
            for p in phases:
                start = p["start_date"].strftime("%b %Y")
                end = p["end_date"].strftime("%b %Y")
                st.markdown(
                    f'<span class="phase-badge">Phase {p["phase_number"]}</span> '
                    f'**{p["phase"]}** &nbsp; ({start} – {end}) &nbsp; '
                    f'*{p["commit_count"]} commits*',
                    unsafe_allow_html=True,
                )
        else:
            st.info("Not enough data to detect distinct phases.")

        st.markdown("---")

        # ── Timeline (Milestones) ──────────────────────────────────
        st.markdown("## 🏆 Timeline — Key Milestones")
        if milestones:
            for m in milestones[:20]:
                date_str = m["date"].strftime("%b %d, %Y")
                st.markdown(
                    f'<div class="milestone-card">'
                    f'<span class="milestone-date">{date_str}</span><br>'
                    f'<span class="milestone-desc">{m["description"]}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("No milestones detected.")

        st.markdown("---")

        # ── Contributor Insights ───────────────────────────────────
        st.markdown("## 👥 Contributor Insights")
        col_left, col_right = st.columns([1, 2])
        with col_left:
            st.dataframe(
                contributors.head(15)[["author", "commits", "lines_added", "lines_deleted"]],
                use_container_width=True,
                hide_index=True,
            )
        with col_right:
            fig_contrib = plot_contributor_commits(contributors)
            st.pyplot(fig_contrib)

        # ── Collaboration Intensity Per Phase ──────────────────────
        if collab_intensity:
            st.markdown("### 🤝 Collaboration Intensity Per Phase")
            import pandas as _pd
            collab_df = _pd.DataFrame(collab_intensity)
            st.dataframe(
                collab_df[["phase_number", "phase", "active_contributors",
                           "top_contributor", "top_contributor_commits"]],
                use_container_width=True,
                hide_index=True,
            )

        st.markdown("---")

        # ── Inactivity Periods ─────────────────────────────────────
        if inactivity:
            st.markdown("## 💤 Periods of Inactivity")
            for gap in inactivity[:5]:
                start_str = gap["start"].strftime("%b %d, %Y")
                end_str = gap["end"].strftime("%b %d, %Y")
                st.markdown(
                    f'<div class="milestone-card">'
                    f'<span class="milestone-date">{start_str} → {end_str}</span><br>'
                    f'<span class="milestone-desc">{gap["duration_days"]} days of inactivity</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            st.markdown("---")

        # ── Branch Structure ───────────────────────────────────────
        if branches:
            st.markdown("## 🌿 Branch Structure")
            st.write(f"**{len(branches)}** branches detected")
            import pandas as _pd2
            branch_df = _pd2.DataFrame(branches)
            if not branch_df.empty:
                st.dataframe(
                    branch_df[["name", "latest_commit"]].head(20),
                    use_container_width=True,
                    hide_index=True,
                )
            st.markdown("---")

        # ── Visualisations ─────────────────────────────────────────
        st.markdown("## 📈 Visualisations")

        tab1, tab2, tab3 = st.tabs([
            "Commit Activity Over Time",
            "Commit Type Distribution",
            "Code Churn",
        ])

        with tab1:
            fig_monthly = plot_commits_per_month(monthly)
            st.pyplot(fig_monthly)

        with tab2:
            fig_types = plot_commit_types(type_counts)
            st.pyplot(fig_types)

        with tab3:
            fig_lines = plot_lines_over_time(df)
            st.pyplot(fig_lines)

        st.markdown("---")

        # ── Raw structured summary (collapsible) ──────────────────
        with st.expander("📋 Raw Structured Summary"):
            st.code(summary_text, language="text")

    except Exception as e:
        st.error(f"❌ An error occurred: {e}")
        import traceback
        st.code(traceback.format_exc())

    finally:
        if repo is not None:
            cleanup_repo(repo)

elif analyze_btn and not repo_url:
    st.warning("⚠️ Please enter a repository URL in the sidebar.")
else:
    # ── Landing page ───────────────────────────────────────────────
    st.markdown("---")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown("### 🔍 Analyse")
        st.markdown("Deep-dive into any public Git repository's commit history.")
    with col_b:
        st.markdown("### 🤖 AI Narrative")
        st.markdown("Get an AI-generated chronological story of your project's evolution.")
    with col_c:
        st.markdown("### 📊 Visualise")
        st.markdown("Interactive charts for commit activity, contributors, and code churn.")

    st.markdown("---")
    st.info("👈 Enter a public GitHub repository URL in the sidebar and click **Analyze Repository** to get started!")
