"""Tool Runtime - Execution environment for agent tools."""

from agent_toolkit.runtime.base_executor import BaseExecutor, ExecutionStatus, ExecutionResult
from agent_toolkit.runtime.sandbox_manager import SandboxManager
from agent_toolkit.runtime.resource_manager import ResourceManager

# 可选导入（避免缺少依赖时程序无法启动）
DockerExecutor = None
KubernetesExecutor = None

try:
    from agent_toolkit.runtime.docker_executor_implementation import DockerExecutor
except ImportError:
    pass

try:
    from agent_toolkit.runtime.kubernetes_executor_implementation import KubernetesExecutor
except ImportError:
    pass

__version__ = "0.1.0"

__all__ = [
    "BaseExecutor",
    "ExecutionStatus",
    "ExecutionResult",
    "SandboxManager",
    "ResourceManager",
]

# 只有成功导入时才添加到 __all__
if DockerExecutor is not None:
    __all__.append("DockerExecutor")
if KubernetesExecutor is not None:
    __all__.append("KubernetesExecutor")
