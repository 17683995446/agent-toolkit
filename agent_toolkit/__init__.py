"""Agent Toolkit - Multi-agent orchestration and tool management system."""

__version__ = "0.1.0"
__author__ = "Agent Toolkit Team"

from agent_toolkit.shared.application_settings import Settings
from agent_toolkit.shared.structured_logging import setup_logging
from agent_toolkit.shared.custom_exceptions import (
    AgentToolkitException,
    ConfigurationError,
    NotFoundError,
)

__all__ = [
    "__version__",
    "Settings",
    "setup_logging",
    "AgentToolkitException",
    "ConfigurationError",
    "NotFoundError",
]
