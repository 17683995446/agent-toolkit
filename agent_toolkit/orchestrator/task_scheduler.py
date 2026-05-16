"""Scheduler for tool chain orchestration."""

import asyncio
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from agent_toolkit.orchestrator.orchestration_models import ToolChain, ExecutionContext
from agent_toolkit.shared.structured_logging import LoggerMixin


class ScheduleType(str, Enum):
    """Types of scheduling."""
    IMMEDIATE = "immediate"
    DELAYED = "delayed"
    CRON = "cron"
    INTERVAL = "interval"


@dataclass
class Schedule:
    """Schedule for chain execution."""
    schedule_id: str
    chain_id: str
    schedule_type: ScheduleType
    chain: ToolChain
    initial_inputs: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    run_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_due(self) -> bool:
        """Check if the schedule is due."""
        if not self.enabled:
            return False
        if self.next_run is None:
            return True
        return datetime.utcnow() >= self.next_run


class Scheduler(LoggerMixin):
    """Scheduler for tool chain execution."""

    def __init__(self):
        self._schedules: Dict[str, Schedule] = {}
        self._running = False
        self._execution_engine = None
        self._scheduler_task: Optional[asyncio.Task] = None

    def set_execution_engine(self, engine: Any) -> None:
        """Set the orchestration engine."""
        self._execution_engine = engine

    def create_schedule(
        self,
        schedule_id: str,
        chain: ToolChain,
        initial_inputs: Optional[Dict[str, Any]] = None,
        schedule_type: ScheduleType = ScheduleType.IMMEDIATE,
        run_at: Optional[datetime] = None,
        interval_seconds: Optional[int] = None,
        cron_expression: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Schedule:
        """Create a new schedule."""
        schedule = Schedule(
            schedule_id=schedule_id,
            chain_id=chain.id,
            schedule_type=schedule_type,
            chain=chain,
            initial_inputs=initial_inputs or {},
            metadata=metadata or {}
        )

        if schedule_type == ScheduleType.IMMEDIATE:
            schedule.next_run = datetime.utcnow()
        elif schedule_type == ScheduleType.DELAYED and run_at:
            schedule.next_run = run_at
        elif schedule_type == ScheduleType.INTERVAL and interval_seconds:
            schedule.next_run = datetime.utcnow() + timedelta(seconds=interval_seconds)
        elif schedule_type == ScheduleType.CRON and cron_expression:
            schedule.next_run = self._parse_cron(cron_expression)

        self._schedules[schedule_id] = schedule

        self.logger.info(
            "schedule_created",
            schedule_id=schedule_id,
            chain_id=chain.id,
            schedule_type=schedule_type.value,
            next_run=schedule.next_run.isoformat() if schedule.next_run else None
        )

        return schedule

    def get_schedule(self, schedule_id: str) -> Optional[Schedule]:
        """Get a schedule by ID."""
        return self._schedules.get(schedule_id)

    def list_schedules(self) -> List[Schedule]:
        """List all schedules."""
        return list(self._schedules.values())

    def update_schedule(
        self,
        schedule_id: str,
        enabled: Optional[bool] = None,
        initial_inputs: Optional[Dict[str, Any]] = None
    ) -> Optional[Schedule]:
        """Update a schedule."""
        schedule = self._schedules.get(schedule_id)
        if not schedule:
            return None

        if enabled is not None:
            schedule.enabled = enabled
        if initial_inputs is not None:
            schedule.initial_inputs = initial_inputs

        self.logger.info("schedule_updated", schedule_id=schedule_id)
        return schedule

    def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a schedule."""
        if schedule_id in self._schedules:
            del self._schedules[schedule_id]
            self.logger.info("schedule_deleted", schedule_id=schedule_id)
            return True
        return False

    async def start(self) -> None:
        """Start the scheduler."""
        if self._running:
            self.logger.warning("scheduler_already_running")
            return

        self._running = True
        self._scheduler_task = asyncio.create_task(self._run_scheduler())
        self.logger.info("scheduler_started")

    async def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        self.logger.info("scheduler_stopped")

    async def _run_scheduler(self) -> None:
        """Main scheduler loop."""
        while self._running:
            try:
                due_schedules = [s for s in self._schedules.values() if s.is_due]

                for schedule in due_schedules:
                    await self._execute_scheduled_chain(schedule)

                await asyncio.sleep(1)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("scheduler_loop_error", error=str(e))
                await asyncio.sleep(5)

    async def _execute_scheduled_chain(self, schedule: Schedule) -> None:
        """Execute a scheduled chain."""
        if not self._execution_engine:
            self.logger.error("no_execution_engine_configured")
            return

        self.logger.info(
            "executing_scheduled_chain",
            schedule_id=schedule.schedule_id,
            chain_id=schedule.chain_id
        )

        try:
            context = await self._execution_engine.execute_chain(
                chain=schedule.chain,
                initial_inputs=schedule.initial_inputs
            )

            schedule.last_run = datetime.utcnow()
            schedule.run_count += 1

            if schedule.schedule_type == ScheduleType.INTERVAL:
                schedule.next_run = datetime.utcnow() + timedelta(seconds=30)
            elif schedule.schedule_type == ScheduleType.CRON:
                pass

            self.logger.info(
                "scheduled_chain_completed",
                schedule_id=schedule.schedule_id,
                status=context.status.value
            )

        except Exception as e:
            self.logger.error(
                "scheduled_chain_failed",
                schedule_id=schedule.schedule_id,
                error=str(e)
            )

    def _parse_cron(self, cron_expression: str) -> datetime:
        """Parse a cron expression to get next run time."""
        from croniter import croniter

        try:
            cron = croniter(cron_expression, datetime.utcnow())
            return cron.get_next(datetime)
        except Exception as e:
            self.logger.warning("cron_parse_failed", expression=cron_expression, error=str(e))
            return datetime.utcnow() + timedelta(hours=1)

    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        total = len(self._schedules)
        enabled = sum(1 for s in self._schedules.values() if s.enabled)
        due = sum(1 for s in self._schedules.values() if s.is_due)

        return {
            "running": self._running,
            "total_schedules": total,
            "enabled_schedules": enabled,
            "due_schedules": due,
            "total_runs": sum(s.run_count for s in self._schedules.values())
        }
