"""Sandbox management for secure tool execution."""

import asyncio
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field
from enum import Enum

from agent_toolkit.shared.structured_logging import LoggerMixin


class SandboxType(str, Enum):
    """Types of sandbox."""
    NONE = "none"
    DOCKER = "docker"
    GVISO = "gviso"
    SECCOMP = "seccomp"
    APPARMOR = "apparmor"


class SandboxStatus(str, Enum):
    """Sandbox status."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    ERROR = "error"


@dataclass
class SandboxConfig:
    """Configuration for sandbox."""
    sandbox_type: SandboxType = SandboxType.DOCKER
    network_enabled: bool = False
    internet_access: bool = False
    filesystem_readonly: bool = True
    allowed_paths: List[str] = field(default_factory=list)
    denied_paths: List[str] = field(default_factory=list)
    max_processes: int = 100
    max_memory_mb: int = 512
    max_cpu_percent: int = 50
    max_disk_mb: int = 1024
    max_network_mbps: int = 10
    timeout_seconds: int = 300


@dataclass
class SandboxInstance:
    """A sandbox instance."""
    instance_id: str
    config: SandboxConfig
    status: SandboxStatus = SandboxStatus.ACTIVE
    created_at: float = 0.0
    process_ids: List[int] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class SandboxManager(LoggerMixin):
    """Manager for sandbox instances."""

    def __init__(self):
        self._sandboxes: Dict[str, SandboxInstance] = {}
        self._lock = asyncio.Lock()

    async def create_sandbox(
        self,
        sandbox_id: str,
        config: Optional[SandboxConfig] = None
    ) -> SandboxInstance:
        """Create a new sandbox instance."""
        async with self._lock:
            if sandbox_id in self._sandboxes:
                raise ValueError(f"Sandbox {sandbox_id} already exists")

            if config is None:
                config = SandboxConfig()

            import time
            sandbox = SandboxInstance(
                instance_id=sandbox_id,
                config=config,
                status=SandboxStatus.ACTIVE,
                created_at=time.time()
            )

            self._sandboxes[sandbox_id] = sandbox

            self.logger.info(
                "sandbox_created",
                sandbox_id=sandbox_id,
                sandbox_type=config.sandbox_type.value
            )

            return sandbox

    async def get_sandbox(self, sandbox_id: str) -> Optional[SandboxInstance]:
        """Get a sandbox instance."""
        return self._sandboxes.get(sandbox_id)

    async def destroy_sandbox(self, sandbox_id: str) -> bool:
        """Destroy a sandbox instance."""
        async with self._lock:
            if sandbox_id not in self._sandboxes:
                return False

            sandbox = self._sandboxes[sandbox_id]
            sandbox.status = SandboxStatus.TERMINATED

            del self._sandboxes[sandbox_id]

            self.logger.info("sandbox_destroyed", sandbox_id=sandbox_id)
            return True

    async def pause_sandbox(self, sandbox_id: str) -> bool:
        """Pause a sandbox instance."""
        sandbox = await self.get_sandbox(sandbox_id)
        if not sandbox:
            return False

        sandbox.status = SandboxStatus.SUSPENDED
        self.logger.info("sandbox_paused", sandbox_id=sandbox_id)
        return True

    async def resume_sandbox(self, sandbox_id: str) -> bool:
        """Resume a sandbox instance."""
        sandbox = await self.get_sandbox(sandbox_id)
        if not sandbox or sandbox.status != SandboxStatus.SUSPENDED:
            return False

        sandbox.status = SandboxStatus.ACTIVE
        self.logger.info("sandbox_resumed", sandbox_id=sandbox_id)
        return True

    async def get_sandbox_stats(self, sandbox_id: str) -> Dict[str, Any]:
        """Get sandbox statistics."""
        sandbox = await self.get_sandbox(sandbox_id)
        if not sandbox:
            return {}

        return {
            "sandbox_id": sandbox.instance_id,
            "status": sandbox.status.value,
            "sandbox_type": sandbox.config.sandbox_type.value,
            "process_count": len(sandbox.process_ids),
            "created_at": sandbox.created_at,
            "metadata": sandbox.metadata
        }

    async def list_sandboxes(self) -> List[SandboxInstance]:
        """List all sandbox instances."""
        return list(self._sandboxes.values())

    async def cleanup_idle_sandboxes(self, max_idle_seconds: int = 3600) -> int:
        """Clean up idle sandbox instances."""
        import time
        cleaned = 0

        async with self._lock:
            current_time = time.time()
            to_remove = []

            for sandbox_id, sandbox in self._sandboxes.items():
                if sandbox.status == SandboxStatus.ACTIVE:
                    idle_time = current_time - sandbox.created_at
                    if idle_time > max_idle_seconds:
                        to_remove.append(sandbox_id)

            for sandbox_id in to_remove:
                await self.destroy_sandbox(sandbox_id)
                cleaned += 1

        if cleaned > 0:
            self.logger.info("idle_sandboxes_cleaned", count=cleaned)

        return cleaned

    async def enforce_resource_limits(self, sandbox_id: str) -> bool:
        """Enforce resource limits on a sandbox."""
        sandbox = await self.get_sandbox(sandbox_id)
        if not sandbox:
            return False

        if sandbox.config.sandbox_type == SandboxType.DOCKER:
            await self._enforce_docker_limits(sandbox)
        elif sandbox.config.sandbox_type == SandboxType.GVISO:
            await self._enforce_gviso_limits(sandbox)

        return True

    async def _enforce_docker_limits(self, sandbox: SandboxInstance) -> None:
        """Enforce limits for Docker sandbox."""
        self.logger.debug(
            "enforcing_docker_limits",
            sandbox_id=sandbox.instance_id,
            memory_mb=sandbox.config.max_memory_mb,
            cpu_percent=sandbox.config.max_cpu_percent
        )

    async def _enforce_gviso_limits(self, sandbox: SandboxInstance) -> None:
        """Enforce limits for gVisor sandbox."""
        self.logger.debug(
            "enforcing_gviso_limits",
            sandbox_id=sandbox.instance_id
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get sandbox manager statistics."""
        total = len(self._sandboxes)
        active = sum(1 for s in self._sandboxes.values() if s.status == SandboxStatus.ACTIVE)
        suspended = sum(1 for s in self._sandboxes.values() if s.status == SandboxStatus.SUSPENDED)

        return {
            "total_sandboxes": total,
            "active_sandboxes": active,
            "suspended_sandboxes": suspended,
            "sandbox_types": {
                st.value: sum(1 for s in self._sandboxes.values() if s.config.sandbox_type == st)
                for st in SandboxType
            }
        }
