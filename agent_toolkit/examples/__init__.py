"""
Agent Toolkit 使用示例集合

本模块包含 Agent Toolkit 各核心模块的使用示例代码，帮助开发者快速上手。
"""

from agent_toolkit.examples.registry_examples import (
    register_http_tool_example,
    register_cli_tool_example,
    search_tools_example,
    tool_version_management_example,
)
from agent_toolkit.examples.adapter_examples import (
    http_adapter_usage_example,
    cli_adapter_usage_example,
    sdk_adapter_usage_example,
)
from agent_toolkit.examples.runtime_examples import (
    docker_execution_example,
    kubernetes_execution_example,
)
from agent_toolkit.examples.orchestrator_examples import (
    sequential_chain_example,
    parallel_chain_example,
)
from agent_toolkit.examples.observability_examples import (
    metrics_collection_example,
    tracing_example,
)

__all__ = [
    "register_http_tool_example",
    "register_cli_tool_example",
    "search_tools_example",
    "tool_version_management_example",
    "http_adapter_usage_example",
    "cli_adapter_usage_example",
    "sdk_adapter_usage_example",
    "docker_execution_example",
    "kubernetes_execution_example",
    "sequential_chain_example",
    "parallel_chain_example",
    "metrics_collection_example",
    "tracing_example",
]
