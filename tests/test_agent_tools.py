import pytest
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.tools import (
    search_vector_db,
    get_table_dependencies,
    validate_lineage_path,
    get_node_metadata,
    trace_data_flow,
    check_data_freshness,
)

def test_search_vector_db():
    """Test vector search tool"""
    result = search_vector_db.invoke({"query": "What feeds into revenue?", "limit": 3})
    
    assert result['success'] == True
    assert result['count'] > 0
    assert 'items' in result
    print("✓ search_vector_db working")

def test_get_table_dependencies():
    """Test graph dependency tool"""
    result = get_table_dependencies.invoke({
        "table_id": "dashboard_revenue",
        "depth": 3
    })
    
    assert result['success'] == True
    assert 'dependencies' in result
    print("✓ get_table_dependencies working")

def test_validate_lineage_path():
    """Test path validation"""
    result = validate_lineage_path.invoke({
        "source_id": "table_orders",
        "target_id": "dashboard_revenue"
    })
    
    assert result['success'] == True
    assert 'is_valid' in result
    print("✓ validate_lineage_path working")

def test_get_node_metadata():
    """Test node metadata"""
    result = get_node_metadata.invoke({"node_id": "table_users"})
    
    assert result['success'] == True
    print("✓ get_node_metadata working")

def test_trace_data_flow():
    """Test data flow tracing"""
    result = trace_data_flow.invoke({
        "start_node": "table_orders",
        "end_node": "dashboard_revenue"
    })
    
    assert result['success'] == True
    assert 'path' in result
    print("✓ trace_data_flow working")

def test_check_data_freshness():
    """Test data freshness check"""
    result = check_data_freshness.invoke({"table_id": "table_users"})
    
    assert result['success'] == True
    assert 'freshness_score' in result
    print("✓ check_data_freshness working")

if __name__ == "__main__":
    # Run tests manually
    test_search_vector_db()
    test_get_table_dependencies()
    test_validate_lineage_path()
    test_get_node_metadata()
    test_trace_data_flow()
    test_check_data_freshness()
    print("\n✓ All tools tested successfully")

