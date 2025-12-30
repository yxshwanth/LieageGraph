"""
Semantic Lineage Engine - FastAPI Application

This module provides the main FastAPI application that orchestrates
vector search, graph queries, and LLM inference to answer natural
language questions about data lineage.

The application combines:
- Vector search (DuckDB) for semantic similarity
- Graph queries (PostgreSQL) for dependency traversal
- Local LLM (Ollama) for natural language understanding
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import os

import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from vector.database import VectorStore
from vector.embeddings import LocalEmbedder
from graph.schema import GraphStore

app = FastAPI(title="Semantic Lineage Engine")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
vector_store = VectorStore()
embedder = LocalEmbedder()
graph_store = GraphStore()

# Request/Response models
class QueryRequest(BaseModel):
    """Request model for lineage queries."""
    query: str
    depth: int = 3

class QueryResponse(BaseModel):
    """Response model for lineage queries."""
    query: str
    answer: str
    context_docs: List[Dict]
    lineage_path: Dict
    confidence: float

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok"}

@app.post("/api/query")
async def query_lineage(request: QueryRequest) -> QueryResponse:
    """
    Main endpoint: natural language query → lineage answer
    """
    try:
        # Step 1: Embed the query
        query_embedding = embedder.embed_text(request.query)
        
        # Step 2: Vector search for relevant context
        context_docs = vector_store.search(query_embedding, limit=3)
        
        # Step 3: Build context for LLM
        context_text = "\n".join([
            f"- {doc['table_name']}: {doc['text']}"
            for doc in context_docs
        ])
        
        # Step 4: If we identified a target table, fetch its lineage
        # For now, we'll assume the most relevant doc is the target
        if context_docs:
            # Fix: context_docs is a list, access first element
            target_table_name = context_docs[0]['table_name']
            # Find the node ID (this is a simple mapping)
            target_id = f"table_{target_table_name}"
            
            lineage_path = graph_store.get_dependencies(target_id, request.depth)
        else:
            lineage_path = {"root": "", "dependencies": []}
        
        # Step 5: Call local LLM with context
        llm_prompt = f"""
You are a data lineage expert. Answer the user's question about data dependencies.

Query: {request.query}

Related data:
{context_text}

Lineage context (what feeds into the target):
{lineage_path}

Based on this information, answer the query concisely:
        """
        
        answer = call_local_llm(llm_prompt)
        
        # Fix: Get confidence from first context doc if available
        confidence = context_docs[0]['similarity'] if context_docs else 0.0
        
        return QueryResponse(
            query=request.query,
            answer=answer,
            context_docs=context_docs,
            lineage_path=lineage_path,
            confidence=confidence
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def call_local_llm(prompt: str) -> str:
    """
    Call Ollama API for LLM inference.
    
    Args:
        prompt: The prompt to send to the LLM
        
    Returns:
        The LLM's response text
        
    Raises:
        Exception: If the API call fails or returns non-200 status
    """
    import requests
    
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "mistral",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,  # Lower temperature for factual answers
            }
        },
        timeout=60
    )
    
    if response.status_code != 200:
        raise Exception(f"LLM error: {response.text}")
    
    return response.json()['response']

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

