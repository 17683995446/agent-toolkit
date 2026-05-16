"""Resource management for tool execution."""

import asyncio
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    psutil = None
    HAS_PSUTIL = False

from agent_toolkit.shared.structured_logging import LoggerMixin


@dataclass
class ResourceLimit:
    """Resource limit configuration."""
    cpu_cores: float = 2.0
    memory_mb: int = 4096
    disk_mb: int = 10240
    network_mbps: int = 100
    max_processes: int = 100
    max_open_files: int = 1024


@dataclass
class ResourceUsage:
    """Current resource usage."""
    cpu_percent: float = 0.0
    memory_mb: int = 0
    memory_percent: float = 0.0
    disk_mb: int = 0
    network_mbps: float = 0.0
    process_count: int = 0
    thread_count: int = 0
    open_files: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ExecutionResource:
    """Resources allocated for an execution."""
    execution_id: str
    limits: ResourceLimit
    usage: ResourceUsage = field(default_factory=ResourceUsage)
    allocated_at: datetime = field(default_factory=datetime.utcnow)


class ResourceManager(LoggerMixin):
    """Manager for execution resources."""

    def __init__(self):
        self._resources: Dict[str, ExecutionResource] = {}
        self._system_limits = ResourceLimit()
        self._lock = asyncio.Lock()

    async def allocate_resources(
        self,
        execution_id: str,
        limits: Optional[ResourceLimit] = None
    ) -> ExecutionResource:
        """Allocate resources for an execution."""
        async with self._lock:
            if execution_id in self._resources:
                raise ValueError(f"Resources already allocated for {execution_id}")

            if limits is None:
                limits = self._system_limits

            resource = ExecutionResource(
                execution_id=execution_id,
                limits=limits
            )

            self._resources[execution_id] = resource

            self.logger.info(
                "resources_allocated",
                execution_id=execution_id,
                limits=limits.__dict__
            )

            return resource

    async def release_resources(self, execution_id: str) -> bool:
        """Release resources allocated for an execution."""
        async with self._lock:
            if execution_id not in self._resources:
                return False

            resource = self._resources.pop(execution_id)

            self.logger.info(
                "resources_released",
                execution_id=execution_id
            )

            return True

    async def get_resources(self, execution_id: str) -> Optional[ExecutionResource]:
        """Get allocated resources for an execution."""
        return self._resources.get(execution_id)

    async def update_usage(self, execution_id: str) -> bool:
        """Update resource usage for an execution."""
        resource = await self.get_resources(execution_id)
        if not resource:
            return False

        usage = await self._collect_system_usage()
        resource.usage = usage

        return True

    async def check_limits(self, execution_id: str) -> tuple[bool, Dict[str, Any]]:
        """Check if resource usage is within limits."""
        resource = await self.get_resources(execution_id)
        if not resource:
            return False, {}

        violations = {}

        if resource.usage.cpu_percent > resource.limits.cpu_cores * 100:
            violations["cpu"] = {
                "used": resource.usage.cpu_percent,
                "limit": resource.limits.cpu_cores * 100
            }

        if resource.usage.memory_mb > resource.limits.memory_mb:
            violations["memory"] = {
                "used": resource.usage.memory_mb,
                "limit": resource.limits.memory_mb
            }

        if resource.usage.disk_mb > resource.limits.disk_mb:
            violations["disk"] = {
                "used": resource.usage.disk_mb,
                "limit": resource.limits.disk_mb
            }

        if resource.usage.process_count > resource.limits.max_processes:
            violations["processes"] = {
                "used": resource.usage.process_count,
                "limit": resource.limits.max_processes
            }

        if resource.usage.open_files > resource.limits.max_open_files:
            violations["open_files"] = {
                "used": resource.usage.open_files,
                "limit": resource.limits.max_open_files
            }

        return len(violations) == 0, violations

    async def get_system_resources(self) -> Dict[str, Any]:
        """Get overall system resource information."""
        if HAS_PSUTIL and psutil is not None:
            return {
                "cpu": {
                    "count": psutil.cpu_count(),
                    "percent": psutil.cpu_percent(interval=0.1),
                    "per_cpu": psutil.cpu_percent(interval=0.1, percpu=True),
                },
                "memory": {
                    "total": psutil.virtual_memory().total,
                    "available": psutil.virtual_memory().available,
                    "percent": psutil.virtual_memory().percent,
                },
                "disk": {
                    "total": psutil.disk_usage("/").total,
                    "used": psutil.disk_usage("/").used,
                    "free": psutil.disk_usage("/").free,
                    "percent": psutil.disk_usage("/").percent,
                },
                "network": {
                    "connections": len(psutil.net_connections()),
                }
            }
        else:
            return {
                "cpu": {"count": 2, "percent": 0, "per_cpu": []},
                "memory": {"total": 0, "available": 0, "percent": 0},
                "disk": {"total": 0, "used": 0, "free": 0, "percent": 0},
                "network": {"connections": 0},
                "psutil_available": False
            }

    async def _collect_system_usage(self) -> ResourceUsage:
        """Collect current system resource usage."""
        if HAS_PSUTIL and psutil is not None:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            return ResourceUsage(
                cpu_percent=cpu_percent,
                memory_mb=memory.used // (1024 * 1024),
                memory_percent=memory.percent,
                process_count=len(psutil.pids()),
                timestamp=datetime.utcnow()
            )
        else:
            return ResourceUsage(
                cpu_percent=0,
                memory_mb=0,
                memory_percent=0,
                process_count=0,
                timestamp=datetime.utcnow()
            )

    async def cleanup_stale_resources(self, max_age_seconds: int = 3600) -> int:
        """Clean up stale resource allocations."""
        cleaned = 0
        current_time = datetime.utcnow()

        async with self._lock:
            to_remove = []

            for execution_id, resource in self._resources.items():
                age = (current_time - resource.allocated_at).total_seconds()
                if age > max_age_seconds:
                    to_remove.append(execution_id)

            for execution_id in to_remove:
                await self.release_resources(execution_id)
                cleaned += 1

        if cleaned > 0:
            self.logger.info("stale_resources_cleaned", count=cleaned)

        return cleaned

    def set_system_limits(self, limits: ResourceLimit) -> None:
        """Set system-wide resource limits."""
        self._system_limits = limits
        self.logger.info("system_limits_updated", limits=limits.__dict__)

    def get_stats(self) -> Dict[str, Any]:
        """Get resource manager statistics."""
        total = len(self._resources)
        total_memory = sum(r.limits.memory_mb for r in self._resources.values())
        total_cpu = sum(r.limits.cpu_cores for r in self._resources.values())

        return {
            "total_allocations": total,
            "total_allocated_memory_mb": total_memory,
            "total_allocated_cpu_cores": total_cpu,
            "system_limits": self._system_limits.__dict__
        }


_global_resource_manager: Optional[ResourceManager] = None


def get_resource_manager() -> ResourceManager:
    """Get the global resource manager instance."""
    global _global_resource_manager
    if _global_resource_manager is None:
        _global_resource_manager = ResourceManager()
    return _global_resource_manager
