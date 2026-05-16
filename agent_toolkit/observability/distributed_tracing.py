"""Distributed tracing with OpenTelemetry."""

import time
from typing import Any, Dict, Optional
from contextvars import ContextVar
from functools import wraps

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace import Span, Status, StatusCode
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from agent_toolkit.shared.structured_logging import LoggerMixin


trace_context: ContextVar[Optional[Span]] = ContextVar("trace_context", default=None)


class TracingManager(LoggerMixin):
    """Manager for distributed tracing."""

    def __init__(self):
        self._tracer: Optional[trace.Tracer] = None
        self._provider: Optional[TracerProvider] = None
        self._propagator = TraceContextTextMapPropagator()
        self._initialized = False

    def initialize(
        self,
        service_name: str = "agent-toolkit",
        service_version: str = "0.1.0",
        exporter_type: str = "console",
        exporter_endpoint: Optional[str] = None
    ) -> None:
        """Initialize the tracing provider."""
        if self._initialized:
            self.logger.warning("tracing_already_initialized")
            return

        resource = Resource.create({
            "service.name": service_name,
            "service.version": service_version,
        })

        self._provider = TracerProvider(resource=resource)

        if exporter_type == "console":
            exporter = ConsoleSpanExporter()
        elif exporter_type == "otlp" and exporter_endpoint:
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
                exporter = OTLPSpanExporter(endpoint=exporter_endpoint)
            except ImportError:
                self.logger.warning("otlp_exporter_not_available")
                exporter = ConsoleSpanExporter()
        else:
            exporter = ConsoleSpanExporter()

        self._provider.add_span_processor(BatchSpanProcessor(exporter))

        trace.set_tracer_provider(self._provider)
        self._tracer = trace.get_tracer(service_name)

        self._initialized = True

        self.logger.info(
            "tracing_initialized",
            service_name=service_name,
            exporter_type=exporter_type
        )

    def get_tracer(self) -> trace.Tracer:
        """Get the tracer instance."""
        if not self._tracer:
            self.initialize()
        return self._tracer

    def start_span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        parent_span: Optional[Span] = None
    ) -> Span:
        """Start a new span."""
        tracer = self.get_tracer()

        span_kwargs = {}
        if parent_span:
            span_kwargs["parent"] = parent_span

        span = tracer.start_span(name, **span_kwargs)

        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)

        return span

    def end_span(self, span: Span, status: str = "ok", error: Optional[str] = None) -> None:
        """End a span."""
        if error:
            span.set_status(Status(StatusCode.ERROR, error))
            span.record_exception(error)
        else:
            span.set_status(Status(StatusCode.OK))

        span.end()

    def create_span_context(self) -> Dict[str, str]:
        """Create a trace context for propagation."""
        span = trace_context.get()
        if span:
            return self._propagator.inject({})
        return {}

    def extract_span_context(self, headers: Dict[str, str]) -> Optional[Span]:
        """Extract span context from headers."""
        context = self._propagator.extract(carrier=headers)
        return context

    def get_current_span(self) -> Optional[Span]:
        """Get the current active span."""
        return trace.get_current_span()

    def shutdown(self) -> None:
        """Shutdown the tracing provider."""
        if self._provider:
            self._provider.shutdown()
            self._initialized = False
            self.logger.info("tracing_shutdown")


_global_tracing_manager: Optional[TracingManager] = None


def tracing_manager() -> TracingManager:
    """Get the global tracing manager instance."""
    global _global_tracing_manager
    if _global_tracing_manager is None:
        _global_tracing_manager = TracingManager()
    return _global_tracing_manager


def traced(
    name: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None
):
    """Decorator to trace function execution."""
    def decorator(func):
        span_name = name or func.__name__

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            manager = tracing_manager()
            tracer = manager.get_tracer()

            with tracer.start_as_current_span(span_name) as span:
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                span.set_attribute("function.name", func.__name__)

                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            manager = tracing_manager()
            tracer = manager.get_tracer()

            with tracer.start_as_current_span(span_name) as span:
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                span.set_attribute("function.name", func.__name__)

                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


class SpanContext:
    """Context manager for span creation."""

    def __init__(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        manager: Optional[TracingManager] = None
    ):
        self.name = name
        self.attributes = attributes or {}
        self.manager = manager or tracing_manager()
        self.span: Optional[Span] = None

    def __enter__(self) -> "SpanContext":
        self.span = self.manager.start_span(self.name, self.attributes)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.span:
            if exc_val:
                self.span.set_status(Status(StatusCode.ERROR, str(exc_val)))
                self.span.record_exception(exc_val)
            else:
                self.span.set_status(Status(StatusCode.OK))
            self.span.end()
        return False

    async def __aenter__(self) -> "SpanContext":
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self.__exit__(exc_type, exc_val, exc_tb)
