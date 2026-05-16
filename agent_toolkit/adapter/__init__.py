"""Tool Adapter - Adapts various tool interfaces to a unified API."""

from agent_toolkit.adapter.base_adapter import BaseAdapter, AdapterResult
from agent_toolkit.adapter.http_adapter_implementation import HTTPAdapter
from agent_toolkit.adapter.cli_adapter_implementation import CLIAdapter
from agent_toolkit.adapter.sdk_adapter_implementation import SDKAdapter
from agent_toolkit.adapter.function_adapter_implementation import LocalFunctionAdapter
from agent_toolkit.adapter.adapter_registry import AdapterRegistry

__version__ = "0.1.0"

__all__ = [
    "BaseAdapter",
    "AdapterResult",
    "HTTPAdapter",
    "CLIAdapter",
    "SDKAdapter",
    "LocalFunctionAdapter",
    "AdapterRegistry",
]
