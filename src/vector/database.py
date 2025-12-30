"""
Vector database module for storing and searching embeddings.

This module provides a VectorStore class that uses DuckDB to store
text embeddings and metadata, enabling semantic search over data lineage
descriptions.
"""

import duckdb
import json
from typing import List, Dict
from pathlib import Path

class VectorStore:
    """
    Vector store for semantic search over data lineage metadata.
    
    Uses DuckDB to store embeddings and metadata, with cosine similarity
    search for finding relevant tables, transformations, and dashboards.
    
    Attributes:
        db_path: Path to the DuckDB database file
        conn: DuckDB connection object
    """
    def __init__(self, db_path: str = "semantic_lineage.duckdb"):
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
        self._init_schema()
    
    def _init_schema(self):
        """
        Initialize the database schema.
        
        Creates two tables:
        - embeddings: Stores text and metadata
        - vectors: Stores embedding vectors (DOUBLE[])
        """
        
        # Create embeddings table
        self.conn.execute('''
        CREATE TABLE IF NOT EXISTS embeddings (
            id VARCHAR PRIMARY KEY,
            text VARCHAR,
            table_name VARCHAR,
            column_names VARCHAR,
            source_type VARCHAR,  -- 'source', 'transform', 'dashboard'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create vector table (separate for performance)
        self.conn.execute('''
        CREATE TABLE IF NOT EXISTS vectors (
            id VARCHAR PRIMARY KEY,
            embedding DOUBLE[],
            FOREIGN KEY (id) REFERENCES embeddings(id)
        )
        ''')
        
        print("✓ Vector schema initialized")
    
    def add_embedding(self, 
                     id: str,
                     text: str,
                     embedding: List[float],
                     table_name: str,
                     source_type: str,
                     column_names: str = None):
        """
        Add an embedding to the vector store.
        
        Args:
            id: Unique identifier for the embedding
            text: Text description of the table/transformation
            embedding: Embedding vector (list of floats)
            table_name: Name of the table
            source_type: Type of source ('source', 'transform', 'dashboard')
            column_names: Optional column names (default: None)
        """
        
        self.conn.execute(
            '''INSERT OR REPLACE INTO embeddings 
               (id, text, table_name, column_names, source_type) 
               VALUES (?, ?, ?, ?, ?)''',
            [id, text, table_name, column_names, source_type]
        )
        
        # DuckDB can handle Python lists directly for array columns
        self.conn.execute(
            '''INSERT OR REPLACE INTO vectors (id, embedding) 
               VALUES (?, ?)''',
            [id, embedding]
        )
        
        self.conn.commit()
    
    def search(self, 
              query_embedding: List[float],
              limit: int = 5) -> List[Dict]:
        """
        Search for similar embeddings using cosine similarity.
        
        Args:
            query_embedding: Query embedding vector
            limit: Maximum number of results to return
            
        Returns:
            List of dictionaries containing:
            - id: Embedding ID
            - text: Original text
            - table_name: Table name
            - source_type: Source type
            - similarity: Cosine similarity score (0-1)
        """
        
        # Fetch all vectors and compute cosine similarity in Python
        # This is more reliable than trying to do it in SQL
        results = self.conn.execute('''
        SELECT 
            e.id,
            e.text,
            e.table_name,
            e.source_type,
            v.embedding
        FROM vectors v
        JOIN embeddings e ON v.id = e.id
        ''').fetchall()
        
        # Compute cosine similarity for each result
        scored_results = []
        query_norm = sum(x * x for x in query_embedding) ** 0.5
        
        for r in results:
            stored_embedding = r[4]  # This is a list from DuckDB
            if stored_embedding and len(stored_embedding) == len(query_embedding):
                dot_product = sum(a * b for a, b in zip(stored_embedding, query_embedding))
                stored_norm = sum(x * x for x in stored_embedding) ** 0.5
                similarity = dot_product / (query_norm * stored_norm) if (query_norm * stored_norm) > 0 else 0.0
                
                scored_results.append({
                    "id": r[0],
                    "text": r[1],
                    "table_name": r[2],
                    "source_type": r[3],
                    "similarity": similarity
                })
        
        # Sort by similarity and return top results
        scored_results.sort(key=lambda x: x["similarity"], reverse=True)
        return scored_results[:limit]

# Test it
if __name__ == "__main__":
    store = VectorStore()
    print("✓ VectorStore initialized")

