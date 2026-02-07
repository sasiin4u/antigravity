"""
T_PROFILER — Execution Logs
=============================
Live log viewer, LLM interaction timeline, and summarized logs.
"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from backend.session_manager import get_session

st.set_page_config(page_title="Execution Logs", page_icon=":scroll:", layout="wide")
st.header("Execution Logs")


def _query(sql: str) -> pd.DataFrame:
    session = get_session()
    return session.sql(sql).to_pandas()


tab_live, tab_llm, tab_summary = st.tabs(["Live Logs", "LLM Interactions", "Summarized Logs"])

# ---------------------------------------------------------------------------
# Live Logs
# ---------------------------------------------------------------------------
with tab_live:
    st.subheader("ZZ_MODEL_EXEC_LOG")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        cell_filter = st.text_input("Filter by cell name", "", key="log_cell")
    with col_f2:
        limit = st.number_input("Max rows", min_value=50, max_value=5000, value=500, step=50)

    try:
        where = ""
        if cell_filter:
            where = f"WHERE CELL_NAME ILIKE '%{cell_filter}%'"
        log_df = _query(f"""
            SELECT *
            FROM DATA_OBSERVABILITY.DATA_PROFILING.ZZ_MODEL_EXEC_LOG
            {where}
            ORDER BY LOG_TIMESTAMP DESC
            LIMIT {limit}
        """)
        if not log_df.empty:
            st.dataframe(log_df, use_container_width=True, hide_index=True)
        else:
            st.info("No execution logs found.")
    except Exception as exc:
        st.warning(f"Could not load logs: {exc}")

    if st.button("Refresh", key="refresh_live"):
        st.rerun()

# ---------------------------------------------------------------------------
# LLM Interaction Timeline
# ---------------------------------------------------------------------------
with tab_llm:
    st.subheader("LLM Interaction Log")

    col_a, col_p = st.columns(2)
    with col_a:
        actor_filter = st.selectbox(
            "Filter by actor",
            ["All", "Modeler", "Validator", "Profiler", "MermaidFixer", "Reviewer"],
            key="llm_actor",
        )
    with col_p:
        provider_filter = st.selectbox(
            "Filter by provider",
            ["All", "OPENAI", "CORTEX"],
            key="llm_provider",
        )

    try:
        conditions = []
        if actor_filter != "All":
            conditions.append(f"ACTOR = '{actor_filter}'")
        if provider_filter != "All":
            conditions.append(f"LLM_PROVIDER = '{provider_filter}'")
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        llm_df = _query(f"""
            SELECT *
            FROM DATA_OBSERVABILITY.DATA_PROFILING.ZZ_MODEL_EXEC_LLM_LOG_V
            {where}
            ORDER BY LOG_TIMESTAMP DESC
            LIMIT 500
        """)
        if not llm_df.empty:
            st.dataframe(llm_df, use_container_width=True, hide_index=True)

            # Actor-based grouping summary
            if "ACTOR" in llm_df.columns:
                st.subheader("Calls by Actor")
                actor_summary = llm_df.groupby("ACTOR").size().reset_index(name="CALL_COUNT")
                st.bar_chart(actor_summary.set_index("ACTOR"))
        else:
            st.info("No LLM interaction logs found.")
    except Exception as exc:
        st.warning(f"Could not load LLM logs: {exc}")

# ---------------------------------------------------------------------------
# Summarized Logs
# ---------------------------------------------------------------------------
with tab_summary:
    st.subheader("Summarized Execution Log")
    try:
        summary_df = _query("""
            SELECT *
            FROM DATA_OBSERVABILITY.DATA_PROFILING.ZZ_MODEL_EXEC_LOG_SUMMARY
            ORDER BY 1 DESC
        """)
        if not summary_df.empty:
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
        else:
            st.info("No summary data. The log summarization task may not have run yet.")
    except Exception as exc:
        st.warning(f"Could not load summary: {exc}")
