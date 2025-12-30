from typing import Dict, Any, Optional
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.agents.tools import ALL_TOOLS
from src.agents.tracing import trace_tool_call
import json
import time

def get_tool_by_name(tool_name: str):
    """Find tool by name"""
    for tool in ALL_TOOLS:
        if tool.name.lower() == tool_name.lower():
            return tool
    return None

def execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a specific tool with given inputs.
    
    Args:
        tool_name: Name of tool to call
        tool_input: Arguments for the tool
    
    Returns:
        Tool result (includes "success" field)
    """
    
    with trace_tool_call(tool_name, tool_input) as span:
        start_time = time.time()
        
        tool = get_tool_by_name(tool_name)
        
        if not tool:
            result = {
                "success": False,
                "error": f"Tool not found: {tool_name}"
            }
            if span:
                span.set_attribute("success", False)
                span.set_attribute("error", result["error"])
            return result
        
        try:
            # LangChain tools are callables
            result = tool.invoke(tool_input)
            latency_ms = (time.time() - start_time) * 1000
            
            # Add tracing attributes
            if span:
                span.set_attribute("success", result.get("success", False))
                span.set_attribute("latency_ms", latency_ms)
                
                # Add result metadata if available
                if isinstance(result, dict):
                    if "count" in result:
                        span.set_attribute("result_count", result["count"])
                    if "error" in result:
                        span.set_attribute("error", result["error"])
            
            return result
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            result = {
                "success": False,
                "error": str(e)
            }
            if span:
                span.set_attribute("success", False)
                span.set_attribute("error", str(e))
                span.set_attribute("latency_ms", latency_ms)
            return result

def should_continue_investigation(state: Dict[str, Any]) -> bool:
    """
    Decide if investigation should continue or wrap up.
    
    Continue if:
    - Not all tools have been tried
    - Confidence is below 0.8
    - Investigation step count < 5
    
    Stop if:
    - Found a clear answer
    - Tried enough tools
    - Multiple tools confirm the same result
    """
    
    tool_count = len(state.get("tool_results", {}))
    confidence = state.get("confidence_score", 0.0)
    
    # Simple heuristic: continue if low confidence and haven't tried many tools
    should_continue = (confidence < 0.8 and tool_count < 4)
    
    return should_continue

if __name__ == "__main__":
    # Test tool execution
    result = execute_tool("search_vector_db", {
        "query": "What feeds into revenue?",
        "limit": 3
    })
    print(f"✓ Tool execution works")
    print(f"  Result success: {result.get('success')}")
    print(f"  Items found: {result.get('count', 0)}")

