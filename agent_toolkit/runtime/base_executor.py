"""Base executor class for tool runtime."""

import asyncio
import time
import uuid
from typing import Any, Optional, Dict
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum

from agent_toolkit.shared.structured_logging import LoggerMixin


class ExecutionStatus(str, Enum):
    """Execution status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class ExecutorConfig:
    """Configuration for tool executor."""
    timeout: int = 300
    max_retries: int = 3
    retry_delay: float = 1.0
    enable_sandbox: bool = True
    cpu_limit: str = "2"
    memory_limit: str = "4Gi"
    disk_limit: str = "10Gi"
    network_enabled: bool = True
    environment: Dict[str, str] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """Result of tool execution."""
    execution_id: str
    tool_id: str
    status: ExecutionStatus
    output: Optional[Any] = None
    error: Optional[str] = None
    exit_code: Optional[int] = None
    execution_time_ms: float = 0.0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        """Check if execution was successful."""
        return self.status == ExecutionStatus.SUCCESS

    @property
    def is_terminal(self) -> bool:
        """Check if status is terminal."""
        return self.status in {
            ExecutionStatus.SUCCESS,
            ExecutionStatus.FAILED,
            ExecutionStatus.TIMEOUT,
            ExecutionStatus.CANCELLED
        }


class BaseExecutor(ABC, LoggerMixin):
    """Abstract base class for tool executors."""

    def __init__(self, config: ExecutorConfig):
        self.config = config
        self._is_initialized = False
        self._active_executions: Dict[str, asyncio.Task] = {}
        self._execution_results: Dict[str, ExecutionResult] = {}
        self._lock = asyncio.Lock()

    @abstractmethod
    async def _do_execute(
        self,
        tool_id: str,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """Execute tool. Must be implemented by subclasses."""
        pass

    async def initialize(self) -> None:
        """Initialize the executor."""
        if self._is_initialized:
            return
        
        self._is_initialized = True
        self.logger.info("executor_initialized", executor_type=self.__class__.__name__)

    async def execute(
        self,
        tool_id: str,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """Execute a tool with the given input."""
        if not self._is_initialized:
            await self.initialize()

        execution_id = str(uuid.uuid4())
        start_time = time.time()

        result = ExecutionResult(
            execution_id=execution_id,
            tool_id=tool_id,
            status=ExecutionStatus.PENDING,
            start_time=start_time,
            metadata={"context": context or {}}
        )

        self._execution_results[execution_id] = result

        self.logger.info(
            "execution_started",
            execution_id=execution_id,
            tool_id=tool_id
        )

        try:
            result.status = ExecutionStatus.RUNNING
            
            if self.config.timeout > 0:
                result = await asyncio.wait_for(
                    self._do_execute(tool_id, input_data, context),
                    timeout=self.config.timeout
                )
            else:
                result = await self._do_execute(tool_id, input_data, context)

            result.execution_id = execution_id
            result.start_time = start_time
            result.end_time = time.time()
            result.execution_time_ms = (result.end_time - start_time) * 1000

            self._execution_results[execution_id] = result

            self.logger.info(
                "execution_completed",
                execution_id=execution_id,
                tool_id=tool_id,
                status=result.status.value,
                execution_time_ms=result.execution_time_ms
            )

            return result

        except asyncio.TimeoutError:
            result.status = ExecutionStatus.TIMEOUT
            result.error = f"Execution timed out after {self.config.timeout}s"
            result.end_time = time.time()
            result.execution_time_ms = (result.end_time - start_time) * 1000
            
            self.logger.warning(
                "execution_timeout",
                execution_id=execution_id,
                tool_id=tool_id,
                timeout=self.config.timeout
            )
            
            return result

        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error = str(e)
            result.end_time = time.time()
            result.execution_time_ms = (result.end_time - start_time) * 1000
            
            self.logger.error(
                "execution_error",
                execution_id=execution_id,
                tool_id=tool_id,
                error=str(e)
            )
            
            return result

    async def execute_with_retry(
        self,
        tool_id: str,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """Execute with retry logic."""
        last_result: Optional[ExecutionResult] = None
        
        for attempt in range(self.config.max_retries + 1):
            result = await self.execute(tool_id, input_data, context)
            last_result = result
            
            if result.is_success:
                return result
            
            if attempt < self.config.max_retries:
                delay = self.config.retry_delay * (2 ** attempt)
                self.logger.info(
                    "execution_retry",
                    tool_id=tool_id,
                    attempt=attempt + 1,
                    delay=delay
                )
                await asyncio.sleep(delay)
        
        return last_result or ExecutionResult(
            execution_id="",
            tool_id=tool_id,
            status=ExecutionStatus.FAILED,
            error="Max retries exceeded"
        )

    async def cancel(self, execution_id: str) -> bool:
        """Cancel a running execution."""
        async with self._lock:
            if execution_id in self._active_executions:
                task = self._active_executions.pop(execution_id)
                task.cancel()
                
                if execution_id in self._execution_results:
                    self._execution_results[execution_id].status = ExecutionStatus.CANCELLED
                
                self.logger.info("execution_cancelled", execution_id=execution_id)
                return True
        return False

    def get_execution_status(self, execution_id: str) -> Optional[ExecutionResult]:
        """Get the status of an execution."""
        return self._execution_results.get(execution_id)

    def list_active_executions(self) -> list[str]:
        """List all active execution IDs."""
        return list(self._active_executions.keys())

    async def cleanup(self) -> None:
        """Cleanup executor resources."""
        for execution_id in list(self._active_executions.keys()):
            await self.cancel(execution_id)
        
        self._execution_results.clear()
        self._is_initialized = False
        
        self.logger.info("executor_cleaned_up")

    async def health_check(self) -> bool:
        """Check if executor is healthy."""
        return self._is_initialized

    def get_stats(self) -> Dict[str, Any]:
        """Get executor statistics."""
        total = len(self._execution_results)
        success = sum(
            1 for r in self._execution_results.values()
            if r.status == ExecutionStatus.SUCCESS
        )
        failed = sum(
            1 for r in self._execution_results.values()
            if r.status == ExecutionStatus.FAILED
        )
        
        return {
            "initialized": self._is_initialized,
            "active_executions": len(self._active_executions),
            "total_executions": total,
            "successful": success,
            "failed": failed,
            "success_rate": success / total if total > 0 else 0
        }
