"""
Snowpark session management for T_PROFILER.

Inside a Snowflake Notebook / Streamlit-in-Snowflake:
    session = get_session()          # uses get_active_session()

Standalone / external Streamlit:
    session = get_session()          # builds a session from secrets.toml
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

_cached_session = None


def _active_session():
    """Try to obtain the session from a running Snowflake Notebook context."""
    try:
        from snowflake.snowpark.context import get_active_session
        return get_active_session()
    except Exception:
        return None


def _session_from_streamlit_secrets():
    """Build a Snowpark session from .streamlit/secrets.toml [snowflake]."""
    try:
        import streamlit as st
        from snowflake.snowpark import Session

        sf = st.secrets["snowflake"]
        params = {
            "account": sf["account"],
            "user": sf["user"],
            "password": sf["password"],
            "role": sf.get("role", "ACCOUNTADMIN"),
            "warehouse": sf.get("warehouse", "COMPUTE_WH"),
            "database": sf.get("database", "DATA_OBSERVABILITY"),
            "schema": sf.get("schema", "DATA_PROFILING"),
        }
        return Session.builder.configs(params).create()
    except Exception as exc:
        logger.debug("Cannot create session from Streamlit secrets: %s", exc)
        return None


def get_session() -> "snowflake.snowpark.Session":
    """Return a Snowpark session, caching it for the process lifetime.

    Resolution order:
      1. Already-cached session
      2. Active Snowflake Notebook / SiS session
      3. Session built from .streamlit/secrets.toml
    """
    global _cached_session
    if _cached_session is not None:
        return _cached_session

    session = _active_session()
    if session is not None:
        logger.info("Using active Snowflake session.")
        _cached_session = session
        return session

    session = _session_from_streamlit_secrets()
    if session is not None:
        logger.info("Created Snowpark session from Streamlit secrets.")
        _cached_session = session
        return session

    raise RuntimeError(
        "Cannot obtain a Snowpark session. Either:\n"
        "  1. Run inside a Snowflake Notebook / Streamlit-in-Snowflake, or\n"
        "  2. Configure [snowflake] in .streamlit/secrets.toml"
    )
