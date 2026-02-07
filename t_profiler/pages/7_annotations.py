"""
T_PROFILER — User Annotations
===============================
Editable grid for USER_INPUT_SOURCE — per-table user notes
that feed into LLM prompts.
"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from backend.session_manager import get_session

st.set_page_config(page_title="User Annotations", page_icon=":memo:", layout="wide")
st.header("User Annotations")


def _query(sql: str) -> pd.DataFrame:
    session = get_session()
    return session.sql(sql).to_pandas()


# ---------------------------------------------------------------------------
# Load current annotations
# ---------------------------------------------------------------------------
try:
    ann_df = _query("SELECT * FROM DATA_OBSERVABILITY.DATA_PROFILING.USER_INPUT_SOURCE ORDER BY TABLE_NAME")
except Exception:
    ann_df = pd.DataFrame()

if ann_df.empty:
    st.info("No USER_INPUT_SOURCE data. Run the INITIAL_VIEWS stage first to seed the table.")
    st.stop()

# ---------------------------------------------------------------------------
# Editable data editor
# ---------------------------------------------------------------------------
st.subheader("Edit Table Annotations")
st.caption("Modify the notes below and click **Save Changes** to write back to Snowflake.")

edited_df = st.data_editor(
    ann_df,
    use_container_width=True,
    hide_index=True,
    num_rows="fixed",
)

# ---------------------------------------------------------------------------
# Save changes back to Snowflake
# ---------------------------------------------------------------------------
if st.button("Save Changes", type="primary"):
    try:
        session = get_session()
        # Compare original vs edited to find changed rows
        changed = edited_df.compare(ann_df) if ann_df.shape == edited_df.shape else None

        if changed is not None and changed.empty:
            st.success("No changes detected.")
        else:
            # Write full dataframe back via MERGE pattern
            # Create a temp table, then MERGE into USER_INPUT_SOURCE
            snowpark_df = session.create_dataframe(edited_df)
            snowpark_df.write.mode("overwrite").save_as_table(
                "DATA_OBSERVABILITY.DATA_PROFILING.USER_INPUT_SOURCE"
            )
            st.success("Changes saved successfully.")
            st.rerun()
    except Exception as exc:
        st.error(f"Failed to save: {exc}")
