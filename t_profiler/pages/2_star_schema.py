"""
T_PROFILER — Star Schema / Model View
=======================================
Displays domain-to-table mapping, star schema overview,
and relationship diagram data.
"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from backend.session_manager import get_session

st.set_page_config(page_title="Star Schema", page_icon=":star:", layout="wide")
st.header("Star Schema / Model View")


def _query(sql: str) -> pd.DataFrame:
    session = get_session()
    return session.sql(sql).to_pandas()


# ---------------------------------------------------------------------------
# Domain -> Target Table Mapping
# ---------------------------------------------------------------------------
st.subheader("Domain to Target Table Mapping")
try:
    domain_df = _query(
        "SELECT * FROM DATA_OBSERVABILITY.DATA_PROFILING.DOMAIN_TABLE_MAPPING ORDER BY DOMAIN, TARGET_TABLE"
    )
    if not domain_df.empty:
        st.dataframe(domain_df, use_container_width=True, hide_index=True)

        # Summary by domain
        if "DOMAIN" in domain_df.columns:
            st.subheader("Tables per Domain")
            summary = domain_df.groupby("DOMAIN").size().reset_index(name="TABLE_COUNT")
            st.bar_chart(summary.set_index("DOMAIN"))
    else:
        st.info("No domain mapping data. Run the INITIAL_MODEL stage first.")
except Exception as exc:
    st.warning(f"Could not load domain mapping: {exc}")

# ---------------------------------------------------------------------------
# Star Schema Overview
# ---------------------------------------------------------------------------
st.subheader("Star Schema Design")
try:
    star_df = _query(
        "SELECT * FROM DATA_OBSERVABILITY.DATA_PROFILING.STAR_SCHEMA_INITIAL ORDER BY DOMAIN, TABLE_TYPE, TABLE_NAME"
    )
    if not star_df.empty:
        # Filter by domain
        domains = ["All"] + sorted(star_df["DOMAIN"].unique().tolist()) if "DOMAIN" in star_df.columns else ["All"]
        sel_domain = st.selectbox("Filter by domain", domains)
        if sel_domain != "All":
            star_df = star_df[star_df["DOMAIN"] == sel_domain]
        st.dataframe(star_df, use_container_width=True, hide_index=True)
    else:
        st.info("No star schema data. Run the INITIAL_MODEL stage first.")
except Exception as exc:
    st.warning(f"Could not load star schema: {exc}")

# ---------------------------------------------------------------------------
# Relationships
# ---------------------------------------------------------------------------
st.subheader("Recommended Relationships (PK/FK)")
try:
    ref_df = _query(
        "SELECT * FROM DATA_OBSERVABILITY.DATA_PROFILING.PROFILING_RECOMMENDED_REFERENCES ORDER BY 1"
    )
    if not ref_df.empty:
        st.dataframe(ref_df, use_container_width=True, hide_index=True)
    else:
        st.info("No relationship data. Run the RI_CHECK stage first.")
except Exception as exc:
    st.warning(f"Could not load relationships: {exc}")
