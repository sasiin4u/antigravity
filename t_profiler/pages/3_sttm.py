"""
T_PROFILER — Source-to-Target Mapping (STTM)
=============================================
Column-level mapping from source tables to target tables.
"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from backend.session_manager import get_session

st.set_page_config(page_title="STTM", page_icon=":left_right_arrow:", layout="wide")
st.header("Source-to-Target Mapping")


def _query(sql: str) -> pd.DataFrame:
    session = get_session()
    return session.sql(sql).to_pandas()


tab_initial, tab_model = st.tabs(["STTM Initial (FINAL Layer)", "Model Column STTM (MODEL Layer)"])

# ---------------------------------------------------------------------------
# STTM Initial
# ---------------------------------------------------------------------------
with tab_initial:
    st.subheader("STTM Initial — FINAL Layer")
    try:
        sttm_df = _query("SELECT * FROM DATA_OBSERVABILITY.DATA_PROFILING.STTM_INITIAL ORDER BY TARGET_TABLE, TARGET_COLUMN")
        if not sttm_df.empty:
            # Target table filter
            targets = ["All"] + sorted(sttm_df["TARGET_TABLE"].unique().tolist()) if "TARGET_TABLE" in sttm_df.columns else ["All"]
            sel = st.selectbox("Filter by target table", targets, key="sttm_init_target")
            if sel != "All":
                sttm_df = sttm_df[sttm_df["TARGET_TABLE"] == sel]
            st.dataframe(sttm_df, use_container_width=True, hide_index=True)
        else:
            st.info("No STTM data. Run the STTM_INITIAL stage first.")
    except Exception as exc:
        st.warning(f"Could not load STTM Initial: {exc}")

# ---------------------------------------------------------------------------
# Model Column STTM
# ---------------------------------------------------------------------------
with tab_model:
    st.subheader("Model Column STTM — MODEL Layer")
    try:
        model_df = _query("SELECT * FROM DATA_OBSERVABILITY.DATA_PROFILING.FINAL_MODEL_COLUMN_STTM ORDER BY TARGET_TABLE, TARGET_COLUMN")
        if not model_df.empty:
            targets = ["All"] + sorted(model_df["TARGET_TABLE"].unique().tolist()) if "TARGET_TABLE" in model_df.columns else ["All"]
            sel = st.selectbox("Filter by target table", targets, key="model_sttm_target")
            if sel != "All":
                model_df = model_df[model_df["TARGET_TABLE"] == sel]
            st.dataframe(model_df, use_container_width=True, hide_index=True)
        else:
            st.info("No Model STTM data. Run the FINAL_MODEL_COLUMN_STTM stage first.")
    except Exception as exc:
        st.warning(f"Could not load Model STTM: {exc}")

# ---------------------------------------------------------------------------
# Lineage summary
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Source-to-Target Lineage Summary")
try:
    lineage_df = _query("""
        SELECT TARGET_TABLE, COUNT(DISTINCT SOURCE_TABLE) AS SOURCE_TABLES, COUNT(*) AS COLUMN_MAPPINGS
        FROM DATA_OBSERVABILITY.DATA_PROFILING.STTM_INITIAL
        GROUP BY TARGET_TABLE
        ORDER BY COLUMN_MAPPINGS DESC
    """)
    if not lineage_df.empty:
        st.dataframe(lineage_df, use_container_width=True, hide_index=True)
except Exception as exc:
    st.warning(f"Could not load lineage summary: {exc}")
