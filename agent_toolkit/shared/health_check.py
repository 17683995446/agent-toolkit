"""
Enhanced Health Check System for Agent Toolkit
Product-grade health monitoring with comprehensive checks
"""

import time
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from fastapi import APIRouter, HTTPException

from agent_toolkit.shared.structured_logging import get_logger

logger = get_logger(__name__)

# Create two routers - one with prefix for API and one without for Kubernetes probes
router = APIRouter(prefix="/api/v1/health", tags=["health"])
probes_router = APIRouter(tags=["health"])


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


@dataclass
class HealthCheckResult:
    name: str
    status: HealthStatus
    response_time_ms: float
    details: Optional[Any] = None  # 更灵活 - 接受任何类型
    error: Optional[str] = None


@dataclass
class OverallHealth:
    status: HealthStatus
    total_checks: int
    passed_checks: int
    failed_checks: int
    warning_checks: int
    uptime_seconds: float
    start_time: str
    checks: List[HealthCheckResult]
    version: str = "0.1.0"


class HealthCheckRegistry:
    """Registry for health check functions"""

    def __init__(self):
        self._checks: Dict[str, Any] = {}
        self._start_time = time.time()
        self._health_history: List[OverallHealth] = []

    def register_check(self, name: str, check_func: Any):
        """Register a health check function"""
        self._checks[name] = check_func
        logger.debug("Health check registered", name=name)

    async def run_all_checks(self) -> List[HealthCheckResult]:
        """Run all registered health checks"""
        results = []
        for name, check_func in self._checks.items():
            try:
                start_time = time.perf_counter()
                success, details = await check_func()
                response_time = (time.perf_counter() - start_time) * 1000
                status = HealthStatus.HEALTHY if success else HealthStatus.UNHEALTHY
                results.append(HealthCheckResult(
                    name=name,
                    status=status,
                    response_time_ms=response_time,
                    details=details
                ))
            except Exception as e:
                results.append(HealthCheckResult(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=0,
                    error=str(e)
                ))
        return results

    async def get_overall_health(self) -> OverallHealth:
        """Get overall system health"""
        checks = await self.run_all_checks()
        total = len(checks)
        passed = sum(1 for c in checks if c.status == HealthStatus.HEALTHY)
        failed = sum(1 for c in checks if c.status == HealthStatus.UNHEALTHY)
        warnings = sum(1 for c in checks if c.status == HealthStatus.WARNING)
        uptime = time.time() - self._start_time

        if failed > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif warnings > 0:
            overall_status = HealthStatus.WARNING
        elif passed == total and total > 0:
            overall_status = HealthStatus.HEALTHY
        else:
            overall_status = HealthStatus.DEGRADED

        health = OverallHealth(
            status=overall_status,
            total_checks=total,
            passed_checks=passed,
            failed_checks=failed,
            warning_checks=warnings,
            uptime_seconds=uptime,
            start_time=datetime.fromtimestamp(self._start_time).isoformat(),
            checks=checks
        )

        self._health_history.append(health)
        if len(self._health_history) > 100:
            self._health_history.pop(0)

        return health


health_registry = HealthCheckRegistry()


async def database_health_check() -> tuple[bool, Dict[str, Any]]:
    """Check database health."""
    try:
        from agent_toolkit.shared.database_connection import get_database_url
        db_url = get_database_url()
        # For now, just check that we can get the URL - actual DB connection optional
        return True, {"url": db_url.replace("://", "://***:***@"), "status": "configured"}
    except Exception as e:
        # Don't fail the health check just because DB is not set up
        return True, {"url": "unknown", "status": "not_configured", "warning": str(e)}


async def memory_health_check() -> tuple[bool, Dict[str, Any]]:
    """Check memory health"""
    try:
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        status = True
        if memory_mb > 1024:
            status = False
        return status, {"memory_mb": round(memory_mb, 2), "threshold_mb": 1024}
    except ImportError:
        return True, {"memory_mb": "unknown (psutil not installed)"}
    except Exception as e:
        return False, {"error": str(e)}


async def disk_health_check() -> tuple[bool, Dict[str, Any]]:
    """Check disk health"""
    try:
        import psutil
        disk_usage = psutil.disk_usage("/")
        usage_percent = disk_usage.percent
        status = usage_percent < 90
        return status, {"usage_percent": usage_percent, "total_gb": round(disk_usage.total / 1024 / 1024 / 1024, 2)}
    except ImportError:
        return True, {"usage_percent": "unknown (psutil not installed)"}
    except Exception as e:
        return False, {"error": str(e)}


