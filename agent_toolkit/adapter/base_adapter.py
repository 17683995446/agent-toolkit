"""Base adapter class and interfaces."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Generic, TypeVar
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio

from agent_toolkit.shared.structured_logging import LoggerMixin, get_logger


T = TypeVar("T")


class AdapterType(str, Enum):
    """Adapter type enumeration."""
    HTTP = "http"
    CLI = "cli"
    SDK = "sdk"
    FUNCTION = "function"
    GRAPHQL = "graphql"
    WEBSOCKET = "websocket"


class ExecutionStatus(str, Enum):
    """Execution status enumeration."""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    PENDING = "pending"


@dataclass
class AdapterConfig:
    """Base configuration for adapters."""
    timeout: int = 30
    retry_count: int = 0
    retry_delay: float = 1.0
    enable_caching: bool = False
    cache_ttl: int = 300


@dataclass
class AdapterResult(Generic[T]):
    """Result from adapter execution."""
    status: ExecutionStatus
    data: Optional[T] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def is_success(self) -> bool:
        """Check if execution was successful."""
        return self.status == ExecutionStatus.SUCCESS
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "status": self.status.value,
            "data": self.data,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ToolMetadata:
    """Metadata for a tool."""
    name: str
    version: str
    adapter_type: AdapterType
    description: str = ""
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)


class BaseAdapter(ABC, LoggerMixin):
    """Abstract base class for all adapters."""
    
    def __init__(
        self,
        config: Optional[AdapterConfig] = None,
        metadata: Optional[ToolMetadata] = None,
    ):
        self.config = config or AdapterConfig()
        self.metadata = metadata
        self._is_initialized = False
        self._lock = asyncio.Lock()
    
    @property
    def adapter_type(self) -> AdapterType:
        """Get the adapter type."""
        raise NotImplementedError
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the adapter."""
        pass
    
    @abstractmethod
    async def execute(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> AdapterResult[Any]:
        """Execute the tool with given input."""
        pass
    
    @abstractmethod
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data against schema."""
        pass
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        self._is_initialized = False
    
    async def health_check(self) -> bool:
        """Check if adapter is healthy."""
        return self._is_initialized
    
    async def _ensure_initialized(self) -> None:
        """Ensure adapter is initialized before use."""
        if not self._is_initialized:
            async with self._lock:
                if not self._is_initialized:
                    await self.initialize()
                    self._is_initialized = True
    
    async def _execute_with_retry(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> AdapterResult[Any]:
        """Execute with retry logic."""
        last_error = None
        
        for attempt in range(self.config.retry_count + 1):
            try:
                result = await self.execute(input_data, context)
                if result.is_success:
                    return result
                last_error = result.error
            except Exception as e:
                last_error = str(e)
                self.logger.error(
                    "adapter_execution_error",
                    attempt=attempt + 1,
                    error=str(e)
                )
            
            if attempt < self.config.retry_count:
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))
        
        return AdapterResult(
            status=ExecutionStatus.FAILURE,
            error=last_error or "Max retries exceeded",
            metadata={"attempts": self.config.retry_count + 1}
        )
