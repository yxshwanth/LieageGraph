from typing import Annotated, List, Dict, Any, Optional
from pydantic import BaseModel, Field
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

def add_messages(left: List[BaseMessage], right: List[BaseMessage]) -> List[BaseMessage]:
    """Reducer function for accumulating messages in agent state"""
    return left + right

class LineageSource(BaseModel):
    """Represents a data lineage node"""
    id: str
    name: str
    node_type: str  # 'table', 'dashboard', 'metric'
    description: str
    depth: int = 0

class LineagePath(BaseModel):
    """Complete lineage path from source to target"""
    root_node: str
    nodes: List[LineageSource]
    edges: List[Dict[str, str]]
    confidence: float

class AgentState(TypedDict):
    """
    Agent state machine.
    
    CRITICAL: All fields here are persisted across agent steps.
    Use Annotated[list, add_messages] for message history.
    """
    
    # Input
    user_query: str
    
    # Message history (append-only)
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Investigation state
    current_step: str  # 'plan' | 'investigate' | 'synthesize' | 'done'
    
    investigation_plan: Optional[str]
    
    target_table: Optional[str]
    
    # Tool results (accumulated during investigation)
    tool_results: Dict[str, Any]
    
    # Discovery results
    discovered_lineage: Optional[LineagePath]
    
    vector_context: List[Dict]
    
    graph_context: Dict[str, Any]
    
    # Confidence tracking
    confidence_score: float
    
    node_confidence_scores: Dict[str, float]
    
    # Final output
    final_answer: Optional[str]
    
    # Debugging
    tool_calls_made: List[str]
    
    errors: List[str]
    
    # Step counting and limits
    step_count: int  # Total steps through graph
    max_steps: int  # Maximum steps allowed (default: 8)
    max_tools: int  # Maximum tool calls allowed (default: 3)

def create_initial_state(user_query: str, max_steps: int = 8, max_tools: int = 3) -> AgentState:
    """Create initial agent state from user query"""
    return AgentState(
        user_query=user_query,
        messages=[HumanMessage(content=user_query)],
        current_step="plan",
        investigation_plan=None,
        target_table=None,
        tool_results={},
        discovered_lineage=None,
        vector_context=[],
        graph_context={},
        confidence_score=0.0,
        node_confidence_scores={},
        final_answer=None,
        tool_calls_made=[],
        errors=[],
        step_count=0,
        max_steps=max_steps,
        max_tools=max_tools,
    )

# Validation
if __name__ == "__main__":
    state = create_initial_state("What feeds into revenue dashboard?")
    print("✓ AgentState initialized")
    print(f"  Current step: {state['current_step']}")
    print(f"  Message count: {len(state['messages'])}")

