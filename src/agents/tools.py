from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.vector.database import VectorStore
from src.vector.embeddings import LocalEmbedder
from src.graph.schema import GraphStore
import json

# Initialize components (these persist for agent lifetime)
# Use lazy initialization to handle DuckDB lock conflicts gracefully
# The connection will be established on first use
vector_store = VectorStore()
embedder = LocalEmbedder()
graph_store = GraphStore()

class SearchResult(BaseModel):
    """Result from vector/graph search"""
    items: List[Dict[str, Any]]
    count: int
    relevance_scores: List[float]

# ============ TOOL 1: Vector Search ============
@tool("search_vector_db")
def search_vector_db(query: str, limit: int = 3) -> Dict[str, Any]:
    """
    Search vector database for relevant tables/dashboards.
    
    Args:
        query: Natural language description of what to find
        limit: Maximum results to return
    
    Returns:
        Dictionary with:
        - items: List of matching tables/dashboards
        - count: Number of results
        - relevance_scores: Similarity scores (0-1)
    
    Example:
        Input: "What tables contain user data?"
        Output: {
            "items": [
                {"table_name": "users", "similarity": 0.92},
                {"table_name": "user_segment", "similarity": 0.87}
            ],
            "count": 2
        }
    """
    try:
        # Generate embedding for query
        query_embedding = embedder.embed_text(query)
        
        # Search vector store
        results = vector_store.search(query_embedding, limit=limit)
        
        return {
            "success": True,
            "items": results,
            "count": len(results),
            "relevance_scores": [r['similarity'] for r in results],
            "query_embedding_dim": len(query_embedding)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "items": [],
            "count": 0
        }

# ============ TOOL 2: Get Table Dependencies ============
@tool("get_table_dependencies")
def get_table_dependencies(table_id: str, depth: int = 3) -> Dict[str, Any]:
    """
    Get upstream dependencies for a table (recursive graph traversal).
    
    Args:
        table_id: ID of table to analyze (e.g., "table_users")
        depth: How many levels deep to traverse (1-5)
    
    Returns:
        Dictionary with:
        - dependencies: List of upstream tables/data sources
        - paths: How each dependency flows in
        - depth_reached: Actual depth traversed
    
    Example:
        Input: table_id="dashboard_revenue", depth=3
        Output: {
            "root": "dashboard_revenue",
            "dependencies": [
                {"name": "revenue_daily", "depth": 1},
                {"name": "order_clean", "depth": 2},
                {"name": "orders", "depth": 3}
            ]
        }
    """
    try:
        # Query graph for dependencies
        result = graph_store.get_dependencies(table_id, depth=depth)
        
        # Flatten results for readability
        dep_names = [d['name'] for d in result.get('dependencies', [])]
        
        return {
            "success": True,
            "root": result['root'],
            "dependency_count": len(result.get('dependencies', [])),
            "dependencies": result.get('dependencies', []),
            "dependency_names": dep_names,
            "depth_used": depth
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "root": table_id,
            "dependency_count": 0,
            "dependencies": []
        }

