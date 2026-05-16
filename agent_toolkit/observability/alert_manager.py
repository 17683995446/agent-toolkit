"""Alert management for Agent Toolkit."""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio

from agent_toolkit.shared.structured_logging import get_logger


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertStatus(str, Enum):
    """Alert status."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


@dataclass
class Alert:
    """Alert definition."""
    alert_id: str
    name: str
    severity: AlertSeverity
    message: str
    source: str
    status: AlertStatus = AlertStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)


@dataclass
class AlertRule:
    """Alert rule definition."""
    rule_id: str
    name: str
    condition: Callable[[Dict[str, Any]], bool]
    severity: AlertSeverity
    message_template: str
    enabled: bool = True
    cooldown_seconds: int = 300


class AlertManager:
    """Manages alerts for Agent Toolkit."""
    
    def __init__(self):
        self._alerts: Dict[str, Alert] = {}
        self._rules: Dict[str, AlertRule] = {}
        self._handlers: List[Callable[[Alert], None]] = []
        self._lock = asyncio.Lock()
        self._logger = get_logger("observability.alerts")
    
    def register_handler(self, handler: Callable[[Alert], None]) -> None:
        """Register an alert handler."""
        self._handlers.append(handler)
        self._logger.info("alert_handler_registered")
    
    def add_rule(self, rule: AlertRule) -> None:
        """Add an alert rule."""
        self._rules[rule.rule_id] = rule
        self._logger.info("alert_rule_added", rule_id=rule.rule_id)
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove an alert rule."""
        if rule_id in self._rules:
            del self._rules[rule_id]
            return True
        return False
    
    async def create_alert(
        self,
        name: str,
        severity: AlertSeverity,
        message: str,
        source: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Alert:
        """Create a new alert."""
        alert_id = f"alert-{datetime.utcnow().timestamp()}"
        
        alert = Alert(
            alert_id=alert_id,
            name=name,
            severity=severity,
            message=message,
            source=source,
            metadata=metadata or {},
        )
        
        async with self._lock:
            self._alerts[alert_id] = alert
        
        for handler in self._handlers:
            try:
                handler(alert)
            except Exception as e:
                self._logger.error(
                    "alert_handler_error",
                    handler=str(handler),
                    error=str(e)
                )
        
        self._logger.warning(
            "alert_created",
            alert_id=alert_id,
            name=name,
            severity=severity.value,
            source=source,
        )
        
        return alert
    
    async def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        async with self._lock:
            if alert_id in self._alerts:
                alert = self._alerts[alert_id]
                alert.status = AlertStatus.ACKNOWLEDGED
                alert.acknowledged_at = datetime.utcnow()
                
                self._logger.info("alert_acknowledged", alert_id=alert_id)
                return True
        return False
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        async with self._lock:
            if alert_id in self._alerts:
                alert = self._alerts[alert_id]
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = datetime.utcnow()
                
                self._logger.info("alert_resolved", alert_id=alert_id)
                return True
        return False
    
    async def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get an alert by ID."""
        return self._alerts.get(alert_id)
    
    async def list_alerts(
        self,
        status: Optional[AlertStatus] = None,
        severity: Optional[AlertSeverity] = None,
        source: Optional[str] = None,
    ) -> List[Alert]:
        """List alerts with optional filtering."""
        alerts = list(self._alerts.values())
        
        if status:
            alerts = [a for a in alerts if a.status == status]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if source:
            alerts = [a for a in alerts if a.source == source]
        
        return sorted(alerts, key=lambda a: a.created_at, reverse=True)
    
    async def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        return await self.list_alerts(status=AlertStatus.ACTIVE)
    
    async def evaluate_rules(self, metrics: Dict[str, Any]) -> List[Alert]:
        """Evaluate all alert rules against current metrics."""
        created_alerts = []
        
        for rule in self._rules.values():
            if not rule.enabled:
                continue
            
            try:
                if rule.condition(metrics):
                    alert = await self.create_alert(
                        name=rule.name,
                        severity=rule.severity,
                        message=rule.message_template.format(**metrics),
                        source=f"rule:{rule.rule_id}",
                        metadata={"rule_id": rule.rule_id},
                    )
                    created_alerts.append(alert)
            
            except Exception as e:
                self._logger.error(
                    "rule_evaluation_error",
                    rule_id=rule.rule_id,
                    error=str(e)
                )
        
        return created_alerts
    
    def create_predefined_rules(self) -> None:
        """Create predefined alert rules."""
        self.add_rule(AlertRule(
            rule_id="high_error_rate",
            name="High Error Rate",
            condition=lambda m: m.get("error_rate", 0) > 0.05,
            severity=AlertSeverity.HIGH,
            message_template="Error rate is {error_rate:.2%}, exceeding 5% threshold",
        ))
        
        self.add_rule(AlertRule(
            rule_id="high_execution_time",
            name="High Execution Time",
            condition=lambda m: m.get("avg_execution_time_ms", 0) > 10000,
            severity=AlertSeverity.MEDIUM,
            message_template="Average execution time is {avg_execution_time_ms:.0f}ms",
        ))
        
        self.add_rule(AlertRule(
            rule_id="resource_limit",
            name="Resource Limit Exceeded",
            condition=lambda m: m.get("memory_usage_percent", 0) > 90,
            severity=AlertSeverity.CRITICAL,
            message_template="Memory usage at {memory_usage_percent:.1f}%",
        ))
        
        self.add_rule(AlertRule(
            rule_id="execution_queue_full",
            name="Execution Queue Full",
            condition=lambda m: m.get("queue_size", 0) > m.get("max_queue_size", 100),
            severity=AlertSeverity.HIGH,
            message_template="Execution queue size ({queue_size}) exceeds max ({max_queue_size})",
        ))


_global_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """Get the global alert manager."""
    global _global_alert_manager
    if _global_alert_manager is None:
        _global_alert_manager = AlertManager()
    return _global_alert_manager
