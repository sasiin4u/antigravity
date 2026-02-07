"""
Centralized secrets management for T_PROFILER.

Supports three retrieval modes (tried in order):
  1. Snowflake Secret Object  — for Snowflake Notebooks / Streamlit-in-Snowflake
  2. Streamlit secrets.toml    — for standalone Streamlit deployments
  3. Environment variables      — fallback for local development / CI

Usage in notebook cells:
    from backend.secrets_config import get_openai_key
    OPENAI_API_KEY = get_openai_key(session)

Usage in Streamlit app:
    from backend.secrets_config import get_openai_key
    OPENAI_API_KEY = get_openai_key()
"""

from __future__ import annotations

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Snowflake Secret fully-qualified name
# ---------------------------------------------------------------------------
SF_SECRET_FQN = "DATA_OBSERVABILITY.DATA_PROFILING.OPENAI_API_KEY_SECRET"


def _from_snowflake_secret(session) -> Optional[str]:
    """Retrieve the key from a Snowflake Secret Object."""
    try:
        row = session.sql(
            f"SELECT SYSTEM$GET_SECRET_STRING('{SF_SECRET_FQN}')"
        ).collect()
        key = row[0][0] if row else None
        if key:
            logger.info("OpenAI key loaded from Snowflake Secret.")
        return key
    except Exception as exc:
        logger.debug("Snowflake Secret lookup failed: %s", exc)
        return None


def _from_streamlit_secrets() -> Optional[str]:
    """Retrieve the key from .streamlit/secrets.toml via st.secrets."""
    try:
        import streamlit as st
        key = st.secrets["openai"]["api_key"]
        if key and not key.startswith("<"):
            logger.info("OpenAI key loaded from Streamlit secrets.toml.")
            return key
        return None
    except Exception:
        return None


def _from_env() -> Optional[str]:
    """Retrieve the key from environment variables."""
    for var in ("OPENAI_API_KEY", "SF_OPENAI_API_KEY"):
        key = os.getenv(var)
        if key:
            logger.info("OpenAI key loaded from env var %s.", var)
            return key
    return None


def get_openai_key(session=None) -> str:
    """Return the OpenAI API key using the first available source.

    Parameters
    ----------
    session : snowflake.snowpark.Session, optional
        Active Snowpark session.  When running inside a Snowflake Notebook
        pass the session obtained from ``get_active_session()``.
        When running in standalone Streamlit, omit this parameter.

    Raises
    ------
    RuntimeError
        If no key can be found from any source.
    """
    key = None

    # 1. Snowflake Secret (preferred when a session is available)
    if session is not None:
        key = _from_snowflake_secret(session)

    # 2. Streamlit secrets.toml
    if key is None:
        key = _from_streamlit_secrets()

    # 3. Environment variables
    if key is None:
        key = _from_env()

    if key is None:
        raise RuntimeError(
            "OpenAI API key not found. Provide it via:\n"
            f"  1. Snowflake Secret: {SF_SECRET_FQN}\n"
            "  2. .streamlit/secrets.toml  [openai] api_key = ...\n"
            "  3. Environment variable OPENAI_API_KEY or SF_OPENAI_API_KEY"
        )
    return key


# ---------------------------------------------------------------------------
# SQL helper: ensure the Snowflake Secret Object exists
# ---------------------------------------------------------------------------
CREATE_SECRET_SQL = """\
CREATE SECRET IF NOT EXISTS {fqn}
  TYPE = GENERIC_STRING
  SECRET_STRING = '{{key}}';
""".format(fqn=SF_SECRET_FQN)


def ensure_snowflake_secret(session, api_key: str) -> None:
    """Create the Snowflake Secret Object if it does not already exist."""
    session.sql(
        f"""CREATE SECRET IF NOT EXISTS {SF_SECRET_FQN}
            TYPE = GENERIC_STRING
            SECRET_STRING = '{api_key}'"""
    ).collect()
    logger.info("Snowflake Secret %s ensured.", SF_SECRET_FQN)
