#!/usr/bin/env python3
"""
StillMe AgentDev - Distributed Tracing
Enterprise-grade distributed tracing and correlation
"""

import asyncio
import contextvars
import functools
import json
import threading
import time
import uuid
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import aiofiles


class SpanStatus(Enum):
    """Span status values"""
    OK = "OK"
    ERROR = "ERROR"
    CANCELLED = "CANCELLED"
    UNKNOWN = "UNKNOWN"

class SpanKind(Enum):
    """Span kinds"""
    CLIENT = "CLIENT"
    SERVER = "SERVER"
    PRODUCER = "PRODUCER"
    CONSUMER = "CONSUMER"
    INTERNAL = "INTERNAL"

@dataclass
class SpanContext:
    """Span context for distributed tracing"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    trace_flags: int = 1
    trace_state: Optional[str] = None

@dataclass
class Span:
    """Distributed tracing span"""
    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    name: str
    kind: SpanKind
    start_time: float
    end_time: Optional[float]
    status: SpanStatus
    attributes: Dict[str, Any]
    events: List[Dict[str, Any]]
    links: List[Dict[str, Any]]
    resource: Dict[str, Any]

@dataclass
class Trace:
    """Complete trace with all spans"""
    trace_id: str
    spans: List[Span]
    start_time: float
    end_time: float
    duration: float
    root_span: Optional[Span]
    status: SpanStatus

# Context variables for tracing
current_span_context = contextvars.ContextVar('span_context', default=None)
current_trace_id = contextvars.ContextVar('trace_id', default=None)

class DistributedTracer:
    """Enterprise distributed tracing system"""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.traces: Dict[str, Trace] = {}
        self.spans: Dict[str, Span] = {}
        self.active_spans: Dict[str, Span] = {}
        self.exporters = []
        self.sampling_rate = self.config.get('sampling_rate', 1.0)
        self.max_traces = self.config.get('max_traces', 10000)
        self.lock = threading.RLock()

    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load tracing configuration"""
        if config_path:
            config_file = Path(config_path)
        else:
            config_file = Path("agent-dev/config/distributed_tracing.yaml")

        if config_file.exists():
            import yaml
            with open(config_file) as f:
                return yaml.safe_load(f)
        else:
            return {
                'sampling_rate': 1.0,
                'max_traces': 10000,
                'exporters': {
                    'jaeger': {
                        'enabled': False,
                        'endpoint': 'http://localhost:14268/api/traces'
                    },
                    'zipkin': {
                        'enabled': False,
                        'endpoint': 'http://localhost:9411/api/v2/spans'
                    },
                    'file': {
                        'enabled': True,
                        'path': '.agentdev/traces.json'
                    }
                },
                'attributes': {
                    'service_name': 'agentdev',
                    'service_version': '1.0.0',
                    'environment': 'development'
                }
            }

    def _should_sample(self) -> bool:
        """Determine if trace should be sampled"""
        import random
        return random.random() < self.sampling_rate

    def _generate_trace_id(self) -> str:
        """Generate unique trace ID"""
        return format(uuid.uuid4().int, '032x')

    def _generate_span_id(self) -> str:
        """Generate unique span ID"""
        return format(uuid.uuid4().int, '016x')

    def start_trace(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> str:
        """Start a new trace"""
        if not self._should_sample():
            return None

        trace_id = self._generate_trace_id()
        span_id = self._generate_span_id()

        span = Span(
            span_id=span_id,
            trace_id=trace_id,
            parent_span_id=None,
            name=name,
            kind=SpanKind.INTERNAL,
            start_time=time.time(),
            end_time=None,
            status=SpanStatus.UNKNOWN,
            attributes=attributes or {},
            events=[],
            links=[],
            resource=self.config['attributes']
        )

        with self.lock:
            self.spans[span_id] = span
            self.active_spans[span_id] = span

        # Set context variables
        current_trace_id.set(trace_id)
        current_span_context.set(SpanContext(
            trace_id=trace_id,
            span_id=span_id
        ))

        print(f"🔍 Trace started: {trace_id} - {name}")
        return trace_id

    def start_span(self, name: str, kind: SpanKind = SpanKind.INTERNAL,
                  attributes: Optional[Dict[str, Any]] = None,
                  parent_span_id: Optional[str] = None) -> str:
        """Start a new span"""
        if not self._should_sample():
            return None

        # Get current context
        current_context = current_span_context.get()
        if not current_context and not parent_span_id:
            # Start new trace
            trace_id = self.start_trace(name, attributes)
            return current_span_context.get().span_id

        span_id = self._generate_span_id()
        trace_id = current_context.trace_id if current_context else parent_span_id

        # Determine parent
        if parent_span_id:
            parent_span = self.spans.get(parent_span_id)
            if parent_span:
                trace_id = parent_span.trace_id
        elif current_context:
            parent_span_id = current_context.span_id

        span = Span(
            span_id=span_id,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            name=name,
            kind=kind,
            start_time=time.time(),
            end_time=None,
            status=SpanStatus.UNKNOWN,
            attributes=attributes or {},
            events=[],
            links=[],
            resource=self.config['attributes']
        )

        with self.lock:
            self.spans[span_id] = span
            self.active_spans[span_id] = span

        # Update context
        current_span_context.set(SpanContext(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id
        ))

        print(f"🔍 Span started: {span_id} - {name}")
        return span_id

    def end_span(self, span_id: str, status: SpanStatus = SpanStatus.OK,
                attributes: Optional[Dict[str, Any]] = None):
        """End a span"""
        with self.lock:
            span = self.spans.get(span_id)
            if not span:
                return

            span.end_time = time.time()
            span.status = status

            if attributes:
                span.attributes.update(attributes)

            # Remove from active spans
            if span_id in self.active_spans:
                del self.active_spans[span_id]

            # Add to trace
            if span.trace_id not in self.traces:
                self.traces[span.trace_id] = Trace(
                    trace_id=span.trace_id,
                    spans=[],
                    start_time=span.start_time,
                    end_time=span.end_time,
                    duration=span.end_time - span.start_time,
                    root_span=None,
                    status=span.status
                )

            trace = self.traces[span.trace_id]
            trace.spans.append(span)

            # Update trace timing
            if span.start_time < trace.start_time:
                trace.start_time = span.start_time
            if span.end_time > trace.end_time:
                trace.end_time = span.end_time
                trace.duration = trace.end_time - trace.start_time

            # Set root span
            if not span.parent_span_id:
                trace.root_span = span

            # Update trace status
            if span.status == SpanStatus.ERROR:
                trace.status = SpanStatus.ERROR

        print(f"🔍 Span ended: {span_id} - {status.value}")

    def add_span_event(self, span_id: str, name: str,
                      attributes: Optional[Dict[str, Any]] = None):
        """Add event to span"""
        with self.lock:
            span = self.spans.get(span_id)
            if not span:
                return

            event = {
                'name': name,
                'timestamp': time.time(),
                'attributes': attributes or {}
            }
            span.events.append(event)

    def add_span_attribute(self, span_id: str, key: str, value: Any):
        """Add attribute to span"""
        with self.lock:
            span = self.spans.get(span_id)
            if not span:
                return

            span.attributes[key] = value

    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Get complete trace by ID"""
        with self.lock:
            return self.traces.get(trace_id)

    def get_span(self, span_id: str) -> Optional[Span]:
        """Get span by ID"""
        with self.lock:
            return self.spans.get(span_id)

    def get_active_spans(self) -> List[Span]:
        """Get all active spans"""
        with self.lock:
            return list(self.active_spans.values())

    def get_trace_statistics(self) -> Dict[str, Any]:
        """Get tracing statistics"""
        with self.lock:
            total_traces = len(self.traces)
            total_spans = len(self.spans)
            active_spans = len(self.active_spans)

            # Count spans by status
            spans_by_status = {}
            for span in self.spans.values():
                status = span.status.value
                spans_by_status[status] = spans_by_status.get(status, 0) + 1

            # Count traces by status
            traces_by_status = {}
            for trace in self.traces.values():
                status = trace.status.value
                traces_by_status[status] = traces_by_status.get(status, 0) + 1

            # Calculate average duration
            durations = [trace.duration for trace in self.traces.values() if trace.duration > 0]
            avg_duration = sum(durations) / len(durations) if durations else 0

            return {
                'total_traces': total_traces,
                'total_spans': total_spans,
                'active_spans': active_spans,
                'spans_by_status': spans_by_status,
                'traces_by_status': traces_by_status,
                'average_duration': avg_duration,
                'sampling_rate': self.sampling_rate
            }

    async def export_traces(self):
        """Export traces to configured exporters"""
        with self.lock:
            traces_to_export = list(self.traces.values())

        for exporter in self.exporters:
            try:
                await exporter.export(traces_to_export)
            except Exception as e:
                print(f"⚠️ Export error: {e}")

    async def cleanup_old_traces(self):
        """Clean up old traces to prevent memory issues"""
        with self.lock:
            if len(self.traces) > self.max_traces:
                # Remove oldest traces
                sorted_traces = sorted(
                    self.traces.items(),
                    key=lambda x: x[1].start_time
                )

                traces_to_remove = sorted_traces[:len(self.traces) - self.max_traces]

                for trace_id, _ in traces_to_remove:
                    trace = self.traces[trace_id]

                    # Remove associated spans
                    for span in trace.spans:
                        if span.span_id in self.spans:
                            del self.spans[span.span_id]

                    del self.traces[trace_id]

                print(f"🧹 Cleaned up {len(traces_to_remove)} old traces")

# Global tracer instance
tracer = DistributedTracer()

# Decorators for automatic tracing
def trace_function(name: Optional[str] = None, kind: SpanKind = SpanKind.INTERNAL):
    """Decorator to automatically trace function execution"""
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            span_name = name or f"{func.__module__}.{func.__name__}"
            span_id = tracer.start_span(span_name, kind)

            try:
                result = await func(*args, **kwargs)
                tracer.end_span(span_id, SpanStatus.OK)
                return result
            except Exception as e:
                tracer.end_span(span_id, SpanStatus.ERROR, {'error': str(e)})
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            span_name = name or f"{func.__module__}.{func.__name__}"
            span_id = tracer.start_span(span_name, kind)

            try:
                result = func(*args, **kwargs)
                tracer.end_span(span_id, SpanStatus.OK)
                return result
            except Exception as e:
                tracer.end_span(span_id, SpanStatus.ERROR, {'error': str(e)})
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator

def trace_span(name: str, kind: SpanKind = SpanKind.INTERNAL):
    """Context manager for tracing spans"""
    class TraceSpan:
        def __init__(self, name: str, kind: SpanKind):
            self.name = name
            self.kind = kind
            self.span_id = None

        def __enter__(self):
            self.span_id = tracer.start_span(self.name, self.kind)
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.span_id:
                status = SpanStatus.ERROR if exc_type else SpanStatus.OK
                tracer.end_span(self.span_id, status)

        def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
            if self.span_id:
                tracer.add_span_event(self.span_id, name, attributes)

        def add_attribute(self, key: str, value: Any):
            if self.span_id:
                tracer.add_span_attribute(self.span_id, key, value)

    return TraceSpan(name, kind)

# Convenience functions
def start_trace(name: str, attributes: Optional[Dict[str, Any]] = None) -> str:
    """Start a new trace"""
    return tracer.start_trace(name, attributes)

def start_span(name: str, kind: SpanKind = SpanKind.INTERNAL,
              attributes: Optional[Dict[str, Any]] = None) -> str:
    """Start a new span"""
    return tracer.start_span(name, kind, attributes)

def end_span(span_id: str, status: SpanStatus = SpanStatus.OK,
            attributes: Optional[Dict[str, Any]] = None):
    """End a span"""
    tracer.end_span(span_id, status, attributes)

def get_current_trace_id() -> Optional[str]:
    """Get current trace ID from context"""
    return current_trace_id.get()

def get_current_span_id() -> Optional[str]:
    """Get current span ID from context"""
    context = current_span_context.get()
    return context.span_id if context else None

if __name__ == "__main__":
    async def main():
        # Example usage
        tracer_instance = DistributedTracer()

        # Start a trace
        trace_id = tracer_instance.start_trace("agentdev_task_execution")

        # Start spans
        with trace_span("task_planning", SpanKind.INTERNAL) as span:
            span.add_attribute("task_type", "deploy_edge")
            span.add_event("plan_generated")
            await asyncio.sleep(0.1)

        with trace_span("security_scan", SpanKind.INTERNAL) as span:
            span.add_attribute("scan_type", "comprehensive")
            await asyncio.sleep(0.2)

        with trace_span("execution", SpanKind.INTERNAL) as span:
            span.add_attribute("target", "production")
            await asyncio.sleep(0.3)

        # Get statistics
        stats = tracer_instance.get_trace_statistics()
        print(f"Tracing statistics: {stats}")

        # Get trace
        trace = tracer_instance.get_trace(trace_id)
        if trace:
            print(f"Trace duration: {trace.duration:.3f}s")
            print(f"Number of spans: {len(trace.spans)}")

    asyncio.run(main())
