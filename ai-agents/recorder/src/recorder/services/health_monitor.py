"""Meeting Health Monitor.

Runs as a background coroutine on the orchestrator.
Checks health conditions every 5 minutes.
Emits HealthAlert to chat UI sidebar only — never spoken, non-intrusive.

Conditions monitored:
  1. No decisions captured in 15+ minutes
  2. Agenda scope has expanded significantly
  3. Open questions from prior meeting not addressed
  4. Topic tabled with no owner assigned
  5. 2+ agents flagged the same risk independently
"""

# Implementation: Phase 4
# Skeleton only.

import asyncio
import structlog

logger = structlog.get_logger()

HEALTH_CHECK_INTERVAL_SECS = 300  # 5 minutes


async def run_health_monitor(session_id: str) -> None:
    """Background coroutine monitoring meeting health. Emits alerts to UI sidebar.
    Phase 4 implementation.
    """
    while True:
        await asyncio.sleep(HEALTH_CHECK_INTERVAL_SECS)
        # Phase 4: check conditions and emit HealthAlert via WebSocket
