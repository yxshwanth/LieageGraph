from langgraph.graph import StateGraph, START, END
from typing import Dict, Any, Literal
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.agents.state import AgentState, create_initial_state
from src.agents.nodes import plan_node, investigate_node, synthesize_node
from src.agents.tool_executor import execute_tool, should_continue_investigation
from src.agents.tools import ALL_TOOLS
from langchain_core.messages import AIMessage
import json

def create_agent_graph():
    """
    Create the complete LangGraph state machine.
    
    Flow:
    START → plan_node → investigate_node → [tool_node] → check_continue
                                              ↓
                                        [execute tool]
                                              ↓
                                        [loop or exit]
                                              ↓
                                        synthesize_node → END
    """
    
    # Create graph
    graph = StateGraph(AgentState)
    
    # ============ ADD NODES ============
    
    # 1. Planning node
    graph.add_node("plan", plan_node)
    
    # 2. Investigation node (decides which tool)
    graph.add_node("investigate", investigate_node)
    
    # 3. Tool execution node (calls the tool)
    def tool_node(state: AgentState) -> Dict[str, Any]:
        """Execute the selected tool and update state"""
        
        tool_name = state.get("next_tool", "").strip()
        query = state["user_query"]
        step_count = state.get("step_count", 0)
        max_steps = state.get("max_steps", 8)
        max_tools = state.get("max_tools", 3)
        prev_tool_results = state.get("tool_results", {})
        tool_calls = state.get("tool_calls_made", []).copy()
        tool_count = len(prev_tool_results)
        
        # Check if no tool name provided - execute a default tool
        if not tool_name:
            tool_name = "search_vector_db"  # Default fallback
        
        # Check for duplicate tool calls (prevent calling same tool repeatedly)
        if tool_name in tool_calls or tool_name in prev_tool_results:
            # Already tried this tool - but still execute it once, then should_continue will stop
            # This ensures we get at least some results
            pass  # Allow execution even if duplicate (should_continue will prevent loops)
        
        # Build tool input based on tool type and query
        tool_input = {}
        
        if "search" in tool_name.lower():
            tool_input = {"query": query, "limit": 3}
        elif "dependencies" in tool_name.lower():
            # Try to extract table name from query or use a default
            # In production, LLM would extract this
            tool_input = {"table_id": "dashboard_revenue", "depth": 3}
        elif "validate" in tool_name.lower() or "trace" in tool_name.lower():
            tool_input = {"source_id": "table_orders", "target_id": "dashboard_revenue"}
        elif "metadata" in tool_name.lower():
            tool_input = {"node_id": "table_users"}
        elif "freshness" in tool_name.lower():
            tool_input = {"table_id": "table_users"}
        else:
            # Default fallback
            tool_input = {"query": query, "limit": 3}
        
        # Execute tool (only if we have a valid tool name)
        if not tool_name:
            # If no tool name, skip to synthesize
            return {
                "current_step": "synthesize",
                "step_count": step_count + 1,
                "messages": [AIMessage(content="No tool selected, synthesizing answer")]
            }
        
        result = execute_tool(tool_name, tool_input)
        
        # Store result (always create new dict to ensure state update)
        tool_results = dict(prev_tool_results)
        tool_results[tool_name] = result
        
        # Track which tools were called (store tool name as string)
        tool_calls.append(tool_name)
        
        # Calculate new confidence
        successful = sum(1 for r in tool_results.values() if isinstance(r, dict) and r.get("success", False))
        new_confidence = successful / len(tool_results) if tool_results else 0.0
        
        # Update vector_context or graph_context if relevant
        vector_context = state.get("vector_context", []).copy()
        graph_context = state.get("graph_context", {}).copy()
        
        if "search" in tool_name.lower() and isinstance(result, dict) and result.get("success"):
            vector_context = result.get("items", [])
        elif "dependencies" in tool_name.lower() and isinstance(result, dict) and result.get("success"):
            graph_context = result
        
        # Fix: Use AIMessage for messages
        result_count = result.get('count', 0) if isinstance(result, dict) else 0
        message_content = f"Executed {tool_name}: {result_count} results"
        
        return {
            "tool_results": tool_results,
            "tool_calls_made": tool_calls,
            "confidence_score": new_confidence,
            "vector_context": vector_context,
            "graph_context": graph_context,
            "step_count": step_count + 1,
            "messages": [
                AIMessage(content=message_content)
            ]
        }
    
    graph.add_node("tool_node", tool_node)
    
    # 4. Synthesis node (create final answer)
    graph.add_node("synthesize", synthesize_node)
    
    # ============ ADD EDGES ============
    
    # Entry point
    graph.add_edge(START, "plan")
    
    # Planning → Investigation
    graph.add_edge("plan", "investigate")
    
    # Investigation → Tool execution
    graph.add_edge("investigate", "tool_node")
    
    # Tool → Check if we should continue
    def should_continue(state: AgentState) -> Literal["investigate", "synthesize"]:
        """Routing logic: continue investigating or synthesize answer?"""
        
        # Priority 1: Check hard limits first (deterministic stopping)
        step_count = state.get("step_count", 0)
        max_steps = state.get("max_steps", 8)
        max_tools = state.get("max_tools", 3)
        tool_results = state.get("tool_results", {})
        tool_count = len(tool_results)
        
        # Hard limits - always stop
        if step_count >= max_steps:
            return "synthesize"
        if tool_count >= max_tools:
            return "synthesize"
        
        # Priority 2: If no tools executed yet, always continue to get at least one
        if tool_count == 0:
            return "investigate"
        
        # Priority 3: Check confidence
        confidence = state.get("confidence_score", 0.0)
        if confidence > 0.7:
            return "synthesize"
        
        # Priority 4: After 2+ tools, synthesize (prevent infinite loops)
        if tool_count >= 2:
            return "synthesize"
        
        # Otherwise continue investigating (but only if we have tools)
        return "investigate"
    
    graph.add_conditional_edges(
        "tool_node",
        should_continue,
        {
            "investigate": "investigate",
            "synthesize": "synthesize"
        }
    )
    
    # Synthesis → End
    graph.add_edge("synthesize", END)
    
    # ============ COMPILE ============
    
    compiled = graph.compile()
    
    return compiled

def run_agent(query: str, verbose: bool = True) -> Dict[str, Any]:
    """
    Run the agent on a query and return results.
    
    Args:
        query: User's natural language question
        verbose: Print intermediate steps
    
    Returns:
        Final state with answer, confidence, tool results
    """
    
    # Create initial state
    initial_state = create_initial_state(query)
    
    # Create and compile graph
    graph = create_agent_graph()
    
    # Run graph
    if verbose:
        print(f"Query: {query}")
        print("-" * 60)
    
    # Execute graph with reasonable recursion limit
    # Hard limits in routing should prevent hitting this
    final_state = graph.invoke(initial_state, config={"recursion_limit": 40})
    
    if verbose:
        print(f"Final Answer: {final_state.get('final_answer', 'No answer')}")
        print(f"Confidence: {final_state.get('confidence_score', 0.0):.0%}")
        print(f"Tools used: {final_state.get('tool_calls_made', [])}")
    
    return final_state

if __name__ == "__main__":
    # Test the graph
    try:
        print("Creating agent graph...")
        graph = create_agent_graph()
        print("✓ Graph created successfully")
        print(f"  Graph compiled: {graph is not None}")
    except Exception as e:
        print(f"✗ Error creating graph: {e}")
        import traceback
        traceback.print_exc()

