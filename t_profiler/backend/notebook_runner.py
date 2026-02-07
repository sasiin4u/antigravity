"""
Interface for executing T_PROFILER notebook stages.

Each "stage" maps to one or more cells in T_PROFILER_BACKUP.ipynb.
This module lets the Streamlit app trigger individual stages and
track their execution status.
"""

from __future__ import annotations

import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class StageStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class Stage:
    cell_number: int
    name: str
    cell_type: str  # "python" or "sql"
    description: str
    status: StageStatus = StageStatus.PENDING
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    error_message: Optional[str] = None


# ---------------------------------------------------------------------------
# Pipeline definition (mirrors the 33 cells in the spec)
# ---------------------------------------------------------------------------
PIPELINE_STAGES: List[Stage] = [
    Stage(0, "START", "python", "Capture run start time"),
    Stage(1, "OPTIONAL_DROP", "sql", "Drop databases/schemas for clean slate"),
    Stage(2, "CREATE_SCHEMAS", "sql", "Create schemas, network rules, external access"),
    Stage(3, "ROLE", "sql", "Set role to ACCOUNTADMIN"),
    Stage(4, "LOGGING", "python", "Create ZZ_MODEL_EXEC_LOG and log_exec()"),
    Stage(5, "FINAL_LOGS_DISPLAY", "sql", "Create log views, summary tables, stored proc"),
    Stage(6, "BUILD_CALENDAR_DIM", "sql", "Create DIM_DATE_GREGORIAN stored proc"),
    Stage(7, "CALL_CALENDAR_DIM", "sql", "Call calendar dim builder"),
    Stage(8, "BASE_PACKAGES", "python", "Import core packages"),
    Stage(9, "DATA_PROFILING", "python", "Profile columns — Cortex + OpenAI"),
    Stage(10, "INITIAL_VIEWS", "python", "Create *_FINAL views, seed USER_INPUT_SOURCE"),
    Stage(11, "RI_CHECK", "python", "Relationship inference via Cortex"),
    Stage(12, "TABLE_LEVEL_SUMMARY", "python", "Per-table descriptions — Cortex + OpenAI"),
    Stage(13, "PROFILING_VIEWS", "python", "Create PROFILING_SOURCE_TABLE view"),
    Stage(14, "PROFILING_TABLE_LEVEL_DETAILS", "python", "Consolidated per-table detail"),
    Stage(15, "INITIAL_MODEL", "python", "5-stage star schema refinement"),
    Stage(16, "STTM_INITIAL", "python", "Source-to-target column mapping"),
    Stage(17, "PROFILING_TABLE_LAYER_MAPPING", "python", "TABLE_LAYER_MAPPING build"),
    Stage(18, "MERGE_OBJECTS_MAPPING", "python", "Domain assignment + DIM merges"),
    Stage(19, "MERGE_OBJECT_SUMMARY", "python", "Column-merge recommendations"),
    Stage(20, "MERGE_METADATA_GENERATE", "python", "FINAL layer merge metadata"),
    Stage(21, "FINAL_LAYER_METADATA_BASE", "python", "Build FINAL_LAYER_METADATA"),
    Stage(22, "FINAL_SELECT_GENERATE", "python", "Generate SELECT statements"),
    Stage(23, "FINAL_SELECT_OPTIMIZE", "python", "Schema-aware syntax-fix loop"),
    Stage(24, "FINAL_DDL_GENERATE", "python", "Generate complete DDL package"),
    Stage(25, "FINAL_LAYER_DDL_EXEC", "python", "Execute generated DDL"),
    Stage(26, "FINAL_MODEL_TABLE_MAPPING", "python", "MODEL table mapping"),
    Stage(27, "MODEL_STTM_INPUT", "python", "Build MODEL_STTM_INPUT"),
    Stage(28, "FINAL_MODEL_COLUMN_STTM", "python", "Column-level STTM for MODEL"),
    Stage(29, "MODEL_DDL_GENERATE", "python", "Generate MODEL DDL"),
    Stage(30, "MODEL_DDL_EXEC", "python", "Execute MODEL DDL"),
    Stage(31, "MERMAIDCHART", "python", "Generate Mermaid ER diagram"),
    Stage(32, "END", "python", "Capture end time, compute runtime"),
]


def get_pipeline() -> List[Stage]:
    """Return a fresh copy of the pipeline stages."""
    import copy
    return copy.deepcopy(PIPELINE_STAGES)


def _run_sql_stage(session, stage: Stage, sql: str) -> None:
    """Execute a SQL stage."""
    session.sql(sql).collect()


def run_stage(session, stage: Stage, cell_executor: Optional[Callable] = None) -> None:
    """Execute a single pipeline stage and update its status.

    Parameters
    ----------
    session : snowflake.snowpark.Session
    stage : Stage
    cell_executor : callable, optional
        A function(session, cell_number) that runs the actual cell logic.
        If not provided, stages are marked as DONE without execution
        (useful for UI development before the notebook is wired up).
    """
    stage.status = StageStatus.RUNNING
    stage.started_at = time.time()
    try:
        if cell_executor is not None:
            cell_executor(session, stage.cell_number)
        stage.status = StageStatus.DONE
    except Exception as exc:
        stage.status = StageStatus.ERROR
        stage.error_message = str(exc)
        logger.error("Stage %s failed: %s", stage.name, exc)
    finally:
        stage.finished_at = time.time()


def run_pipeline(
    session,
    stages: List[Stage],
    cell_executor: Optional[Callable] = None,
    skip_cells: Optional[List[int]] = None,
    progress_callback: Optional[Callable] = None,
) -> List[Stage]:
    """Run the full pipeline sequentially.

    Parameters
    ----------
    session : Snowpark session
    stages : list of Stage
    cell_executor : callable(session, cell_number), optional
    skip_cells : list of cell numbers to skip
    progress_callback : callable(stage_index, stage), optional
        Called after each stage completes — useful for updating Streamlit UI.
    """
    skip = set(skip_cells or [])
    for i, stage in enumerate(stages):
        if stage.cell_number in skip:
            stage.status = StageStatus.SKIPPED
            continue
        run_stage(session, stage, cell_executor)
        if progress_callback:
            progress_callback(i, stage)
        if stage.status == StageStatus.ERROR:
            logger.warning("Pipeline halted at stage %s due to error.", stage.name)
            break
    return stages
