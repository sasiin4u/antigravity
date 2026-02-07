"""
T_PROFILER — Data Profiling Results
====================================
Displays column-level and table-level profiling output.
"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from backend.session_manager import get_session

st.set_page_config(page_title="Data Profiling", page_icon=":bar_chart:", layout="wide")
st.header("Data Profiling Results")


def _query(sql: str) -> pd.DataFrame:
    session = get_session()
    return session.sql(sql).to_pandas()


# ---------------------------------------------------------------------------
# Table selector
# ---------------------------------------------------------------------------
try:
    tables_df = _query(
        "SELECT DISTINCT TABLE_NAME FROM DATA_OBSERVABILITY.DATA_PROFILING.PROFILING_TABLE_LEVEL_FINAL ORDER BY 1"
    )
    table_list = tables_df["TABLE_NAME"].tolist()
except Exception:
    table_list = []

if not table_list:
    st.info("No profiling data found. Run the DATA_PROFILING stage first.")
    st.stop()

selected_table = st.selectbox("Select a table", table_list)

# ---------------------------------------------------------------------------
# Column-level stats
# ---------------------------------------------------------------------------
st.subheader("Column-Level Statistics")
try:
    col_df = _query(f"""
        SELECT *
        FROM DATA_OBSERVABILITY.DATA_PROFILING.PROFILING_COLUMN_LIST_FINAL
        WHERE TABLE_NAME = '{selected_table}'
        ORDER BY ORDINAL_POSITION
    """)
    st.dataframe(col_df, use_container_width=True, hide_index=True)
except Exception as exc:
    st.warning(f"Could not load column stats: {exc}")

# ---------------------------------------------------------------------------
# Table-level summary
# ---------------------------------------------------------------------------
st.subheader("Table-Level Summary")
try:
    tbl_df = _query(f"""
        SELECT *
        FROM DATA_OBSERVABILITY.DATA_PROFILING.PROFILING_TABLE_LEVEL_FINAL
        WHERE TABLE_NAME = '{selected_table}'
    """)
    if not tbl_df.empty:
        for col in tbl_df.columns:
            st.text(f"{col}: {tbl_df.iloc[0][col]}")
except Exception as exc:
    st.warning(f"Could not load table summary: {exc}")

# ---------------------------------------------------------------------------
# Type distribution
# ---------------------------------------------------------------------------
st.subheader("Data Type Distribution")
try:
    type_df = _query(f"""
        SELECT DATA_TYPE, COUNT(*) AS COL_COUNT
        FROM DATA_OBSERVABILITY.DATA_PROFILING.PROFILING_COLUMN_LIST_FINAL
        WHERE TABLE_NAME = '{selected_table}'
        GROUP BY DATA_TYPE
        ORDER BY COL_COUNT DESC
    """)
    if not type_df.empty:
        st.bar_chart(type_df.set_index("DATA_TYPE"))
except Exception as exc:
    st.warning(f"Could not load type distribution: {exc}")

# ---------------------------------------------------------------------------
# Domain classification
# ---------------------------------------------------------------------------
st.subheader("Domain Classification")
try:
    domain_df = _query(f"""
        SELECT COLUMN_NAME, DOMAIN, DOMAIN_CONFIDENCE
        FROM DATA_OBSERVABILITY.DATA_PROFILING.PROFILING_COLUMN_LIST_FINAL
        WHERE TABLE_NAME = '{selected_table}'
          AND DOMAIN IS NOT NULL
        ORDER BY DOMAIN
    """)
    if not domain_df.empty:
        st.dataframe(domain_df, use_container_width=True, hide_index=True)
    else:
        st.info("No domain classifications available for this table.")
except Exception as exc:
    st.warning(f"Could not load domain data: {exc}")
