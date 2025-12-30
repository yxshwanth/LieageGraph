"""
Traced version of the agent graph with OpenTelemetry integration.

This module provides a wrapper around the base agent graph that adds
OpenTelemetry tracing for observability. Tracing is optional and
controlled via the TRACING_ENABLED environment variable.
"""

import sys
from pathlib import Path
from typing import Dict, Any

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.agents.graph import create_agent_graph
from src.agents.tracing import trace_agent_execution, _tracing_enabled
from src.agents.state import create_initial_state

def create_traced_agent_graph():
    """
    Create agent graph with integrated OpenTelemetry tracing.
    
    Returns:
        A graph instance with tracing enabled (if TRACING_ENABLED=true)
        or the base graph (if tracing is disabled)
    """
    
    base_graph = create_agent_graph()
    
    # Only wrap with tracing if enabled
    if not _tracing_enabled():
        return base_graph
    
    # Wrap execution with tracing
    original_invoke = base_graph.invoke
    
    def traced_invoke(input_state, config=None):
        query = input_state.get("user_query", "unknown")
        
        with trace_agent_execution(query) as span:
            if span:
                span.set_attribute("component", "agent_graph")
                span.set_attribute("status", "started")
            
            try:
                result = original_invoke(input_state, config)
                
                if span:
                    span.set_attribute("status", "success")
                    span.set_attribute("final_confidence", result.get("confidence_score", 0.0))
                    span.set_attribute("tools_executed", len(result.get("tool_calls_made", [])))
                    span.set_attribute("final_step", result.get("current_step", "unknown"))
                    span.set_attribute("total_steps", result.get("step_count", 0))
                
                return result
            
            except Exception as e:
                if span:
                    span.set_attribute("status", "error")
                    span.set_attribute("error_message", str(e))
                raise
    
    base_graph.invoke = traced_invoke
    return base_graph

def run_traced_agent(query: str, verbose: bool = True, recursion_limit: int = 40) -> Dict[str, Any]:
    """
    Run agent with OpenTelemetry tracing.
    
    Traces will be visible in Jaeger UI:
        http://localhost:16686
    
    Args:
        query: The user's natural language question
        verbose: If True, prints intermediate steps and final summary
        recursion_limit: Maximum number of steps the graph can execute
    
    Returns:
        The final AgentState dictionary after the graph execution
    """
    
    initial_state = create_initial_state(query)
    graph = create_traced_agent_graph()
    
    if verbose:
        tracing_status = "enabled" if _tracing_enabled() else "disabled"
        print(f"Running agent (tracing: {tracing_status})")
        print(f"Query: {query}")
        if _tracing_enabled():
            print(f"View traces at: http://localhost:16686")
        print("-" * 60)
    
    # Execute graph
    result = graph.invoke(initial_state, config={'recursion_limit': recursion_limit})
    
    if verbose:
        print(f"✓ Execution complete")
        print(f"  Final Answer: {result.get('final_answer', 'No answer')[:200]}...")
        print(f"  Confidence: {result.get('confidence_score', 0.0):.0%}")
        print(f"  Tools used: {result.get('tool_calls_made', [])}")
        print(f"  Final step: {result.get('current_step')}")
        if _tracing_enabled():
            print(f"  View traces at: http://localhost:16686")
    
    return result

if __name__ == "__main__":
    print("Testing traced agent...")
    try:
        result = run_traced_agent("What feeds into revenue?", verbose=True)
        print("\n✓ Traced execution successful")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

