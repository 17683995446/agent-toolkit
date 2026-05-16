"""Logging configuration for observability."""

from typing import Any, Dict, Optional
import logging
import sys
from datetime import datetime

import structlog

from agent_toolkit.shared.structured_logging import setup_logging as shared_setup_logging, get_logger


class ObservabilityLogging:
    """Logging configuration for observability components."""
    
    def __init__(
        self,
        service_name: str = "agent-toolkit",
        log_level: str = "INFO",
        json_format: bool = True,
    ):
        self.service_name = service_name
        self.log_level = log_level
        self.json_format = json_format
        self._logger = get_logger("observability.logging")
    
    def configure(self) -> None:
        """Configure logging for observability."""
        shared_setup_logging()
        
        self._logger.info(
            "observability_logging_configured",
            service=self.service_name,
            level=self.log_level,
            format="json" if self.json_format else "console"
        )
    
    def log_execution(
        self,
        execution_id: str,
        tool_name: str,
        status: str,
        duration_ms: float,
        error: Optional[str] = None,
    ) -> None:
        """Log tool execution."""
        log_data = {
            "execution_id": execution_id,
            "tool_name": tool_name,
            "status": status,
            "duration_ms": duration_ms,
            "event_type": "tool_execution",
        }
        
        if error:
            log_data["error"] = error
            self._logger.error("tool_execution_failed", **log_data)
        else:
            self._logger.info("tool_execution_completed", **log_data)
    
    def log_chain_execution(
        self,
        execution_id: str,
        chain_id: str,
        status: str,
        total_steps: int,
        completed_steps: int,
        duration_ms: float,
    ) -> None:
        """Log chain execution."""
        self._logger.info(
            "chain_execution_completed",
            execution_id=execution_id,
            chain_id=chain_id,
            status=status,
            total_steps=total_steps,
            completed_steps=completed_steps,
            duration_ms=duration_ms,
            event_type="chain_execution",
        )
    
    def log_resource_usage(
        self,
        cpu_percent: float,
        memory_mb: float,
        active_executions: int,
    ) -> None:
        """Log resource usage."""
        self._logger.info(
            "resource_usage",
            cpu_percent=cpu_percent,
            memory_mb=memory_mb,
            active_executions=active_executions,
            event_type="resource_monitor",
        )
    
    def log_error(
        self,
        error: Exception,
        context: Dict[str, Any],
    ) -> None:
        """Log an error with context."""
        self._logger.error(
            "error_occurred",
            error_type=type(error).__name__,
            error_message=str(error),
            context=context,
            event_type="error",
        )
    
    def log_audit_event(
        self,
        event: str,
        user: Optional[str],
        resource: str,
        action: str,
        result: str,
    ) -> None:
        """Log an audit event."""
        self._logger.info(
            "audit_event",
            event=event,
            user=user,
            resource=resource,
            action=action,
            result=result,
            event_type="audit",
        )


class ExecutionLogger:
    """Logger for tool execution tracking."""
    
    def __init__(self, logger: Optional[Any] = None):
        self.logger = logger or get_logger("execution")
        self._active_executions: Dict[str, Dict[str, Any]] = {}
    
    def start_execution(
        self,
        execution_id: str,
        tool_name: str,
        input_data: Dict[str, Any],
    ) -> None:
        """Log execution start."""
        self._active_executions[execution_id] = {
            "tool_name": tool_name,
            "started_at": datetime.utcnow(),
            "input_data": input_data,
        }
        
        self.logger.info(
            "execution_started",
            execution_id=execution_id,
            tool_name=tool_name,
            event_type="execution_start",
        )
    
    def complete_execution(
        self,
        execution_id: str,
        output: Any,
        duration_ms: float,
    ) -> None:
        """Log execution completion."""
        if execution_id in self._active_executions:
            exec_info = self._active_executions.pop(execution_id)
            tool_name = exec_info["tool_name"]
        else:
            tool_name = "unknown"
        
        self.logger.info(
            "execution_completed",
            execution_id=execution_id,
            tool_name=tool_name,
            duration_ms=duration_ms,
            event_type="execution_complete",
        )
    
    def fail_execution(
        self,
        execution_id: str,
        error: str,
        duration_ms: float,
    ) -> None:
        """Log execution failure."""
        if execution_id in self._active_executions:
            exec_info = self._active_executions.pop(execution_id)
            tool_name = exec_info["tool_name"]
        else:
            tool_name = "unknown"
        
        self.logger.error(
            "execution_failed",
            execution_id=execution_id,
            tool_name=tool_name,
            error=error,
            duration_ms=duration_ms,
            event_type="execution_failed",
        )
    
    def get_active_count(self) -> int:
        """Get count of active executions."""
        return len(self._active_executions)
