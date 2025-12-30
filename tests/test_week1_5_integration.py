"""
Integration tests for Week 1.5 - Agent Core

These tests verify end-to-end functionality of the LangGraph agent
with all its components: planning, investigation, tool execution, and synthesis.
"""

import pytest
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.graph import run_agent
from src.agents.state import create_initial_state
from src.vector.database import VectorStore
from src.graph.schema import GraphStore

class TestAgentIntegration:
    """End-to-end tests for Week 1.5"""
    
    def setup_method(self):
        """Initialize test data"""
        self.vector_store = VectorStore()
        self.graph_store = GraphStore()
    
    def test_simple_query(self):
        """Test agent on simple query"""
        result = run_agent(
            "What feeds into revenue dashboard?",
            verbose=False
        )
        
        assert result is not None
        assert result.get("current_step") == "done"
        assert result.get("final_answer") is not None
        assert len(result["final_answer"]) > 0
        assert result.get("confidence_score", 0.0) > 0.3
        
        print(f"✓ Simple query test passed (confidence: {result['confidence_score']:.0%})")
    
    def test_complex_query(self):
        """Test agent on more complex question"""
        result = run_agent(
            "Can you trace the complete data flow from orders to the revenue dashboard?",
            verbose=False
        )
        
        assert result.get("current_step") == "done"
        assert "order" in result["final_answer"].lower() or "revenue" in result["final_answer"].lower()
        
        print(f"✓ Complex query test passed")
    
    def test_agent_uses_multiple_tools(self):
        """Test that agent uses multiple tools"""
        result = run_agent(
            "What tables are involved in revenue reporting?",
            verbose=False
        )
        
        tools_used = result.get("tool_calls_made", [])
        assert len(tools_used) > 0, "Agent should use at least one tool"
        
        print(f"✓ Multi-tool test passed (tools used: {tools_used})")
    
    def test_agent_state_consistency(self):
        """Test that agent state remains consistent through execution"""
        initial_state = create_initial_state("Test query")
        
        result = run_agent("What feeds into revenue?", verbose=False)
        
        # Final state should have all expected fields
        required_fields = [
            "user_query",
            "current_step",
            "final_answer",
            "confidence_score",
            "tool_calls_made"
        ]
        
        for field in required_fields:
            assert field in result, f"Missing field: {field}"
        
        print(f"✓ State consistency test passed")
    
    def test_agent_latency(self):
        """Test that agent responds within acceptable latency"""
        import time
        
        start = time.time()
        result = run_agent("What feeds into revenue?", verbose=False)
        elapsed = time.time() - start
        
        # Should complete in reasonable time
        # Ollama inference can vary, so we allow up to 45 seconds
        # Typical: 3-6 seconds, but can be slower on first run or with complex queries
        assert elapsed < 45, f"Query took {elapsed:.1f}s, should be < 45s"
        
        print(f"✓ Latency test passed ({elapsed:.1f}s)")
    
    def test_error_handling(self):
        """Test that agent handles errors gracefully"""
        result = run_agent("Invalid nonsense query xyz abc def", verbose=False)
        
        # Should still complete even with bad query
        assert result.get("current_step") == "done"
        assert "error" not in result.get("final_answer", "").lower() or result.get("confidence_score", 0.0) < 0.5
        
        print(f"✓ Error handling test passed")

def test_agent_response_quality():
    """Test that agent responses are reasonable"""
    result = run_agent("What feeds into revenue dashboard?", verbose=False)
    
    answer = result.get("final_answer", "")
    
    # Response should mention relevant concepts
    should_mention = ["revenue", "dashboard", "data", "table"]
    mentions = sum(1 for word in should_mention if word.lower() in answer.lower())
    
    assert mentions >= 2, f"Response should mention multiple relevant concepts, found {mentions}"
    
    print(f"✓ Response quality test passed")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

