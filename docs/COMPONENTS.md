# Component Reference

Detailed documentation for each component in the LineageGraph system.

## Agent Components

### Agent Graph (`src/agents/graph.py`)

The main agent orchestration system using LangGraph.

**Key Functions**:
- `create_agent_graph()`: Creates the LangGraph state machine
- `run_agent(query, verbose=False)`: Main entry point for agent execution

**Graph Structure**:
```
START → plan → investigate → tool → check_continue
                              ↓
                         [loop back or]
                              ↓
                         synthesize → END
```

### Agent Nodes (`src/agents/nodes.py`)

Individual nodes in the agent graph:

1. **plan_node(state)**
   - Analyzes user query
   - Creates execution plan
   - Determines required information

2. **investigate_node(state)**
   - Selects appropriate tools
   - Prepares tool inputs
   - Decides investigation strategy

3. **synthesize_node(state)**
   - Combines tool results
   - Generates final answer using LLM
   - Calculates confidence score

### Agent State (`src/agents/state.py`)

Type definitions for agent state:

```python
class AgentState(TypedDict):
    user_query: str
    current_step: str
    plan: str
    next_tool: str
    tool_results: Dict[str, Any]
    final_answer: str
    confidence_score: float
    step_count: int
    tool_calls_made: List[str]
```

### Agent Tools (`src/agents/tools.py`)

Tools available to the agent:

#### 1. search_vector_db

**Purpose**: Semantic search over table descriptions

**Input**:
```python
{
    "query": "What feeds into revenue?",
    "limit": 3
}
```

**Output**:
```python
{
    "success": True,
    "count": 3,
    "items": [
        {
            "id": "table_revenue_daily",
            "table_name": "revenue_daily",
            "text": "...",
            "similarity": 0.85
        },
        ...
    ]
}
```

#### 2. get_table_dependencies

**Purpose**: Get upstream dependencies of a table

**Input**:
```python
{
    "table_id": "dashboard_revenue",
    "depth": 3
}
```

**Output**:
```python
{
    "success": True,
    "dependencies": [
        {
            "id": "table_revenue_daily",
            "name": "revenue_daily",
            "type": "Table",
            "depth": 0
        },
        ...
    ]
}
```

#### 3. validate_lineage_path

**Purpose**: Validate if a path exists between two nodes

**Input**:
```python
{
    "source_id": "table_orders",
    "target_id": "dashboard_revenue"
}
```

**Output**:
```python
{
    "success": True,
    "is_valid": True,
    "path_length": 3
}
```

#### 4. get_node_metadata

**Purpose**: Get metadata for a specific node

**Input**:
```python
{
    "node_id": "table_users"
}
```

**Output**:
```python
{
    "success": True,
    "node": {
        "id": "table_users",
        "name": "users",
        "type": "Table",
        "description": "..."
    }
}
```

#### 5. trace_data_flow

**Purpose**: Trace complete data flow path

**Input**:
```python
{
    "start_node": "table_orders",
    "end_node": "dashboard_revenue"
}
```

**Output**:
```python
{
    "success": True,
    "path": [
        "table_orders",
        "table_order_clean",
        "table_revenue_daily",
        "dashboard_revenue"
    ]
}
```

#### 6. check_data_freshness

**Purpose**: Check data freshness score

**Input**:
```python
{
    "table_id": "table_users"
}
```

**Output**:
```python
{
    "success": True,
    "freshness_score": 0.95,
    "last_updated": "2024-01-01T00:00:00Z"
}
```

## Storage Components

### Vector Store (`src/vector/database.py`)

DuckDB-based vector database for semantic search.

**Key Methods**:
- `add_embedding(id, text, embedding, table_name, source_type)`: Store embedding
- `search(query_embedding, limit=3)`: Search for similar embeddings

**Schema**:
- `embeddings` table: Text and metadata
- `vectors` table: Embedding vectors

### Graph Store (`src/graph/schema.py`)

PostgreSQL-based graph database for lineage relationships.

**Key Methods**:
- `add_node(id, node_type, name, description)`: Add a node
- `add_edge(source_id, target_id, edge_type)`: Add a relationship
- `get_dependencies(node_id, depth)`: Get upstream dependencies

**Schema**:
- `nodes` table: Graph nodes
- `edges` table: Graph relationships

### Embedder (`src/vector/embeddings.py`)

Sentence-transformers based embedder.

**Model**: `all-MiniLM-L6-v2` (384 dimensions)

**Key Methods**:
- `embed_text(text)`: Generate embedding for text
- `embed_batch(texts)`: Generate embeddings for multiple texts

## API Components

### FastAPI Application (`src/main.py`)

Main FastAPI application.

**Endpoints**:
- `GET /health`: Health check
- `POST /api/query`: Execute lineage query

**Request/Response Models**:
- `QueryRequest`: Input model
- `QueryResponse`: Output model

## Frontend Components

### Query Interface (`frontend/src/components/QueryInterface.jsx`)

Main query interface component.

**Features**:
- Natural language query input
- Results display
- Error handling

### API Client (`frontend/src/api/client.js`)

HTTP client for backend communication.

**Methods**:
- `queryLineage(query, depth)`: Send query to backend

## Utility Components

### Service Management (`scripts/manage.sh`)

Bash script for managing services.

**Commands**:
- `start`: Start all services
- `stop`: Stop all services
- `status`: Check service status
- `restart`: Restart all services

### Tracing (`src/agents/tracing.py`)

OpenTelemetry tracing support.

**Features**:
- Agent execution tracing
- Tool call tracing
- LLM inference tracing

**Usage**:
```bash
export TRACING_ENABLED=true
# Traces sent to Jaeger at http://localhost:16686
```

## Data Loaders

### Graph Loader (`src/graph/loader.py`)

Loads sample lineage data into PostgreSQL.

**Sample Data**:
- 5 nodes (users, orders, order_clean, revenue_daily, revenue_dashboard)
- 4 edges (lineage relationships)

### Vector Loader (`src/vector/loader.py`)

Loads sample embeddings into DuckDB.

**Sample Data**:
- 5 table descriptions
- Embeddings for each description

## Testing Components

### Evaluation Harness (`tests/eval_harness.py`)

Comprehensive evaluation system.

**Features**:
- Golden dataset evaluation
- Node recall calculation
- Answer relevance scoring
- Pass rate metrics

### Test Suites

- `test_agent_tools.py`: Unit tests for agent tools
- `test_agent_graph.py`: Tests for agent graph
- `test_week1_5_integration.py`: Integration tests
- `test_evaluation_pipeline.py`: Evaluation pipeline tests

## Configuration

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `TRACING_ENABLED`: Enable/disable OpenTelemetry tracing

### Configuration Files

- `requirements.txt`: Python dependencies
- `frontend/package.json`: Frontend dependencies
- `.github/workflows/test.yml`: CI/CD configuration

