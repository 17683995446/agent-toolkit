"""API routes for Observability."""

from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Response
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from agent_toolkit.observability.metrics_collector import metrics_collector
from agent_toolkit.observability.distributed_tracing import tracing_manager
from agent_toolkit.observability.alert_manager import (
    get_alert_manager,
    AlertSeverity,
    AlertStatus,
)

# 创建统一的路由
router = APIRouter(prefix="/api/v1", tags=["observability"])

metrics_router = APIRouter(prefix="/metrics", tags=["metrics"])
tracing_router = APIRouter(prefix="/tracing", tags=["tracing"])
alerts_router = APIRouter(prefix="/alerts", tags=["alerts"])


@metrics_router.get("/", response_class=PlainTextResponse)
async def prometheus_metrics():
    """Prometheus metrics endpoint."""
    collector = metrics_collector()
    return collector.get_metrics()


@metrics_router.get("/info")
async def metrics_info():
    """Get metrics information."""
    collector = metrics_collector()
    return {
        "success": True,
        "metrics": "Prometheus metrics available at /metrics endpoint",
        "timestamp": datetime.utcnow().isoformat(),
    }


# 挂载子路由到统一路由
router.include_router(metrics_router)
router.include_router(tracing_router)
router.include_router(alerts_router)


class AlertCreateRequest(BaseModel):
    """Create alert request."""
    name: str = Field(..., description="Alert name")
    severity: AlertSeverity = Field(..., description="Alert severity")
    message: str = Field(..., description="Alert message")
    source: str = Field(..., description="Alert source")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


@alerts_router.post("/", status_code=201)
async def create_alert(request: AlertCreateRequest):
    """Create a new alert."""
    manager = get_alert_manager()
    
    alert = await manager.create_alert(
        name=request.name,
        severity=request.severity,
        message=request.message,
        source=request.source,
        metadata=request.metadata,
    )
    
    return {
        "alert_id": alert.alert_id,
        "status": alert.status.value,
        "created_at": alert.created_at.isoformat(),
    }


@alerts_router.get("/")
async def list_alerts(
    status: Optional[AlertStatus] = None,
    severity: Optional[AlertSeverity] = None,
):
    """List alerts."""
    manager = get_alert_manager()
    
    alerts = await manager.list_alerts(
        status=status,
        severity=severity,
    )
    
    return {
        "alerts": [
            {
                "alert_id": a.alert_id,
                "name": a.name,
                "severity": a.severity.value,
                "status": a.status.value,
                "message": a.message,
                "source": a.source,
                "created_at": a.created_at.isoformat(),
            }
            for a in alerts
        ],
        "total": len(alerts),
    }


@alerts_router.get("/{alert_id}")
async def get_alert(alert_id: str):
    """Get alert details."""
    manager = get_alert_manager()
    alert = await manager.get_alert(alert_id)
    
    if not alert:
        return {"error": "Alert not found"}, 404
    
    return {
        "alert_id": alert.alert_id,
        "name": alert.name,
        "severity": alert.severity.value,
        "status": alert.status.value,
        "message": alert.message,
        "source": alert.source,
        "created_at": alert.created_at.isoformat(),
        "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
        "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
        "metadata": alert.metadata,
    }


@alerts_router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Acknowledge an alert."""
    manager = get_alert_manager()
    success = await manager.acknowledge_alert(alert_id)
    
    return {
        "alert_id": alert_id,
        "acknowledged": success,
    }


@alerts_router.post("/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """Resolve an alert."""
    manager = get_alert_manager()
    success = await manager.resolve_alert(alert_id)
    
    return {
        "alert_id": alert_id,
        "resolved": success,
    }


@alerts_router.get("/active/count")
async def get_active_alert_count():
    """Get count of active alerts."""
    manager = get_alert_manager()
    alerts = await manager.get_active_alerts()
    
    by_severity = {}
    for alert in alerts:
        severity = alert.severity.value
        by_severity[severity] = by_severity.get(severity, 0) + 1
    
    return {
        "total": len(alerts),
        "by_severity": by_severity,
    }


@tracing_router.get("/status")
async def tracing_status():
    """Get tracing status."""
    manager = tracing_manager()
    
    return {
        "success": True,
        "enabled": True,
        "service_name": "agent-toolkit",
        "version": "0.1.0",
    }


@tracing_router.post("/span")
async def create_span(
    name: str,
    attributes: Optional[Dict[str, Any]] = None,
):
    """Create a new span (for testing)."""
    manager = tracing_manager()
    
    with manager.start_span(name, attributes=attributes) as span:
        pass
    
    return {"success": True, "status": "span_created", "name": name}
