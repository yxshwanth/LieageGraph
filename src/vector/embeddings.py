"""
Local embedding generation module.

This module provides a LocalEmbedder class that uses sentence-transformers
to generate embeddings locally without requiring external API calls.
"""

from sentence_transformers import SentenceTransformer
from typing import List
import os

class LocalEmbedder:
    """Generate embeddings using local sentence-transformers model"""
    
    """
    Local embedding generator using sentence-transformers.
    
    Generates embeddings for text using a local model, avoiding the need
    for external API calls. Uses the all-MiniLM-L6-v2 model by default,
    which provides a good balance of speed and quality.
    
    Attributes:
        model_name: Name of the sentence-transformers model
        model: Loaded SentenceTransformer model instance
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedder with sentence-transformers model.
        
        Args:
            model_name: Name of the sentence-transformers model to use.
                       Default: 'all-MiniLM-L6-v2' (384 dimensions, fast, good quality)
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        print(f"✓ Loaded embedding model: {model_name} (dimension: {self.model.get_sentence_embedding_dimension()})")
    
    def embed_text(self, text: str) -> List[float]:
        """
        Embed a single text string.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple texts efficiently.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

# Sample lineage data for testing and demonstration
SAMPLE_LINEAGE_DATA = [
    {
        "id": "table_users",
        "text": "Users table contains user_id, email, name, created_at. Source system: production_db",
        "table_name": "users",
        "source_type": "source"
    },
    {
        "id": "table_orders",
        "text": "Orders table contains order_id, user_id, amount, order_date. Source system: production_db",
        "table_name": "orders",
        "source_type": "source"
    },
    {
        "id": "table_order_clean",
        "text": "Cleaned orders data with validation, deduplication. Transforms: order_raw -> order_clean",
        "table_name": "order_clean",
        "source_type": "transform"
    },
    {
        "id": "table_revenue_daily",
        "text": "Daily revenue aggregated by date. Depends on: order_clean, users. Aggregates to revenue per day",
        "table_name": "revenue_daily",
        "source_type": "transform"
    },
    {
        "id": "dashboard_revenue",
        "text": "Revenue dashboard displays daily revenue trends. Depends on: revenue_daily",
        "table_name": "revenue_dashboard",
        "source_type": "dashboard"
    }
]

if __name__ == "__main__":
    embedder = LocalEmbedder()
    
    # Test embedding
    test_text = "What feeds into the revenue dashboard?"
    embedding = embedder.embed_text(test_text)
    print(f"✓ Embedded text (dimension: {len(embedding)})")
    print(f"  Sample values: {embedding[:5]}")

