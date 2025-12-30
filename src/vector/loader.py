import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from vector.database import VectorStore
from vector.embeddings import LocalEmbedder, SAMPLE_LINEAGE_DATA
from tqdm import tqdm

def load_sample_data():
    """Load sample lineage data with embeddings"""
    
    store = VectorStore()
    embedder = LocalEmbedder()
    
    print("Loading sample lineage data...")
    for item in tqdm(SAMPLE_LINEAGE_DATA, desc="Embedding and storing"):
        # Generate embedding
        embedding = embedder.embed_text(item["text"])
        
        # Store in vector DB
        store.add_embedding(
            id=item["id"],
            text=item["text"],
            embedding=embedding,
            table_name=item["table_name"],
            source_type=item["source_type"],
            column_names=None
        )
    
    print(f"✓ Loaded {len(SAMPLE_LINEAGE_DATA)} items")
    
    # Test search
    test_query = "What feeds into revenue?"
    query_embedding = embedder.embed_text(test_query)
    results = store.search(query_embedding, limit=3)
    
    print(f"\nSearch test: '{test_query}'")
    for r in results:
        print(f"  - {r['table_name']} ({r['similarity']:.2%})")

if __name__ == "__main__":
    load_sample_data()

