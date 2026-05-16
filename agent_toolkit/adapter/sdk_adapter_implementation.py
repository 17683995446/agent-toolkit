"""SDK Adapter implementation."""

import asyncio
import importlib
from typing import Any, Optional, Dict, Callable
from dataclasses import dataclass, field

from pydantic import BaseModel, Field

from agent_toolkit.adapter.base_adapter import (
    BaseAdapter,
    AdapterType,
    AdapterConfig,
    AdapterResult,
    ToolMetadata,
    ExecutionStatus,
)
from agent_toolkit.shared.structured_logging import LoggerMixin


class SDKAdapterConfig(BaseModel):
    """Configuration for SDK adapter."""
    module_name: str = Field(..., description="Python module name")
    class_name: Optional[str] = Field(None, description="Class name to instantiate")
    function_name: Optional[str] = Field(None, description="Function name to call")
    init_kwargs: Dict[str, Any] = Field(default_factory=dict, description="Initialization kwargs")
    method_name: str = Field("execute", description="Method name to call")
    input_schema: Optional[Dict[str, Any]] = Field(None, description="Input JSON schema")


class SDKAdapter(BaseAdapter, LoggerMixin):
    """Adapter for Python SDK integrations."""

    def __init__(
        self,
        config: SDKAdapterConfig,
        metadata: Optional[ToolMetadata] = None,
    ):
        self._config = config
        self._instance: Optional[Any] = None
        self._module: Optional[Any] = None
        self._method: Optional[Callable] = None
        super().__init__(config=config, metadata=metadata)

    @property
    def adapter_type(self) -> AdapterType:
        """Get adapter type."""
        return AdapterType.SDK

    async def initialize(self) -> None:
        """Initialize the SDK adapter."""
        try:
            self._module = importlib.import_module(self._config.module_name)
            
            if self._config.class_name:
                cls = getattr(self._module, self._config.class_name)
                self._instance = cls(**self._config.init_kwargs)
                self._method = getattr(self._instance, self._config.method_name)
            elif self._config.function_name:
                self._method = getattr(self._module, self._config.function_name)
            elif hasattr(self._module, self._config.method_name):
                self._method = getattr(self._module, self._config.method_name)

            self.logger.info(
                "sdk_adapter_initialized",
                module=self._config.module_name,
                class_name=self._config.class_name,
                method=self._config.method_name
            )

        except ImportError as e:
            self.logger.error("sdk_import_error", module=self._config.module_name, error=str(e))
            raise
        except AttributeError as e:
            self.logger.error("sdk_attribute_error", error=str(e))
            raise

    async def execute(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> AdapterResult[Any]:
        """Execute SDK method/function."""
        import time
        start_time = time.time()

        try:
            if not self._method:
                await self.initialize()

            self.logger.debug(
                "sdk_execution_start",
                method=self._config.method_name,
                input_keys=list(input_data.keys())
            )

            if asyncio.iscoroutinefunction(self._method):
                result = await self._method(**input_data)
            else:
                result = self._method(**input_data)

            execution_time = (time.time() - start_time) * 1000

            self.logger.info(
                "sdk_execution_success",
                execution_time_ms=execution_time
            )

            return AdapterResult(
                status=ExecutionStatus.SUCCESS,
                data=result,
                execution_time_ms=execution_time,
                metadata={
                    "method": self._config.method_name,
                    "module": self._config.module_name,
                }
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.error("sdk_execution_error", error=str(e))
            
            return AdapterResult(
                status=ExecutionStatus.FAILURE,
                error=str(e),
                execution_time_ms=execution_time,
                metadata={
                    "method": self._config.method_name,
                    "module": self._config.module_name,
                }
            )

    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data against schema."""
        if not self._config.input_schema:
            return True

        required_fields = self._config.input_schema.get("required", [])
        for field_name in required_fields:
            if field_name not in input_data:
                self.logger.warning(
                    "validation_failed",
                    reason=f"Missing required field: {field_name}"
                )
                return False

        return True

    async def health_check(self) -> bool:
        """Check if the SDK adapter is healthy."""
        if not self._method:
            return False
        
        try:
            if hasattr(self._method, '__self__'):
                instance_class = type(self._method.__self__)
                return instance_class is not None
            return True
        except Exception:
            return False

    async def cleanup(self) -> None:
        """Cleanup SDK resources."""
        if self._instance and hasattr(self._instance, 'close'):
            try:
                if asyncio.iscoroutinefunction(self._instance.close):
                    await self._instance.close()
                else:
                    self._instance.close()
            except Exception as e:
                self.logger.warning("sdk_cleanup_error", error=str(e))
        
        self._instance = None
        self._module = None
        self._method = None


class FunctionAdapter(BaseAdapter, LoggerMixin):
    """Adapter for local Python functions."""

    def __init__(
        self,
        func: Callable,
        metadata: Optional[ToolMetadata] = None,
        input_schema: Optional[Dict[str, Any]] = None,
    ):
        self._func = func
        self._input_schema = input_schema
        super().__init__(config=AdapterConfig(), metadata=metadata)

    @property
    def adapter_type(self) -> AdapterType:
        """Get adapter type."""
        return AdapterType.FUNCTION

    async def initialize(self) -> None:
        """Initialize the function adapter."""
        self.logger.info(
            "function_adapter_initialized",
            function=self._func.__name__
        )

    async def execute(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> AdapterResult[Any]:
        """Execute the function."""
        import time
        start_time = time.time()

        try:
            self.logger.debug(
                "function_execution_start",
                function=self._func.__name__
            )

            if asyncio.iscoroutinefunction(self._func):
                result = await self._func(**input_data)
            else:
                result = self._func(**input_data)

            execution_time = (time.time() - start_time) * 1000

            self.logger.info(
                "function_execution_success",
                execution_time_ms=execution_time
            )

            return AdapterResult(
                status=ExecutionStatus.SUCCESS,
                data=result,
                execution_time_ms=execution_time,
                metadata={
                    "function": self._func.__name__,
                }
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.error("function_execution_error", error=str(e))
            
            return AdapterResult(
                status=ExecutionStatus.FAILURE,
                error=str(e),
                execution_time_ms=execution_time,
                metadata={
                    "function": self._func.__name__,
                }
            )

    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data against schema."""
        if not self._input_schema:
            return True

        required_fields = self._input_schema.get("required", [])
        for field_name in required_fields:
            if field_name not in input_data:
                return False

        return True
