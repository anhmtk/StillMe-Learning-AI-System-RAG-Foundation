#!/usr/bin/env python3
"""
AgentDev OpenTelemetry Tracing - SEAL-GRADE
Enterprise-grade distributed tracing with OpenTelemetry
"""

import asyncio
import time
import uuid
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Callable
from contextlib import asynccontextmanager, contextmanager
import functools
import threading

# OpenTelemetry imports
try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    from opentelemetry.context import Context
    from opentelemetry.propagate import inject, extract
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.asyncio import AsyncioInstrumentor
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    # Mock classes for when OpenTelemetry is not available
    class Status:
        OK = "OK"
        ERROR = "ERROR"
    
    class StatusCode:
        OK = "OK"
        ERROR = "ERROR"
        UNSET = "UNSET"

class SpanKind(Enum):
    """Span kinds"""
    INTERNAL = "INTERNAL"
    SERVER = "SERVER"
    CLIENT = "CLIENT"
    PRODUCER = "PRODUCER"
    CONSUMER = "CONSUMER"

class TraceStatus(Enum):
    """Trace status"""
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"
    CANCELLED = "CANCELLED"

@dataclass
class TraceContext:
    """Trace context information"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    baggage: Optional[Dict[str, str]] = None

@dataclass
class SpanAttributes:
    """Span attributes"""
    job_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    tool_name: Optional[str] = None
    model: Optional[str] = None
    status: Optional[str] = None
    error_code: Optional[str] = None
    duration_ms: Optional[float] = None
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

class AgentDevTracer:
    """
    SEAL-GRADE OpenTelemetry Tracer
    
    Features:
    - Distributed tracing
    - Span correlation
    - Performance monitoring
    - Error tracking
    - Context propagation
    - Custom attributes
    - Async support
    """
    
    def __init__(self, 
                 service_name: str = "agentdev",
                 service_version: str = "1.0.0",
                 otlp_endpoint: Optional[str] = None,
                 enable_auto_instrumentation: bool = True):
        self.service_name = service_name
        self.service_version = service_version
        self.otlp_endpoint = otlp_endpoint
        
        # Initialize tracer provider
        self._setup_tracer_provider()
        
        # Get tracer
        if OPENTELEMETRY_AVAILABLE:
            self.tracer = trace.get_tracer(service_name, service_version)
        else:
            self.tracer = self._create_mock_tracer()
        
        # Auto-instrumentation
        if enable_auto_instrumentation and OPENTELEMETRY_AVAILABLE:
            self._setup_auto_instrumentation()
        
        # Thread-local context
        self._context = threading.local()
        
        # Active spans tracking
        self._active_spans: Dict[str, Any] = {}
    
    def _setup_tracer_provider(self):
        """Setup OpenTelemetry tracer provider"""
        if not OPENTELEMETRY_AVAILABLE:
            # Create mock tracer provider
            self._create_mock_tracer()
            return
        
        # Create resource
        resource = Resource.create({
            "service.name": self.service_name,
            "service.version": self.service_version,
            "service.instance.id": str(uuid.uuid4())
        })
        
        # Create tracer provider
        tracer_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(tracer_provider)
        
        # Add OTLP exporter if endpoint provided
        if self.otlp_endpoint:
            otlp_exporter = OTLPSpanExporter(endpoint=self.otlp_endpoint)
            span_processor = BatchSpanProcessor(otlp_exporter)
            tracer_provider.add_span_processor(span_processor)
    
    def _create_mock_tracer(self):
        """Create mock tracer when OpenTelemetry is not available"""
        class MockTracer:
            def start_span(self, name, **kwargs):
                return MockSpan(name)
        
        class MockSpan:
            def __init__(self, name):
                self.name = name
                self.attributes = {}
                self.status = "UNSET"
                self.start_time = time.time()
                self.end_time = None
            
            def set_attribute(self, key, value):
                self.attributes[key] = value
            
            def set_status(self, status):
                self.status = status
            
            def end(self):
                self.end_time = time.time()
        
        return MockTracer()
    
    def _setup_auto_instrumentation(self):
        """Setup auto-instrumentation"""
        try:
            # Instrument HTTP libraries
            RequestsInstrumentor().instrument()
            HTTPXClientInstrumentor().instrument()
            
            # Instrument asyncio
            AsyncioInstrumentor().instrument()
        except Exception as e:
            print(f"Warning: Failed to setup auto-instrumentation: {e}")
    
    def start_span(self, 
                   name: str,
                   kind: SpanKind = SpanKind.INTERNAL,
                   attributes: Optional[SpanAttributes] = None,
                   parent_span: Optional[Any] = None) -> Any:
        """Start a new span"""
        span_kwargs = {
            "kind": getattr(trace.SpanKind, kind.value) if OPENTELEMETRY_AVAILABLE else None
        }
        
        if parent_span:
            span_kwargs["context"] = parent_span.get_span_context() if hasattr(parent_span, 'get_span_context') else None
        
        span = self.tracer.start_span(name, **span_kwargs)
        
        # Set attributes
        if attributes:
            self._set_span_attributes(span, attributes)
        
        # Track active span
        span_id = str(uuid.uuid4())
        self._active_spans[span_id] = span
        
        return span
    
    def _set_span_attributes(self, span: Any, attributes: SpanAttributes):
        """Set span attributes"""
        attrs = asdict(attributes)
        for key, value in attrs.items():
            if value is not None:
                span.set_attribute(f"agentdev.{key}", value)
    
    def end_span(self, span: Any, status: TraceStatus = TraceStatus.SUCCESS, error: Optional[Exception] = None):
        """End a span"""
        if error:
            span.set_status("ERROR")
            span.set_attribute("agentdev.error", True)
            span.set_attribute("agentdev.error_message", str(error))
        else:
            span.set_status("OK")
        
        span.end()
    
    @contextmanager
    def span(self, 
             name: str,
             kind: SpanKind = SpanKind.INTERNAL,
             attributes: Optional[SpanAttributes] = None,
             parent_span: Optional[Any] = None):
        """Context manager for spans"""
        span = self.start_span(name, kind, attributes, parent_span)
        try:
            yield span
        except Exception as e:
            self.end_span(span, TraceStatus.ERROR, e)
            raise
        else:
            self.end_span(span, TraceStatus.SUCCESS)
    
    @asynccontextmanager
    async def async_span(self, 
                        name: str,
                        kind: SpanKind = SpanKind.INTERNAL,
                        attributes: Optional[SpanAttributes] = None,
                        parent_span: Optional[Any] = None):
        """Async context manager for spans"""
        span = self.start_span(name, kind, attributes, parent_span)
        try:
            yield span
        except Exception as e:
            self.end_span(span, TraceStatus.ERROR, e)
            raise
        else:
            self.end_span(span, TraceStatus.SUCCESS)
    
    def trace_function(self, 
                      name: Optional[str] = None,
                      kind: SpanKind = SpanKind.INTERNAL,
                      attributes: Optional[SpanAttributes] = None):
        """Decorator to trace function execution"""
        def decorator(func: Callable):
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                span_name = name or f"{func.__module__}.{func.__name__}"
                with self.span(span_name, kind, attributes):
                    return func(*args, **kwargs)
            
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                span_name = name or f"{func.__module__}.{func.__name__}"
                async with self.async_span(span_name, kind, attributes):
                    return await func(*args, **kwargs)
            
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def create_trace_context(self, 
                           trace_id: Optional[str] = None,
                           span_id: Optional[str] = None,
                           parent_span_id: Optional[str] = None,
                           baggage: Optional[Dict[str, str]] = None) -> TraceContext:
        """Create trace context"""
        return TraceContext(
            trace_id=trace_id or str(uuid.uuid4()),
            span_id=span_id or str(uuid.uuid4()),
            parent_span_id=parent_span_id,
            baggage=baggage or {}
        )
    
    def inject_trace_context(self, headers: Dict[str, str], trace_context: TraceContext):
        """Inject trace context into headers"""
        if OPENTELEMETRY_AVAILABLE:
            # Create context with trace info
            context = Context()
            inject(headers, context)
        else:
            # Mock injection
            headers["trace-id"] = trace_context.trace_id
            headers["span-id"] = trace_context.span_id
            if trace_context.parent_span_id:
                headers["parent-span-id"] = trace_context.parent_span_id
    
    def extract_trace_context(self, headers: Dict[str, str]) -> Optional[TraceContext]:
        """Extract trace context from headers"""
        if OPENTELEMETRY_AVAILABLE:
            context = extract(headers)
            # Extract trace info from context
            # This is a simplified version
            trace_id = headers.get("trace-id")
            span_id = headers.get("span-id")
            parent_span_id = headers.get("parent-span-id")
            
            if trace_id and span_id:
                return TraceContext(
                    trace_id=trace_id,
                    span_id=span_id,
                    parent_span_id=parent_span_id
                )
        else:
            # Mock extraction
            trace_id = headers.get("trace-id")
            span_id = headers.get("span-id")
            parent_span_id = headers.get("parent-span-id")
            
            if trace_id and span_id:
                return TraceContext(
                    trace_id=trace_id,
                    span_id=span_id,
                    parent_span_id=parent_span_id
                )
        
        return None
    
    def get_current_span(self) -> Optional[Any]:
        """Get current active span"""
        if OPENTELEMETRY_AVAILABLE:
            return trace.get_current_span()
        else:
            # Return the most recent active span
            if self._active_spans:
                return list(self._active_spans.values())[-1]
            return None
    
    def get_trace_id(self) -> Optional[str]:
        """Get current trace ID"""
        span = self.get_current_span()
        if span and hasattr(span, 'get_span_context'):
            return span.get_span_context().trace_id
        return None
    
    def get_span_id(self) -> Optional[str]:
        """Get current span ID"""
        span = self.get_current_span()
        if span and hasattr(span, 'get_span_context'):
            return span.get_span_context().span_id
        return None

# Global tracer instance
_global_tracer: Optional[AgentDevTracer] = None

def get_tracer() -> AgentDevTracer:
    """Get global tracer instance"""
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = AgentDevTracer()
    return _global_tracer

def set_global_tracer(tracer: AgentDevTracer):
    """Set global tracer instance"""
    global _global_tracer
    _global_tracer = tracer

# Convenience functions
def start_span(name: str, **kwargs) -> Any:
    """Start a new span"""
    return get_tracer().start_span(name, **kwargs)

def span(name: str, **kwargs):
    """Context manager for spans"""
    return get_tracer().span(name, **kwargs)

def async_span(name: str, **kwargs):
    """Async context manager for spans"""
    return get_tracer().async_span(name, **kwargs)

def trace_function(name: Optional[str] = None, **kwargs):
    """Decorator to trace function execution"""
    return get_tracer().trace_function(name, **kwargs)

def get_current_span() -> Optional[Any]:
    """Get current active span"""
    return get_tracer().get_current_span()

def get_trace_id() -> Optional[str]:
    """Get current trace ID"""
    return get_tracer().get_trace_id()

def get_span_id() -> Optional[str]:
    """Get current span ID"""
    return get_tracer().get_span_id()
