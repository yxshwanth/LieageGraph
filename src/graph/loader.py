import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from graph.schema import GraphStore

SAMPLE_LINEAGE = {
    "nodes": [
        ("table_users", "Table", "users", "User master data"),
        ("table_orders", "Table", "orders", "Raw orders"),
        ("table_order_clean", "Table", "order_clean", "Cleaned orders"),
        ("table_revenue_daily", "Table", "revenue_daily", "Daily revenue"),
        ("dashboard_revenue", "Dashboard", "revenue_dashboard", "Revenue dashboard"),
    ],
    "edges": [
        ("table_orders", "table_order_clean", "FEEDS_INTO"),
        ("table_order_clean", "table_revenue_daily", "FEEDS_INTO"),
        ("table_users", "table_revenue_daily", "FEEDS_INTO"),
        ("table_revenue_daily", "dashboard_revenue", "FEEDS_INTO"),
    ]
}

def load_sample_lineage():
    store = GraphStore()
    
    # Add nodes
    for node_id, node_type, name, desc in SAMPLE_LINEAGE["nodes"]:
        store.add_node(node_id, node_type, name, desc)
    
    # Add edges
    for source, target, edge_type in SAMPLE_LINEAGE["edges"]:
        store.add_edge(source, target, edge_type)
    
    print("✓ Loaded sample lineage")
    
    # Test query
    deps = store.get_dependencies("dashboard_revenue")
    print(f"\nDependencies of {deps['root']}:")
    for dep in deps['dependencies']:
        print(f"  {dep['name']} (depth {dep['depth']})")

if __name__ == "__main__":
    load_sample_lineage()

