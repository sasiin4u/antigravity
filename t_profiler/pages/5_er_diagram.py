"""
T_PROFILER — ER Diagram (Mermaid)
==================================
Renders the generated Mermaid ER diagram.
"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from backend.session_manager import get_session

st.set_page_config(page_title="ER Diagram", page_icon=":chart_with_upwards_trend:", layout="wide")
st.header("Entity-Relationship Diagram")


def _query(sql: str) -> pd.DataFrame:
    session = get_session()
    return session.sql(sql).to_pandas()


try:
    mermaid_df = _query("SELECT * FROM DATA_OBSERVABILITY.DATA_PROFILING.MERMAIDCHART LIMIT 1")
    if not mermaid_df.empty:
        # Extract the mermaid code from the first available text column
        mermaid_code = None
        for col in mermaid_df.columns:
            val = str(mermaid_df.iloc[0][col])
            if "erDiagram" in val or "graph" in val or "classDiagram" in val:
                mermaid_code = val
                break

        if mermaid_code is None:
            # Fall back to the first large text column
            for col in mermaid_df.columns:
                val = str(mermaid_df.iloc[0][col])
                if len(val) > 50:
                    mermaid_code = val
                    break

        if mermaid_code:
            # Render with st.markdown using mermaid code fence
            st.subheader("ER Diagram")
            st.markdown(f"```mermaid\n{mermaid_code}\n```")

            # Raw code viewer
            with st.expander("View raw Mermaid code"):
                st.code(mermaid_code, language="text")

            # Download button
            st.download_button(
                label="Download Mermaid code",
                data=mermaid_code,
                file_name="t_profiler_er_diagram.mmd",
                mime="text/plain",
            )
        else:
            st.warning("MERMAIDCHART table exists but no diagram code found.")
    else:
        st.info("No ER diagram data. Run the MERMAIDCHART stage first.")
except Exception as exc:
    st.warning(f"Could not load Mermaid diagram: {exc}")