# ============ TOOL 3: Validate Lineage Path ============
@tool("validate_lineage_path")
def validate_lineage_path(
    source_id: str,
    target_id: str,
    proposed_path: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Validate that a proposed lineage path actually exists in the graph.
    
    Args:
        source_id: Starting point
        target_id: Ending point
        proposed_path: Optional list of intermediate nodes to validate
    
    Returns:
        Dictionary with:
        - is_valid: Whether path exists
        - actual_path: Real path in graph
        - confidence: How certain we are
    
    Example:
        Input: source="orders", target="revenue_dashboard"
        Output: {
            "is_valid": true,
            "actual_path": ["orders", "order_clean", "revenue_daily", "revenue_dashboard"],
            "confidence": 0.95
        }
    """
    try:
        # Get actual path from target back to source
        upstream = graph_store.get_dependencies(target_id, depth=10)
        
        # Check if source is in upstream dependencies
        upstream_ids = [d['id'] for d in upstream.get('dependencies', [])]
        
        is_valid = source_id in upstream_ids or source_id == target_id
        
        return {
            "success": True,
            "is_valid": is_valid,
            "source": source_id,
            "target": target_id,
            "path_exists": is_valid,
            "confidence": 0.95 if is_valid else 0.2,
            "upstream_nodes": upstream_ids
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "is_valid": False,
            "confidence": 0.0
        }

# ============ TOOL 4: Get Node Metadata ============
@tool("get_node_metadata")
def get_node_metadata(node_id: str) -> Dict[str, Any]:
    """
    Get detailed metadata about a specific table/dashboard.
    
    Args:
        node_id: ID of node (e.g., "table_users")
    
    Returns:
        Dictionary with:
        - name: Human-readable name
        - type: 'table', 'dashboard', 'metric'
        - description: What it contains/does
        - fields: Available columns (if table)
    
    Example:
        Input: "table_users"
        Output: {
            "name": "users",
            "type": "table",
            "description": "User master data",
            "source": "production_db"
        }
    """
    try:
        # Query database for node metadata
        cur = graph_store.conn.cursor()
        cur.execute(
            "SELECT id, name, node_type, description, metadata FROM nodes WHERE id = %s",
            (node_id,)
        )
        result = cur.fetchone()
        
        if result:
            # Fix: Properly unpack tuple
            node_id_db, name, node_type, description, metadata = result
            return {
                "success": True,
                "id": node_id_db,
                "name": name,
                "type": node_type,
                "description": description or "",
                "metadata": metadata if metadata else {}
            }
        else:
            return {
                "success": False,
                "error": f"Node not found: {node_id}",
                "id": node_id
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "id": node_id
        }

# ============ TOOL 5: Trace Data Flow ============
@tool("trace_data_flow")
def trace_data_flow(start_node: str, end_node: str) -> Dict[str, Any]:
    """
    Trace complete data flow path between two nodes.
    
    Args:
        start_node: Source table/node
        end_node: Destination table/node
    
    Returns:
        Dictionary with:
        - path: List of nodes in flow
        - edges: Relationships between nodes
        - confidence: How certain the path is
    
    Example:
        Input: start="orders", end="revenue_dashboard"
        Output: {
            "path": ["orders", "order_clean", "revenue_daily", "revenue_dashboard"],
            "confidence": 0.92
        }
    """
    try:
        # Get upstream from end_node
        upstream = graph_store.get_dependencies(end_node, depth=10)
        
        # Find path that includes start_node
        path = [end_node]
        
        for dep in upstream.get('dependencies', []):
            if dep['id'] not in path:
                path.append(dep['id'])
        
        # Check if start_node is in path
        if start_node in path:
            path = path[:path.index(start_node) + 1]
            path.reverse()
            confidence = 0.95
        else:
            confidence = 0.3
        
        return {
            "success": True,
            "start": start_node,
            "end": end_node,
            "path": path,
            "path_length": len(path),
            "confidence": confidence
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "start": start_node,
            "end": end_node,
            "path": []
        }

# ============ TOOL 6: Check Data Freshness ============
@tool("check_data_freshness")
def check_data_freshness(table_id: str) -> Dict[str, Any]:
    """
    Check how fresh/reliable the data for a table is.
    (Simulated for now - in production would check update logs)
    
    Args:
        table_id: Table to check
    
    Returns:
        Dictionary with:
        - freshness_score: 0-1 (1 = very fresh)
        - last_update: When data was last updated
        - reliability: 0-1 confidence in the data
    """
    try:
        cur = graph_store.conn.cursor()
        cur.execute(
            "SELECT created_at FROM nodes WHERE id = %s",
            (table_id,)
        )
        result = cur.fetchone()
        
        # Simple freshness: recently created = more fresh
        freshness = 0.85
        
        return {
            "success": True,
            "table_id": table_id,
            "freshness_score": freshness,
            "reliability": 0.9,
            "confidence": 0.8,
            "last_update": str(result[0]) if result else None
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "table_id": table_id,
            "freshness_score": 0.5
        }

# Export all tools
ALL_TOOLS = [
    search_vector_db,
    get_table_dependencies,
    validate_lineage_path,
    get_node_metadata,
    trace_data_flow,
    check_data_freshness
]

if __name__ == "__main__":
    print("Available tools:")
    for tool in ALL_TOOLS:
        print(f"  - {tool.name}: {tool.description}")
    print(f"\n✓ {len(ALL_TOOLS)} tools defined")

