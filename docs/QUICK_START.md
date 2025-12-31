# Quick Start Guide

This guide will help you get LineageGraph up and running in minutes.

## Prerequisites Check

Before starting, ensure you have:

- ✅ Python 3.11 or higher
- ✅ Node.js 18 or higher
- ✅ PostgreSQL 15+ installed
- ✅ Homebrew (macOS) or equivalent package manager

Check versions:
```bash
python3 --version  # Should be 3.11+
node --version     # Should be 18+
psql --version     # Should be 15+
```

## Step-by-Step Setup

### 1. Clone and Navigate

```bash
git clone https://github.com/yxshwanth/LieageGraph.git
cd LineageGraph
```

### 2. Install Python Dependencies

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### 4. Set Up Services

#### PostgreSQL

```bash
# Start PostgreSQL
brew services start postgresql@15

# Verify it's running
brew services list | grep postgresql
```

#### Ollama

```bash
# Install Ollama (if not already installed)
brew install ollama

# Start Ollama service
brew services start ollama

# Download Mistral model (this may take a few minutes)
ollama pull mistral

# Verify model is available
ollama list
```

### 5. Load Sample Data

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Load graph data into PostgreSQL
python src/graph/loader.py

# Load vector data into DuckDB
python src/vector/loader.py
```

You should see:
```
✓ Graph schema initialized
✓ Loaded sample lineage
✓ Loaded embedding model: all-MiniLM-L6-v2
✓ Loaded 5 items
```

### 6. Start the Application

**Terminal 1 - Backend:**
```bash
source venv/bin/activate
python src/main.py
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
```

### 7. Test the Application

**Option 1: Using the Frontend**
1. Open http://localhost:5173 in your browser
2. Enter a query like "What feeds into the revenue dashboard?"
3. Click "Query" and see the results

**Option 2: Using curl**
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What feeds into the revenue dashboard?",
    "depth": 3
  }'
```

**Option 3: Using Python**
```python
from src.agents.graph import run_agent

result = run_agent("What feeds into the revenue dashboard?", verbose=False)
print(result["final_answer"])
```

## Verify Everything Works

### Check Services

```bash
# Check PostgreSQL
psql -d semantic_lineage -c "SELECT COUNT(*) FROM nodes;"
# Should return: 5

# Check Ollama
curl http://localhost:11434/api/tags
# Should return JSON with mistral model

# Check Backend
curl http://localhost:8000/health
# Should return: {"status":"ok"}
```

### Run Tests

```bash
source venv/bin/activate
pytest tests/test_agent_tools.py -v
```

All tests should pass.

## Troubleshooting

### PostgreSQL Connection Issues

**Problem**: `psycopg2.OperationalError: connection refused`

**Solution**:
```bash
# Check if PostgreSQL is running
brew services list | grep postgresql

# If not running, start it
brew services start postgresql@15

# Check connection
psql -d postgres
```

### Ollama Not Responding

**Problem**: `Connection refused` when calling Ollama

**Solution**:
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not responding, restart Ollama
brew services restart ollama

# Or start manually
ollama serve
```

### DuckDB Lock Errors

**Problem**: `Database locked` error

**Solution**:
- Make sure only one process is accessing the DuckDB file
- Stop any other Python processes using the database
- The database file is at: `semantic_lineage.duckdb`

### Port Already in Use

**Problem**: `Address already in use` for port 8000 or 5173

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
# For backend: Edit src/main.py, change port=8000
# For frontend: Edit frontend/vite.config.js
```

## Next Steps

- Read the [Architecture Documentation](ARCHITECTURE.md)
- Explore the [Service Management Guide](../SERVICE_MANAGEMENT.md)
- Check out the [Agent Tracing Documentation](../src/agents/TRACING_USAGE.md)

## Getting Help

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section above
2. Review the logs in your terminal
3. Open an issue on GitHub with:
   - Error messages
   - Steps to reproduce
   - Your environment (OS, Python version, etc.)

