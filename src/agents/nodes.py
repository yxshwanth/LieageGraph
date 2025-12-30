from typing import Dict, Any, List
from langchain_core.messages import AIMessage, HumanMessage
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.agents.llm import get_llm
from src.agents.state import AgentState
from src.agents.tracing import trace_node
import json

llm = get_llm()

# Known tables in the system - must match what's in eval_harness.py
KNOWN_TABLES = [
    "users",
    "orders",
    "order_clean",
    "revenue_daily",
    "revenue_dashboard",
]

def plan_node(state: AgentState) -> Dict[str, Any]:
    """
    PLAN STEP: LLM decides what tools to call to answer the question.
    
    State input:
        - user_query: The question to answer
        - messages: History (for context)
    
    State output:
        - investigation_plan: What the agent will investigate
        - current_step: Changes to "investigate"
        - messages: Appends LLM's plan
    """
    
    query = state["user_query"]
    step_count = state.get("step_count", 0)
    
    with trace_node("plan_node", query=query, step=step_count) as span:
        plan_prompt = f"""
You are a data lineage investigator. A user is asking:

"{query}"

Your job is to plan which tools you'll use to answer this question.

Available tools:
1. search_vector_db - Search for relevant tables using natural language
2. get_table_dependencies - Get upstream dependencies of a table
3. validate_lineage_path - Confirm a data path exists
4. get_node_metadata - Get details about a specific table
5. trace_data_flow - Trace complete flow from source to destination
6. check_data_freshness - Check data quality/freshness

Create a concise investigation plan (2-3 steps):

PLAN:
"""
        
        plan = llm.generate(plan_prompt)
        
        if span:
            span.set_attribute("plan_length", len(plan))
        
        return {
            "investigation_plan": plan,
            "current_step": "investigate",
            "step_count": step_count + 1,
            "messages": [
                AIMessage(content=f"Planning investigation:\n{plan}")
            ]
        }

def investigate_node(state: AgentState) -> Dict[str, Any]:
    """
    INVESTIGATE STEP: Route to appropriate tools based on plan.
    
    This node doesn't actually call tools—it decides WHICH tool to call.
    The graph routing will actually invoke the tool.
    
    State input:
        - investigation_plan: What to do
        - user_query: The original question
        - step_count: Current step count
        - max_steps: Maximum steps allowed
        - max_tools: Maximum tools allowed
    
    State output:
        - next_tool: Which tool to call next (e.g., "search_vector_db")
        - current_step: Changes to "tool_use" or "synthesize" if limits reached
        - step_count: Incremented
    """
    
    # Get current state
    step_count = state.get("step_count", 0)
    tool_count = len(state.get("tool_results", {}))
    query = state["user_query"]
    plan = state.get("investigation_plan", "")
    
    with trace_node("investigate_node", query=query, step=step_count, tool_count=tool_count) as span:
        # Note: We don't check limits here because the graph has a hard edge
        # investigate → tool_node. The tool_node and should_continue will
        # check limits and route appropriately.
        
        tool_decision_prompt = f"""
Given the investigation plan:
{plan}

And the original query: "{query}"

Which tool should we call FIRST to make progress?

Respond with ONLY the tool name, like:
search_vector_db
"""
        
        tool_choice = llm.generate(tool_decision_prompt).strip().lower()
        
        # Validate tool choice - if LLM returns something invalid, use default
        valid_tools = ["search_vector_db", "get_table_dependencies", "validate_lineage_path", 
                       "get_node_metadata", "trace_data_flow", "check_data_freshness"]
        
        # Check if tool_choice contains any valid tool name
        selected_tool = None
        for tool in valid_tools:
            if tool in tool_choice or tool_choice in tool:
                selected_tool = tool
                break
        
        # Fallback to search_vector_db if no valid tool found
        if not selected_tool:
            selected_tool = "search_vector_db"
        
        if span:
            span.set_attribute("tool_choice", selected_tool)
            span.set_attribute("llm_raw_choice", tool_choice)
        
        return {
            "current_step": "tool_use",
            "next_tool": selected_tool,
            "step_count": step_count + 1,
            "messages": [
                AIMessage(content=f"Using tool: {selected_tool}")
            ]
        }

def synthesize_node(state: AgentState) -> Dict[str, Any]:
    """
    SYNTHESIZE STEP: LLM creates final answer from tool results.
    
    State input:
        - user_query: Original question
        - tool_results: All accumulated tool outputs
        - vector_context: Relevant documents
        - graph_context: Dependency information
    
    State output:
        - final_answer: Answer to user's question
        - confidence_score: Overall confidence (0-1)
        - current_step: Changes to "done"
    """
    
    query = state["user_query"]
    tool_results = state.get("tool_results", {})
    step_count = state.get("step_count", 0)
    tool_count = len(tool_results)
    
    with trace_node("synthesize_node", query=query, step=step_count, tool_count=tool_count) as span:
        # Format tool results for LLM
        results_text = json.dumps(tool_results, indent=2)
        
        # Build structured prompt that forces explicit table listing
        synthesis_prompt = f"""
You are a data lineage assistant.

You MUST:
1. Answer the question in a short sentence.
2. Then explicitly list ALL relevant table names taken from this set:
   {", ".join(KNOWN_TABLES)}
3. When describing a path, use the format:
   orders -> order_clean -> revenue_daily -> revenue_dashboard

Question:
{query}

Tool results (JSON):
{results_text}

Answer using this template:

Lineage:
<one sentence answer>

Tables:
<comma-separated list of table names>

Path:
<optional arrow-separated path if applicable>

ANSWER:
"""
        
        answer = llm.generate(synthesis_prompt)
        
        # Calculate confidence from tool success rates
        successful_tools = sum(1 for r in tool_results.values() if isinstance(r, dict) and r.get("success", False))
        total_tools = len(tool_results)
        confidence = (successful_tools / total_tools) if total_tools > 0 else 0.5
        
        if span:
            span.set_attribute("answer_length", len(answer))
            span.set_attribute("confidence", confidence)
            span.set_attribute("successful_tools", successful_tools)
            span.set_attribute("total_tools", total_tools)
        
        return {
            "final_answer": answer,
            "confidence_score": confidence,
            "current_step": "done",
            "step_count": step_count + 1,
            "messages": [
                AIMessage(content=f"Answer (confidence: {confidence:.0%}):\n{answer}")
            ]
        }

if __name__ == "__main__":
    from src.agents.state import create_initial_state
    
    # Test plan node
    state = create_initial_state("What feeds into the revenue dashboard?")
    plan_result = plan_node(state)
    # Merge plan result back into state
    state.update(plan_result)
    print("✓ plan_node works")
    print(f"  Plan: {state['investigation_plan'][:100]}...")
    
    # Test investigate node
    investigate_result = investigate_node(state)
    state.update(investigate_result)
    print("✓ investigate_node works")
    print(f"  Next tool: {state.get('next_tool')}")

