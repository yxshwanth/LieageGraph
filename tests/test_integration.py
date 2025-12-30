import pytest
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.vector.database import VectorStore
from src.vector.embeddings import LocalEmbedder
from src.graph.schema import GraphStore

def test_end_to_end_query():
    """Test full flow: embed → search → get lineage"""
    
    # Initialize stores
    vector_store = VectorStore()
    graph_store = GraphStore()
    embedder = LocalEmbedder()
    
    # Embed a query
    query = "What feeds into revenue?"
    embedding = embedder.embed_text(query)
    
    # Search vectors
    results = vector_store.search(embedding, limit=3)
    assert len(results) > 0
    
    # Get lineage for top result
    if results:
        lineage = graph_store.get_dependencies("table_revenue_daily", depth=3)
        assert "dependencies" in lineage
        assert len(lineage["dependencies"]) > 0

def test_vector_search_similarity():
    """Test that vector search returns sensible results"""
    
    embedder = LocalEmbedder()
    
    # Query about revenue should return revenue-related tables
    query = "revenue dashboard dependencies"
    embedding = embedder.embed_text(query)
    
    vector_store = VectorStore()
    results = vector_store.search(embedding, limit=5)
    
    # At least one result should have 'revenue' in the name
    names = [r['table_name'] for r in results]
    assert any('revenue' in name for name in names)

def test_graph_recursive_query():
    """Test recursive dependency traversal"""
    
    graph_store = GraphStore()
    deps = graph_store.get_dependencies("dashboard_revenue", depth=5)
    
    # Should find all upstream tables
    assert len(deps["dependencies"]) > 0
    
    # Should have orders somewhere in the chain
    dep_names = [d['name'] for d in deps['dependencies']]
    assert any('order' in name.lower() for name in dep_names)

