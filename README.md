# LineageGraph: Semantic Data Lineage Engine

A local-first, zero-cost AI-powered system for querying and understanding data lineage using natural language. Built with local LLMs, vector search, and graph databases.

## 🎯 Overview

LineageGraph enables users to ask natural language questions about data dependencies and lineage, such as:
- "What feeds into the revenue dashboard?"
- "Which tables are upstream dependencies of revenue_daily?"
- "Can you trace the complete data flow from orders to revenue?"

The system combines:
- **Vector Search** (DuckDB) for semantic similarity matching
- **Graph Database** (PostgreSQL) for dependency traversal
- **Local LLM** (Ollama) for natural language understanding
- **LangGraph Agent** for intelligent query planning and execution

## ✨ Features

- 🔍 **Natural Language Queries**: Ask questions about data lineage in plain English
- 🧠 **Intelligent Agent**: LangGraph-based agent that plans, investigates, and synthesizes answers
- 📊 **GraphRAG**: Grounds answers in structured graph data for accuracy
- 🔎 **Vector Search**: Semantic search over table descriptions and metadata
- 🎨 **Interactive Frontend**: React-based UI for querying and visualization
- 📈 **Evaluation Suite**: Comprehensive test harness with golden dataset
- 🔬 **Observability**: OpenTelemetry tracing for debugging and monitoring
- 💰 **Zero Cost**: Runs entirely locally, no API costs

## 🏗️ Architecture

```mermaid
graph TB
    subgraph Frontend["Frontend Layer"]
        UI[React UI<br/>Query Interface<br/>Port 5173]
    end
    
    subgraph Backend["Backend Layer"]
        API[FastAPI<br/>REST API<br/>Port 8000]
    end
    
    subgraph Agent["Agent Layer"]
        LangGraph[LangGraph Agent<br/>State Machine]
    end
    
    subgraph Services["Services"]
        LLM[Ollama LLM<br/>Mistral 7B]
        Vector[DuckDB<br/>Vector Search]
        Graph[PostgreSQL<br/>Graph Database]
    end
    
    UI -->|HTTP REST| API
    API --> LangGraph
    LangGraph --> LLM
    LangGraph --> Vector
    LangGraph --> Graph
    
    style Frontend fill:#e1f5ff
    style Backend fill:#fff4e1
    style Agent fill:#ffe1f5
    style Services fill:#e1ffe1
```

For detailed architecture documentation, see:
- [System Overview](docs/SYSTEM_OVERVIEW.md) - Visual architecture diagrams
- [Architecture Documentation](docs/ARCHITECTURE.md) - Detailed system architecture
- [Component Reference](docs/COMPONENTS.md) - Component details

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Ollama (for local LLM)
- Homebrew (macOS) or equivalent package manager

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yxshwanth/LieageGraph.git
   cd LineageGraph
   ```

2. **Install Python dependencies:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Install frontend dependencies:**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Set up services:**
   ```bash
   # Start PostgreSQL
   brew services start postgresql@15
   
   # Start Ollama
   brew services start ollama
   
   # Download Mistral model
   ollama pull mistral
   ```

5. **Load sample data:**
   ```bash
   source venv/bin/activate
   python src/graph/loader.py
   python src/vector/loader.py
   ```

### Running the Application

**Option 1: Using the management script (recommended)**
```bash
# Start infrastructure services
./scripts/manage.sh start

# Start backend (in terminal 1)
source venv/bin/activate
python src/main.py

# Start frontend (in terminal 2)
cd frontend
npm run dev
```

**Option 2: Using Make**
```bash
# Start infrastructure
make start

# Start backend
make backend

# Start frontend (in another terminal)
make frontend
```

**Option 3: Manual**
```bash
# Terminal 1: Backend
source venv/bin/activate
python src/main.py

# Terminal 2: Frontend
cd frontend
npm run dev
```

The application will be available at:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📖 Usage

### API Endpoint

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What feeds into the revenue dashboard?",
    "depth": 3
  }'
```

### Agent API

```python
from src.agents.graph import run_agent

result = run_agent("What feeds into the revenue dashboard?", verbose=True)
print(result["final_answer"])
```