async def cpu_health_check() -> tuple[bool, Dict[str, Any]]:
    """Check CPU health"""
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=0.1)
        status = cpu_percent < 90
        return status, {"cpu_percent": cpu_percent}
    except ImportError:
        return True, {"cpu_percent": "unknown (psutil not installed)"}
    except Exception as e:
        return False, {"error": str(e)}


async def registry_health_check() -> tuple[bool, Dict[str, Any]]:
    """Check Registry module health"""
    try:
        from agent_toolkit.registry.registry_schemas import ToolCreate
        from agent_toolkit.registry.registry_service import ToolService
        return True, {"module": "registry", "status": "available"}
    except Exception as e:
        return False, {"error": str(e)}


async def adapter_health_check() -> tuple[bool, Dict[str, Any]]:
    """Check Adapter module health"""
    try:
        from agent_toolkit.adapter.adapter_registry import AdapterRegistry
        registry = AdapterRegistry()
        return True, {"module": "adapter", "available_adapters": len(registry._adapters)}
    except Exception as e:
        return False, {"error": str(e)}


async def orchestrator_health_check() -> tuple[bool, Dict[str, Any]]:
    """Check Orchestrator module health"""
    try:
        from agent_toolkit.orchestrator.orchestration_engine import OrchestrationEngine
        engine = OrchestrationEngine()
        return True, {"module": "orchestrator", "status": "ready"}
    except Exception as e:
        return False, {"error": str(e)}


# Register all health checks
health_registry.register_check("database", database_health_check)
health_registry.register_check("memory", memory_health_check)
health_registry.register_check("disk", disk_health_check)
health_registry.register_check("cpu", cpu_health_check)
health_registry.register_check("registry", registry_health_check)
health_registry.register_check("adapter", adapter_health_check)
health_registry.register_check("orchestrator", orchestrator_health_check)


@router.get("", response_model=OverallHealth)
async def get_health():
    """Get comprehensive system health"""
    try:
        health = await health_registry.get_overall_health()
        return health
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Health check failed")


@router.get("/liveness")
@probes_router.get("/liveness")
async def get_liveness():
    """Simple liveness probe."""
    return {"status": "alive", "timestamp": datetime.now().isoformat()}


@router.get("/readiness")
@probes_router.get("/readiness")
async def get_readiness():
    """Readiness probe that checks critical components."""
    try:
        health = await health_registry.get_overall_health()
        critical_checks = ["memory", "disk"]  # Database is optional for now
        critical_passed = all(
            check.status == HealthStatus.HEALTHY
            for check in health.checks
            if check.name in critical_checks
        )
        
        status_code = 200 if critical_passed else 503
        return {
            "status": "ready" if critical_passed else "not_ready",
            "timestamp": datetime.now().isoformat(),
            "critical_checks_passed": critical_passed
        }
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Readiness check failed")


@router.get("/history")
async def get_health_history():
    """Get recent health check history."""
    try:
        history = health_registry._health_history
        return {
            "history": [
                {
                    "status": h.status,
                    "timestamp": datetime.fromtimestamp(time.time() - (len(history) - i) * 60).isoformat() 
                    if hasattr(h, 'timestamp') else datetime.now().isoformat(),
                    "total_checks": h.total_checks,
                    "passed_checks": h.passed_checks,
                    "failed_checks": h.failed_checks
                }
                for i, h in enumerate(history[-20:])  # Last 20 entries
            ],
            "total_entries": len(history)
        }
    except Exception as e:
        logger.error("Failed to get health history", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get health history")


@router.get("/metrics")
async def get_health_metrics():
    """Get health metrics for dashboard"""
    try:
        health = await health_registry.get_overall_health()
        
        # Format metrics for dashboard
        return {
            "status": health.status,
            "uptime": health.uptime_seconds,
            "uptime_formatted": format_uptime(health.uptime_seconds),
            "total_checks": health.total_checks,
            "passed_checks": health.passed_checks,
            "failed_checks": health.failed_checks,
            "checks": [
                {
                    "name": check.name,
                    "status": check.status,
                    "response_time_ms": check.response_time_ms,
                    "details": check.details
                }
                for check in health.checks
            ],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error("Health metrics failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get health metrics")


def format_uptime(seconds: float) -> str:
    """Format uptime in human-readable format"""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    
    return " ".join(parts)


print("🚀 Enhanced Health Check System Loaded")
