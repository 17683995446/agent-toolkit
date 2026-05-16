"""Function adapter for executing local Python functions."""

from typing import Any, Dict, Optional, Callable, Awaitable, get_type_hints
import asyncio
import inspect

from agent_toolkit.adapter.base_adapter import (
    BaseAdapter,
    AdapterConfig,
    AdapterResult,
    ToolMetadata,
    ExecutionStatus,
    AdapterType,
)


class LocalFunctionAdapter(BaseAdapter):
    """Adapter for executing local Python functions."""
    
    def __init__(
        self,
        config: Optional[AdapterConfig] = None,
        metadata: Optional[ToolMetadata] = None,
        func: Optional[Callable] = None,
        name: Optional[str] = None,
    ):
        super().__init__(config, metadata)
        self.func = func
        self.func_name = name or (func.__name__ if func else "unknown")
        self._type_hints = get_type_hints(func) if func else {}
        self._signature = inspect.signature(func) if func else None
    
    @property
    def adapter_type(self) -> AdapterType:
        return AdapterType.FUNCTION
    
    async def initialize(self) -> None:
        """Initialize function adapter."""
        self.logger.info(
            "function_adapter_initialized",
            function=self.func_name,
            parameters=list(self._signature.parameters.keys()) if self._signature else []
        )
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> AdapterResult[Any]:
        """Execute the function."""
        if not self.func:
            return AdapterResult(
                status=ExecutionStatus.FAILURE,
                error=f"No function configured for {self.func_name}"
            )
        
        try:
            kwargs = {**input_data}
            
            if context:
                kwargs["_context"] = context
            
            if asyncio.iscoroutinefunction(self.func):
                result = await self.func(**kwargs)
            else:
                result = await asyncio.to_thread(self.func, **kwargs)
            
            return AdapterResult(
                status=ExecutionStatus.SUCCESS,
                data=result,
                metadata={
                    "function": self.func_name,
                    "input_keys": list(input_data.keys()),
                }
            )
        
        except TypeError as e:
            missing_param = str(e).split("'")[1] if "'" in str(e) else "unknown"
            return AdapterResult(
                status=ExecutionStatus.FAILURE,
                error=f"Missing required parameter: {missing_param}",
                metadata={"function": self.func_name}
            )
        except Exception as e:
            return AdapterResult(
                status=ExecutionStatus.FAILURE,
                error=f"{type(e).__name__}: {str(e)}",
                metadata={"function": self.func_name}
            )
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input against function signature."""
        if not self._signature:
            return False
        
        required_params = [
            name for name, param in self._signature.parameters.items()
            if param.default == inspect.Parameter.empty
            and name not in ("self", "_context")
        ]
        
        return all(param in input_data for param in required_params)
    
    def get_required_parameters(self) -> list[str]:
        """Get list of required parameters."""
        if not self._signature:
            return []
        
        return [
            name for name, param in self._signature.parameters.items()
            if param.default == inspect.Parameter.empty
            and name not in ("self", "_context")
        ]
    
    def get_optional_parameters(self) -> dict[str, Any]:
        """Get dict of optional parameters with defaults."""
        if not self._signature:
            return {}
        
        return {
            name: param.default
            for name, param in self._signature.parameters.items()
            if param.default != inspect.Parameter.empty
            and name not in ("self", "_context")
        }


def create_function_adapter(
    func: Callable,
    config: Optional[AdapterConfig] = None,
    metadata: Optional[ToolMetadata] = None,
) -> LocalFunctionAdapter:
    """Factory function to create a function adapter."""
    return LocalFunctionAdapter(
        config=config,
        metadata=metadata,
        func=func,
    )
