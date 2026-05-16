"""Lifecycle management for tool execution."""

import asyncio
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from agent_toolkit.shared.structured_logging import LoggerMixin


class LifecycleEvent(str, Enum):
    """Lifecycle events."""
    PRE_INITIALIZE = "pre_initialize"
    POST_INITIALIZE = "post_initialize"
    PRE_EXECUTE = "pre_execute"
    POST_EXECUTE = "post_execute"
    PRE_CLEANUP = "pre_cleanup"
    POST_CLEANUP = "post_cleanup"
    ON_ERROR = "on_error"
    ON_TIMEOUT = "on_timeout"


@dataclass
class LifecycleHook:
    """A lifecycle hook."""
    event: LifecycleEvent
    callback: Callable
    priority: int = 0
    timeout_seconds: Optional[int] = None
    enabled: bool = True


@dataclass
class LifecycleContext:
    """Context passed to lifecycle hooks."""
    execution_id: str
    tool_id: str
    event: LifecycleEvent
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class LifecycleManager(LoggerMixin):
    """Manager for execution lifecycle hooks."""

    def __init__(self):
        self._hooks: Dict[LifecycleEvent, List[LifecycleHook]] = {
            event: [] for event in LifecycleEvent
        }
        self._lock = asyncio.Lock()

    def register_hook(
        self,
        event: LifecycleEvent,
        callback: Callable,
        priority: int = 0,
        timeout_seconds: Optional[int] = None
    ) -> None:
        """Register a lifecycle hook."""
        hook = LifecycleHook(
            event=event,
            callback=callback,
            priority=priority,
            timeout_seconds=timeout_seconds
        )

        self._hooks[event].append(hook)
        self._hooks[event].sort(key=lambda h: h.priority, reverse=True)

        self.logger.info(
            "lifecycle_hook_registered",
            event=event.value,
            priority=priority
        )

    def unregister_hook(self, event: LifecycleEvent, callback: Callable) -> bool:
        """Unregister a lifecycle hook."""
        hooks = self._hooks.get(event, [])
        for i, hook in enumerate(hooks):
            if hook.callback == callback:
                hooks.pop(i)
                self.logger.info("lifecycle_hook_unregistered", event=event.value)
                return True
        return False

    async def trigger_event(
        self,
        event: LifecycleEvent,
        context: LifecycleContext
    ) -> List[Any]:
        """Trigger a lifecycle event."""
        hooks = self._hooks.get(event, [])
        results = []

        enabled_hooks = [h for h in hooks if h.enabled]

        if not enabled_hooks:
            return results

        self.logger.debug(
            "lifecycle_event_triggered",
            event=event.value,
            hook_count=len(enabled_hooks)
        )

        for hook in enabled_hooks:
            try:
                result = await self._execute_hook(hook, context)
                results.append(result)
            except Exception as e:
                self.logger.error(
                    "lifecycle_hook_error",
                    event=event.value,
                    hook_priority=hook.priority,
                    error=str(e)
                )

        return results

    async def _execute_hook(
        self,
        hook: LifecycleHook,
        context: LifecycleContext
    ) -> Any:
        """Execute a single hook."""
        if hook.timeout_seconds:
            try:
                result = await asyncio.wait_for(
                    hook.callback(context),
                    timeout=hook.timeout_seconds
                )
            except asyncio.TimeoutError:
                self.logger.warning(
                    "lifecycle_hook_timeout",
                    event=context.event.value,
                    timeout=hook.timeout_seconds
                )
                return None
        else:
            result = await hook.callback(context)

        return result

    async def trigger_pre_initialize(self, execution_id: str, tool_id: str) -> List[Any]:
        """Trigger pre-initialize event."""
        context = LifecycleContext(
            execution_id=execution_id,
            tool_id=tool_id,
            event=LifecycleEvent.PRE_INITIALIZE
        )
        return await self.trigger_event(LifecycleEvent.PRE_INITIALIZE, context)

    async def trigger_post_initialize(self, execution_id: str, tool_id: str) -> List[Any]:
        """Trigger post-initialize event."""
        context = LifecycleContext(
            execution_id=execution_id,
            tool_id=tool_id,
            event=LifecycleEvent.POST_INITIALIZE
        )
        return await self.trigger_event(LifecycleEvent.POST_INITIALIZE, context)

    async def trigger_pre_execute(
        self,
        execution_id: str,
        tool_id: str,
        input_data: Any
    ) -> List[Any]:
        """Trigger pre-execute event."""
        context = LifecycleContext(
            execution_id=execution_id,
            tool_id=tool_id,
            event=LifecycleEvent.PRE_EXECUTE,
            metadata={"input_data": input_data}
        )
        return await self.trigger_event(LifecycleEvent.PRE_EXECUTE, context)

    async def trigger_post_execute(
        self,
        execution_id: str,
        tool_id: str,
        output_data: Any
    ) -> List[Any]:
        """Trigger post-execute event."""
        context = LifecycleContext(
            execution_id=execution_id,
            tool_id=tool_id,
            event=LifecycleEvent.POST_EXECUTE,
            metadata={"output_data": output_data}
        )
        return await self.trigger_event(LifecycleEvent.POST_EXECUTE, context)

    async def trigger_on_error(
        self,
        execution_id: str,
        tool_id: str,
        error: Exception
    ) -> List[Any]:
        """Trigger on-error event."""
        context = LifecycleContext(
            execution_id=execution_id,
            tool_id=tool_id,
            event=LifecycleEvent.ON_ERROR,
            metadata={"error": str(error), "error_type": type(error).__name__}
        )
        return await self.trigger_event(LifecycleEvent.ON_ERROR, context)

    async def trigger_on_timeout(
        self,
        execution_id: str,
        tool_id: str,
        timeout_seconds: int
    ) -> List[Any]:
        """Trigger on-timeout event."""
        context = LifecycleContext(
            execution_id=execution_id,
            tool_id=tool_id,
            event=LifecycleEvent.ON_TIMEOUT,
            metadata={"timeout_seconds": timeout_seconds}
        )
        return await self.trigger_event(LifecycleEvent.ON_TIMEOUT, context)

    async def trigger_pre_cleanup(self, execution_id: str, tool_id: str) -> List[Any]:
        """Trigger pre-cleanup event."""
        context = LifecycleContext(
            execution_id=execution_id,
            tool_id=tool_id,
            event=LifecycleEvent.PRE_CLEANUP
        )
        return await self.trigger_event(LifecycleEvent.PRE_CLEANUP, context)

    async def trigger_post_cleanup(self, execution_id: str, tool_id: str) -> List[Any]:
        """Trigger post-cleanup event."""
        context = LifecycleContext(
            execution_id=execution_id,
            tool_id=tool_id,
            event=LifecycleEvent.POST_CLEANUP
        )
        return await self.trigger_event(LifecycleEvent.POST_CLEANUP, context)

    def get_hooks_for_event(self, event: LifecycleEvent) -> List[Dict[str, Any]]:
        """Get all hooks registered for an event."""
        hooks = self._hooks.get(event, [])
        return [
            {
                "priority": h.priority,
                "timeout_seconds": h.timeout_seconds,
                "enabled": h.enabled,
                "callback_name": h.callback.__name__ if hasattr(h.callback, "__name__") else str(h.callback)
            }
            for h in hooks
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get lifecycle manager statistics."""
        return {
            event.value: len(hooks)
            for event, hooks in self._hooks.items()
        }


_global_lifecycle_manager: Optional[LifecycleManager] = None


def get_lifecycle_manager() -> LifecycleManager:
    """Get the global lifecycle manager instance."""
    global _global_lifecycle_manager
    if _global_lifecycle_manager is None:
        _global_lifecycle_manager = LifecycleManager()
    return _global_lifecycle_manager
