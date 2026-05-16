"""Result aggregation for tool chain executions."""

from typing import Any, Dict, List, Optional
from datetime import datetime

from agent_toolkit.orchestrator.orchestration_models import ChainExecution, StepResult, StepStatus
from agent_toolkit.shared.structured_logging import get_logger


class ResultAggregator:
    """Aggregates results from tool chain executions."""
    
    def __init__(self):
        self.logger = get_logger("orchestrator.aggregator")
    
    def aggregate(self, execution: ChainExecution) -> Dict[str, Any]:
        """Aggregate results from an execution."""
        return {
            "execution_id": execution.execution_id,
            "chain_id": execution.chain_id,
            "status": execution.status.value,
            "summary": self._create_summary(execution),
            "step_results": self._aggregate_step_results(execution),
            "timeline": self._create_timeline(execution),
            "statistics": self._calculate_statistics(execution),
        }
    
    def _create_summary(self, execution: ChainExecution) -> Dict[str, Any]:
        """Create execution summary."""
        completed = sum(
            1 for r in execution.step_results.values()
            if r.status == StepStatus.COMPLETED
        )
        failed = sum(
            1 for r in execution.step_results.values()
            if r.status == StepStatus.FAILED
        )
        skipped = sum(
            1 for r in execution.step_results.values()
            if r.status == StepStatus.SKIPPED
        )
        
        return {
            "total_steps": len(execution.step_results),
            "completed": completed,
            "failed": failed,
            "skipped": skipped,
            "total_duration_ms": execution.total_duration_ms,
            "started_at": execution.started_at.isoformat(),
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
        }
    
    def _aggregate_step_results(
        self,
        execution: ChainExecution,
    ) -> Dict[str, Dict[str, Any]]:
        """Aggregate step results."""
        return {
            step_id: {
                "status": result.status.value,
                "duration_ms": result.duration_ms,
                "has_output": result.output is not None,
                "has_error": result.error is not None,
                "retries": result.retries,
            }
            for step_id, result in execution.step_results.items()
        }
    
    def _create_timeline(self, execution: ChainExecution) -> List[Dict[str, Any]]:
        """Create execution timeline."""
        events = []
        
        for result in execution.step_results.values():
            events.append({
                "step_id": result.step_id,
                "status": result.status.value,
                "started_at": result.started_at.isoformat(),
                "completed_at": result.completed_at.isoformat() if result.completed_at else None,
                "duration_ms": result.duration_ms,
            })
        
        return sorted(events, key=lambda x: x["started_at"])
    
    def _calculate_statistics(self, execution: ChainExecution) -> Dict[str, Any]:
        """Calculate execution statistics."""
        durations = [
            r.duration_ms for r in execution.step_results.values()
            if r.completed_at
        ]
        
        return {
            "total_duration_ms": execution.total_duration_ms,
            "average_step_duration_ms": sum(durations) / len(durations) if durations else 0,
            "max_step_duration_ms": max(durations) if durations else 0,
            "min_step_duration_ms": min(durations) if durations else 0,
            "success_rate": (
                sum(1 for r in execution.step_results.values() if r.status == StepStatus.COMPLETED)
                / len(execution.step_results)
                if execution.step_results else 0
            ),
        }
    
    def aggregate_multiple(
        self,
        executions: List[ChainExecution],
    ) -> Dict[str, Any]:
        """Aggregate multiple executions."""
        return {
            "total_executions": len(executions),
            "executions": [self.aggregate(ex) for ex in executions],
            "overall_statistics": self._calculate_overall_statistics(executions),
        }
    
    def _calculate_overall_statistics(
        self,
        executions: List[ChainExecution],
    ) -> Dict[str, Any]:
        """Calculate overall statistics across executions."""
        completed = sum(
            1 for ex in executions
            if ex.status == "completed"
        )
        
        return {
            "total_executions": len(executions),
            "completed": completed,
            "failed": len(executions) - completed,
            "success_rate": completed / len(executions) if executions else 0,
            "total_duration_ms": sum(ex.total_duration_ms for ex in executions),
            "average_duration_ms": (
                sum(ex.total_duration_ms for ex in executions) / len(executions)
                if executions else 0
            ),
        }
