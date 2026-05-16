"""Adapter Registry for managing and discovering adapters."""

from typing import Dict, Type, Optional, Any
from enum import Enum

from agent_toolkit.adapter.base_adapter import BaseAdapter, AdapterType, ToolMetadata
from agent_toolkit.adapter.http_adapter_implementation import HTTPAdapter, HTTPAdapterConfig
from agent_toolkit.adapter.cli_adapter_implementation import CLIAdapter, CLIAdapterConfig
from agent_toolkit.adapter.sdk_adapter_implementation import SDKAdapter, SDKAdapterConfig, FunctionAdapter
from agent_toolkit.shared.structured_logging import LoggerMixin


class AdapterRegistry(LoggerMixin):
    """Registry for managing adapter instances."""

    def __init__(self):
        self._adapters: Dict[str, BaseAdapter] = {}
        self._adapter_factories: Dict[AdapterType, Type[BaseAdapter]] = {
            AdapterType.HTTP: HTTPAdapter,
            AdapterType.CLI: CLIAdapter,
            AdapterType.SDK: SDKAdapter,
            AdapterType.FUNCTION: FunctionAdapter,
        }

    def register(self, name: str, adapter: BaseAdapter) -> None:
        """Register an adapter instance."""
        self._adapters[name] = adapter
        self.logger.info("adapter_registered", name=name, type=adapter.adapter_type.value)

    def unregister(self, name: str) -> bool:
        """Unregister an adapter."""
        if name in self._adapters:
            adapter = self._adapters.pop(name)
            self.logger.info("adapter_unregistered", name=name, type=adapter.adapter_type.value)
            return True
        return False

    def get(self, name: str) -> Optional[BaseAdapter]:
        """Get an adapter by name."""
        return self._adapters.get(name)

    def list_adapters(self) -> Dict[str, Dict[str, Any]]:
        """List all registered adapters."""
        return {
            name: {
                "type": adapter.adapter_type.value,
                "metadata": adapter.metadata.__dict__ if adapter.metadata else None,
                "initialized": adapter._is_initialized,
            }
            for name, adapter in self._adapters.items()
        }

    def create_adapter(
        self,
        adapter_type: AdapterType,
        config: Any,
        metadata: Optional[ToolMetadata] = None,
        name: Optional[str] = None,
    ) -> BaseAdapter:
        """Create and optionally register a new adapter."""
        factory = self._adapter_factories.get(adapter_type)
        if not factory:
            raise ValueError(f"Unknown adapter type: {adapter_type}")

        adapter = factory(config=config, metadata=metadata)
        
        if name:
            self.register(name, adapter)

        return adapter

    async def initialize_all(self) -> None:
        """Initialize all registered adapters."""
        for name, adapter in self._adapters.items():
            if not adapter._is_initialized:
                try:
                    await adapter.initialize()
                    self.logger.info("adapter_initialized", name=name)
                except Exception as e:
                    self.logger.error("adapter_init_failed", name=name, error=str(e))

    async def cleanup_all(self) -> None:
        """Cleanup all registered adapters."""
        for name, adapter in self._adapters.items():
            try:
                await adapter.cleanup()
                self.logger.info("adapter_cleaned_up", name=name)
            except Exception as e:
                self.logger.error("adapter_cleanup_failed", name=name, error=str(e))


_global_registry: Optional[AdapterRegistry] = None


def get_adapter_registry() -> AdapterRegistry:
    """Get the global adapter registry instance."""
    global _global_registry
    if _global_registry is None:
        _global_registry = AdapterRegistry()
    return _global_registry


def register_adapter(name: str, adapter: BaseAdapter) -> None:
    """Register an adapter in the global registry."""
    get_adapter_registry().register(name, adapter)


def get_adapter(name: str) -> Optional[BaseAdapter]:
    """Get an adapter from the global registry."""
    return get_adapter_registry().get(name)


def create_and_register_adapter(
    adapter_type: AdapterType,
    name: str,
    config: Any,
    metadata: Optional[ToolMetadata] = None,
) -> BaseAdapter:
    """Create and register an adapter in the global registry."""
    adapter = get_adapter_registry().create_adapter(
        adapter_type=adapter_type,
        config=config,
        metadata=metadata,
        name=name,
    )
    return adapter
