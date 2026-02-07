"""
T_PROFILER — Generated DDL Viewer
===================================
Browse and inspect generated DDL for FINAL and MODEL layers.
"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from backend.session_manager import get_session

st.set_page_config(page_title="DDL Viewer", page_icon=":page_facing_up:", layout="wide")
st.header("Generated DDL")


def _query(sql: str) -> pd.DataFrame:
    session = get_session()
    return session.sql(sql).to_pandas()


tab_final, tab_model, tab_exec = st.tabs(["FINAL Layer DDL", "MODEL Layer DDL", "Execution Logs"])

# ---------------------------------------------------------------------------
# FINAL Layer DDL
# ---------------------------------------------------------------------------
with tab_final:
    st.subheader("FINAL Layer DDL")
    try:
        ddl_df = _query("SELECT * FROM DATA_OBSERVABILITY.DATA_PROFILING.FINAL_LAYER_DDL ORDER BY TOKEN_ORDER, OBJECT_NAME")
        if not ddl_df.empty:
            # Object filter
            ddl_type_col = "DDL_TYPE" if "DDL_TYPE" in ddl_df.columns else "OBJECT_TYPE" if "OBJECT_TYPE" in ddl_df.columns else None
            if ddl_type_col:
                types = ["All"] + sorted(ddl_df[ddl_type_col].unique().tolist())
                sel_type = st.selectbox("Filter by type", types, key="final_ddl_type")
                if sel_type != "All":
                    ddl_df = ddl_df[ddl_df[ddl_type_col] == sel_type]

            obj_col = "OBJECT_NAME" if "OBJECT_NAME" in ddl_df.columns else None
            if obj_col:
                objects = sorted(ddl_df[obj_col].unique().tolist())
                sel_obj = st.selectbox("Select object", objects, key="final_ddl_obj")
                row = ddl_df[ddl_df[obj_col] == sel_obj].iloc[0]

                ddl_col = "DDL" if "DDL" in ddl_df.columns else "DDL_TEXT" if "DDL_TEXT" in ddl_df.columns else None
                if ddl_col:
                    st.code(row[ddl_col], language="sql")
                else:
                    st.dataframe(ddl_df[ddl_df[obj_col] == sel_obj], use_container_width=True, hide_index=True)
            else:
                st.dataframe(ddl_df, use_container_width=True, hide_index=True)
        else:
            st.info("No FINAL DDL data. Run the FINAL_DDL_GENERATE stage first.")
    except Exception as exc:
        st.warning(f"Could not load FINAL DDL: {exc}")

# ---------------------------------------------------------------------------
# MODEL Layer DDL
# ---------------------------------------------------------------------------
with tab_model:
    st.subheader("MODEL Layer DDL")
    try:
        mddl_df = _query("SELECT * FROM DATA_OBSERVABILITY.DATA_PROFILING.MODEL_DDL ORDER BY TOKEN_ORDER, OBJECT_NAME")
        if not mddl_df.empty:
            ddl_type_col = "DDL_TYPE" if "DDL_TYPE" in mddl_df.columns else "OBJECT_TYPE" if "OBJECT_TYPE" in mddl_df.columns else None
            if ddl_type_col:
                types = ["All"] + sorted(mddl_df[ddl_type_col].unique().tolist())
                sel_type = st.selectbox("Filter by type", types, key="model_ddl_type")
                if sel_type != "All":
                    mddl_df = mddl_df[mddl_df[ddl_type_col] == sel_type]

            obj_col = "OBJECT_NAME" if "OBJECT_NAME" in mddl_df.columns else None
            if obj_col:
                objects = sorted(mddl_df[obj_col].unique().tolist())
                sel_obj = st.selectbox("Select object", objects, key="model_ddl_obj")
                row = mddl_df[mddl_df[obj_col] == sel_obj].iloc[0]

                ddl_col = "DDL" if "DDL" in mddl_df.columns else "DDL_TEXT" if "DDL_TEXT" in mddl_df.columns else None
                if ddl_col:
                    st.code(row[ddl_col], language="sql")
                else:
                    st.dataframe(mddl_df[mddl_df[obj_col] == sel_obj], use_container_width=True, hide_index=True)
            else:
                st.dataframe(mddl_df, use_container_width=True, hide_index=True)
        else:
            st.info("No MODEL DDL data. Run the MODEL_DDL_GENERATE stage first.")
    except Exception as exc:
        st.warning(f"Could not load MODEL DDL: {exc}")

# ---------------------------------------------------------------------------
# Execution Logs
# ---------------------------------------------------------------------------
with tab_exec:
    st.subheader("DDL Execution Logs")
    log_layer = st.radio("Layer", ["FINAL", "MODEL"], horizontal=True, key="exec_log_layer")
    table = "FINAL_LAYER_DDL_EXEC_LOG" if log_layer == "FINAL" else "MODEL_DDL_EXEC_LOG"
    try:
        log_df = _query(f"SELECT * FROM DATA_OBSERVABILITY.DATA_PROFILING.{table} ORDER BY 1 DESC")
        if not log_df.empty:
            st.dataframe(log_df, use_container_width=True, hide_index=True)
        else:
            st.info(f"No {log_layer} execution logs yet.")
    except Exception as exc:
        st.warning(f"Could not load execution logs: {exc}")