### Frontend

Open http://localhost:5173 in your browser and use the query interface to ask questions about data lineage.

## 🧪 Testing

Run the test suite:

```bash
# All tests
pytest tests/ -v

# Unit tests
make test-unit

# Integration tests
make test-integration

# Evaluation pipeline
pytest tests/test_evaluation_pipeline.py -v
```

## 📁 Project Structure

```
LineageGraph/
├── src/
│   ├── agents/          # LangGraph agent implementation
│   │   ├── graph.py      # Agent graph definition
│   │   ├── nodes.py      # Agent nodes (plan, investigate, synthesize)
│   │   ├── tools.py      # Agent tools (vector search, graph queries)
│   │   └── state.py      # Agent state management
│   ├── graph/            # Graph database layer
│   │   ├── schema.py     # PostgreSQL schema and queries
│   │   └── loader.py     # Sample data loader
│   ├── vector/           # Vector search layer
│   │   ├── database.py   # DuckDB vector store
│   │   ├── embeddings.py # Sentence-transformers embedder
│   │   └── loader.py     # Sample data loader
│   └── main.py           # FastAPI application
├── frontend/              # React frontend
│   ├── src/
│   │   ├── App.jsx       # Main app component
│   │   └── components/   # UI components
├── tests/                 # Test suite
│   ├── test_agent_*.py   # Agent tests
│   ├── test_evaluation_pipeline.py  # Evaluation tests
│   └── data/             # Golden dataset
├── docs/                  # Documentation
├── scripts/               # Utility scripts
│   └── manage.sh         # Service management
└── requirements.txt       # Python dependencies
```

## 🔧 Configuration

### Environment Variables

```bash
# Database connection
export DATABASE_URL="postgresql://postgres:postgres@localhost/semantic_lineage"

# Enable OpenTelemetry tracing
export TRACING_ENABLED=true
```

### Service Management

See [SERVICE_MANAGEMENT.md](SERVICE_MANAGEMENT.md) for detailed service management instructions.

## 📊 Evaluation

The project includes a comprehensive evaluation harness:

- **Golden Dataset**: 20+ test cases covering various query types
- **Metrics**: Pass rate, node recall, answer relevance
- **Thresholds**: 70% pass rate, 70% node recall, 65% answer relevance

Run evaluation:
```bash
pytest tests/test_evaluation_pipeline.py -v
```

## 🛠️ Development

### Adding New Tools

1. Define the tool in `src/agents/tools.py`:
   ```python
   @tool("my_new_tool")
   def my_new_tool(param: str) -> Dict[str, Any]:
       """Tool description"""
       # Implementation
       return {"success": True, "result": ...}
   ```

2. Add to `ALL_TOOLS` in `src/agents/tools.py`

3. The agent will automatically discover and use it

### Adding New Data

1. **Graph data**: Use `src/graph/loader.py` as a template
2. **Vector data**: Use `src/vector/loader.py` as a template

## 🚢 CI/CD

GitHub Actions automatically runs:
- Unit tests
- Integration tests
- Evaluation pipeline (optional, slow)

See [.github/workflows/test.yml](.github/workflows/test.yml) for details.

## 📚 Documentation

- [System Overview](docs/SYSTEM_OVERVIEW.md) - Visual architecture diagrams and system overview
- [Architecture Documentation](docs/ARCHITECTURE.md) - Detailed system architecture with Mermaid diagrams
- [Component Reference](docs/COMPONENTS.md) - Detailed component documentation
- [Quick Start Guide](docs/QUICK_START.md) - Step-by-step setup instructions
- [Service Management](SERVICE_MANAGEMENT.md) - Service management guide
- [Agent Tracing](src/agents/TRACING_USAGE.md) - OpenTelemetry tracing usage

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai/) for local LLM inference
- [LangGraph](https://github.com/langchain-ai/langgraph) for agent orchestration
- [DuckDB](https://duckdb.org/) for vector search
- [PostgreSQL](https://www.postgresql.org/) for graph storage

## 📧 Support

For questions, issues, or contributions, please open an issue on GitHub.

---

**Built with ❤️ for zero-cost AI systems**

