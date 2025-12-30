"""
Graph database module for storing and querying data lineage relationships.

This module provides a GraphStore class that uses PostgreSQL to store
nodes and edges representing data lineage, enabling recursive queries
to find upstream and downstream dependencies.
"""

import psycopg2
from psycopg2.extras import execute_values
import os

class GraphStore:
    """
    Graph store for data lineage relationships.
    
    Uses PostgreSQL to store nodes (tables, dashboards, etc.) and edges
    (relationships like FEEDS_INTO, DEPENDS_ON) to represent data lineage.
    Supports recursive queries to traverse dependency chains.
    
    Attributes:
        conn: PostgreSQL connection object
        cur: PostgreSQL cursor object
    """
    
    def __init__(self, db_url: str = None):
        """
        Initialize graph store with PostgreSQL connection.
        
        Args:
            db_url: PostgreSQL connection URL. If None, uses DATABASE_URL
                   environment variable or defaults to localhost with current user.
        """
        if not db_url:
            # Default to current user (yash) or from environment
            default_user = os.getenv("USER", "postgres")
            db_url = os.getenv("DATABASE_URL", f"postgresql://{default_user}@localhost/semantic_lineage")
        
        self.conn = psycopg2.connect(db_url)
        self.cur = self.conn.cursor()
        self._init_schema()
    
    def _init_schema(self):
        """
        Initialize the database schema.
        
        Creates two tables:
        - nodes: Stores graph nodes (tables, dashboards, etc.)
        - edges: Stores relationships between nodes
        
        Also creates indexes for performance.
        """
        
        # Create nodes table
        self.cur.execute('''
        CREATE TABLE IF NOT EXISTS nodes (
            id VARCHAR PRIMARY KEY,
            node_type VARCHAR,  -- 'Table', 'Dashboard', 'Query', etc.
            name VARCHAR,
            description TEXT,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create edges table (relationships)
        self.cur.execute('''
        CREATE TABLE IF NOT EXISTS edges (
            id SERIAL PRIMARY KEY,
            source_id VARCHAR REFERENCES nodes(id),
            target_id VARCHAR REFERENCES nodes(id),
            edge_type VARCHAR,  -- 'FEEDS_INTO', 'DEPENDS_ON', 'USES', etc.
            strength FLOAT DEFAULT 1.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create indexes
        self.cur.execute('CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(node_type)')
        self.cur.execute('CREATE INDEX IF NOT EXISTS idx_nodes_name ON nodes(name)')
        self.cur.execute('CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id)')
        self.cur.execute('CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id)')
        
        self.conn.commit()
        print("✓ Graph schema initialized")
    
    def add_node(self, id: str, node_type: str, name: str, description: str = ""):
        """
        Add a node to the graph.
        
        Args:
            id: Unique identifier for the node
            node_type: Type of node ('Table', 'Dashboard', 'Query', etc.)
            name: Name of the node
            description: Optional description of the node
        """
        self.cur.execute(
            '''INSERT INTO nodes (id, node_type, name, description) 
               VALUES (%s, %s, %s, %s)
               ON CONFLICT (id) DO UPDATE SET description = EXCLUDED.description''',
            (id, node_type, name, description)
        )
        self.conn.commit()
    
    def add_edge(self, source_id: str, target_id: str, edge_type: str, strength: float = 1.0):
        """
        Add a relationship (edge) between two nodes.
        
        Args:
            source_id: ID of the source node
            target_id: ID of the target node
            edge_type: Type of relationship ('FEEDS_INTO', 'DEPENDS_ON', etc.)
            strength: Optional strength/weight of the relationship (default: 1.0)
        """
        self.cur.execute(
            '''INSERT INTO edges (source_id, target_id, edge_type, strength) 
               VALUES (%s, %s, %s, %s)''',
            (source_id, target_id, edge_type, strength)
        )
        self.conn.commit()
    
    def get_dependencies(self, node_id: str, depth: int = 3) -> dict:
        """
        Get all upstream dependencies using recursive query.
        
        Traverses the graph backwards from the given node to find all
        nodes that feed into it, up to the specified depth.
        
        Args:
            node_id: ID of the node to find dependencies for
            depth: Maximum depth to traverse (default: 3)
            
        Returns:
            Dictionary with:
            - root: The original node ID
            - dependencies: List of dependency dictionaries with:
              - id: Node ID
              - name: Node name
              - type: Node type
              - depth: Depth from root (0 = direct dependency)
        """
        
        query = f'''
        WITH RECURSIVE upstream AS (
            SELECT source_id as id, 0 as depth
            FROM edges
            WHERE target_id = %s AND edge_type = 'FEEDS_INTO'
            
            UNION ALL
            
            SELECT e.source_id, u.depth + 1
            FROM edges e
            JOIN upstream u ON e.target_id = u.id
            WHERE u.depth < {depth}
        )
        SELECT DISTINCT n.id, n.name, n.node_type, u.depth
        FROM upstream u
        JOIN nodes n ON u.id = n.id
        ORDER BY u.depth
        '''
        
        self.cur.execute(query, (node_id,))
        results = self.cur.fetchall()
        
        # Fix: Properly unpack tuple results
        return {
            "root": node_id,
            "dependencies": [
                {"id": r[0], "name": r[1], "type": r[2], "depth": r[3]}
                for r in results
            ]
        }

if __name__ == "__main__":
    store = GraphStore()
    print("✓ GraphStore initialized")

