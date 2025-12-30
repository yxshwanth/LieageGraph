"""
OpenTelemetry tracing module for agent observability.

This module provides tracing capabilities using OpenTelemetry with Jaeger exporter.
Tracing is optional and controlled via the TRACING_ENABLED environment variable.
"""

from contextlib import contextmanager
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from typing import Dict, Any, Optional
import json
import os

def _tracing_enabled() -> bool:
    """Check if tracing is enabled via TRACING_ENABLED env var"""
    return os.getenv("TRACING_ENABLED", "false").lower() == "true"

# Initialize tracing only if enabled
tracer = None
if _tracing_enabled():
    # Configure Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name="localhost",
        agent_port=6831,
    )
    
    # Create resource with service name
    resource = Resource.create({SERVICE_NAME: "semantic-lineage-agent"})
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)
    tracer_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
    
    # Get tracer instance
    tracer = trace.get_tracer(__name__)
    print("✓ OpenTelemetry tracing enabled (Jaeger: localhost:6831)")
else:
    # Create a no-op tracer provider to avoid errors
    tracer_provider = TracerProvider()
    trace.set_tracer_provider(tracer_provider)
    tracer = trace.get_tracer(__name__)

@contextmanager
def trace_agent_execution(query: str):
    """
    Context manager to trace full agent execution.
    
    Args:
        query: The user query being processed
    
    Usage:
        with trace_agent_execution("query") as span:
            # run agent
    """
    if not _tracing_enabled():
        yield None
        return
    
    with tracer.start_as_current_span("agent_execution") as span:
        span.set_attribute("query", query)
        span.set_attribute("component", "agent")
        yield span

@contextmanager
def trace_tool_call(tool_name: str, tool_input: Dict[str, Any]):
    """
    Context manager to trace individual tool execution.
    
    Args:
        tool_name: Name of the tool being executed
        tool_input: Input parameters for the tool
    
    Usage:
        with trace_tool_call("search_vector_db", {"query": "..."}) as span:
            # execute tool
    """
    if not _tracing_enabled():
        yield None
        return
    
    with tracer.start_as_current_span(f"tool_{tool_name}") as span:
        span.set_attribute("tool_name", tool_name)
        span.set_attribute("tool_input", json.dumps(tool_input, default=str))
        yield span

@contextmanager
def trace_llm_call(prompt: str, model: str = "mistral"):
    """
    Context manager to trace LLM calls.
    
    Args:
        prompt: The prompt being sent to the LLM
        model: The model name (default: "mistral")
    
    Usage:
        with trace_llm_call(prompt) as span:
            # call LLM
    """
    if not _tracing_enabled():
        yield None
        return
    
    with tracer.start_as_current_span("llm_inference") as span:
        span.set_attribute("model", model)
        span.set_attribute("prompt_length", len(prompt))
        span.set_attribute("component", "llm")
        yield span

@contextmanager
def trace_node(node_name: str, **attributes):
    """
    Context manager to trace individual node execution.
    
    Args:
        node_name: Name of the node (e.g., "plan_node", "investigate_node")
        **attributes: Additional attributes to set on the span
    
    Usage:
        with trace_node("plan_node", query="...", step=1) as span:
            # execute node
    """
    if not _tracing_enabled():
        yield None
        return
    
    with tracer.start_as_current_span(node_name) as span:
        for key, value in attributes.items():
            span.set_attribute(key, str(value))
        yield span

def traced_run_agent(query: str, run_fn):
    """
    Run agent with full tracing.
    
    Args:
        query: User query
        run_fn: Function that runs agent (callable that takes no args)
    
    Returns:
        Agent result
    """
    with trace_agent_execution(query) as span:
        if span:
            span.set_attribute("status", "started")
        
        try:
            result = run_fn()
            
            if span:
                span.set_attribute("status", "completed")
                span.set_attribute("confidence", result.get("confidence_score", 0.0))
                span.set_attribute("tools_used", len(result.get("tool_calls_made", [])))
            
            return result
        
        except Exception as e:
            if span:
                span.set_attribute("status", "failed")
                span.set_attribute("error", str(e))
            raise

if __name__ == "__main__":
    if _tracing_enabled():
        print("✓ Tracing configured for Jaeger at localhost:6831")
        print("View traces at: http://localhost:16686")
    else:
        print("Tracing is disabled. Set TRACING_ENABLED=true to enable.")

