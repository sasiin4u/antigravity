"""
T_PROFILER — Streamlit Dashboard
=================================
Main entry point.  Run with:
    streamlit run t_profiler/streamlit_app.py

Provides:
  - Sidebar: configuration, schema selector, run controls
  - Main area: pipeline status dashboard with progress tracking
"""

import sys
import time
from pathlib import Path

import streamlit as st

# Ensure the project root is on sys.path so `backend.*` imports work.
_project_root = Path(__file__).resolve().parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from backend.session_manager import get_session
from backend.secrets_config import get_openai_key
from backend.notebook_runner import (
    get_pipeline,
    run_stage,
    run_pipeline,
    StageStatus,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="T_PROFILER Dashboard",
    page_icon=":snowflake:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------
if "pipeline" not in st.session_state:
    st.session_state.pipeline = get_pipeline()
if "run_started" not in st.session_state:
    st.session_state.run_started = False

# ---------------------------------------------------------------------------
# Sidebar — Configuration & Controls
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("T_PROFILER")
    st.caption("Automated Data Warehouse Modeler")
    st.divider()

    # -- Schema selector --
    st.subheader("Source Schemas")
    schema_input = st.text_area(
        "DB.SCHEMA list (one per line)",
        value="RAW.TPCH_SF1",
        help="Enter each DB.SCHEMA combo on its own line.",
    )
    db_schema_list = [s.strip() for s in schema_input.splitlines() if s.strip()]

    excluded_tables = st.text_input(
        "Excluded tables (comma-separated)",
        value="",
        help="Tables to skip during profiling.",
    )

    st.divider()

    # -- LLM settings (read-only) --
    st.subheader("LLM Configuration")
    st.text("Cortex: llama3.1-70b")
    st.text("OpenAI: gpt-5")
    st.text("Temperature: 1")

    st.divider()

    # -- Execution mode --
    st.subheader("Execution Mode")
    load_type = st.radio(
        "LOAD_TYPE",
        ["TRUNCATE_AND_LOAD", "STORED_PROCEDURE", "DYNAMIC"],
        index=0,
    )

    st.divider()

    # -- Run controls --
    st.subheader("Run Controls")

    stage_names = [f"{s.cell_number}: {s.name}" for s in st.session_state.pipeline]

    col_run, col_stop = st.columns(2)
    with col_run:
        if st.button("Run Full Pipeline", type="primary", use_container_width=True):
            st.session_state.run_started = True
            st.session_state.pipeline = get_pipeline()  # reset
    with col_stop:
        if st.button("Stop", use_container_width=True):
            st.session_state.run_started = False

    selected_stage = st.selectbox("Run single stage", stage_names)
    if st.button("Run Selected Stage", use_container_width=True):
        idx = stage_names.index(selected_stage)
        st.session_state.pipeline[idx].status = StageStatus.PENDING
        try:
            session = get_session()
            run_stage(session, st.session_state.pipeline[idx])
        except RuntimeError as exc:
            st.error(str(exc))

# ---------------------------------------------------------------------------
# Main area — Pipeline Status Dashboard
# ---------------------------------------------------------------------------
st.header("Pipeline Status")

# -- Metrics row --
pipeline = st.session_state.pipeline
done_count = sum(1 for s in pipeline if s.status == StageStatus.DONE)
error_count = sum(1 for s in pipeline if s.status == StageStatus.ERROR)
running_count = sum(1 for s in pipeline if s.status == StageStatus.RUNNING)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Stages", len(pipeline))
m2.metric("Completed", done_count)
m3.metric("Running", running_count)
m4.metric("Errors", error_count)

# -- Progress bar --
progress = done_count / len(pipeline) if pipeline else 0
st.progress(progress, text=f"{done_count}/{len(pipeline)} stages complete")

# -- Stage cards --
st.subheader("Stages")

STATUS_ICONS = {
    StageStatus.PENDING: ":hourglass_flowing_sand:",
    StageStatus.RUNNING: ":arrows_counterclockwise:",
    StageStatus.DONE: ":white_check_mark:",
    StageStatus.ERROR: ":x:",
    StageStatus.SKIPPED: ":fast_forward:",
}

# Display in a 4-column grid
cols = st.columns(4)
for i, stage in enumerate(pipeline):
    with cols[i % 4]:
        icon = STATUS_ICONS.get(stage.status, "")
        elapsed = ""
        if stage.started_at and stage.finished_at:
            elapsed = f" ({stage.finished_at - stage.started_at:.1f}s)"
        st.markdown(f"**{icon} {stage.cell_number}. {stage.name}**{elapsed}")
        if stage.error_message:
            st.error(stage.error_message, icon=":warning:")

# -- Runtime timer placeholder --
st.divider()
if st.session_state.run_started:
    st.info("Pipeline execution is managed by the notebook backend. "
            "Check the **Execution Logs** page for real-time progress.")

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.divider()
st.caption("T_PROFILER v1.0 — Automated Data Warehouse Modeler")
