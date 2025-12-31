# Service Management Guide

This guide explains how to start, stop, and manage all services for the LineageGraph project.

## Quick Start

### Using the Management Script

```bash
# Check status of all services
./scripts/manage.sh status

# Start all services (PostgreSQL, Ollama)
./scripts/manage.sh start

# Stop all services
./scripts/manage.sh stop

# Restart everything
./scripts/manage.sh restart
```

## Services Overview

The project uses the following services:

1. **PostgreSQL** - Graph database (port 5432)
2. **Ollama** - Local LLM service (port 11434)
3. **FastAPI Backend** - Python API server (port 8000)
4. **Frontend Dev Server** - Vite/React (port 5173)
5. **DuckDB** - File-based vector database (no service needed)

## Manual Service Management

### PostgreSQL

```bash
# Start
brew services start postgresql@15
# or
brew services start postgresql

# Stop
brew services stop postgresql@15
# or
brew services stop postgresql

# Check status
brew services list | grep postgresql

# Connect to database
psql -d semantic_lineage
```

### Ollama

```bash
# Start (as background service)
brew services start ollama

# Start (manual, foreground)
ollama serve

# Stop
brew services stop ollama
# or
pkill ollama

# Check if running
curl http://localhost:11434/api/tags

# Pull model (if not already downloaded)
ollama pull mistral

# List available models
ollama list
```

### FastAPI Backend

```bash
# Start (from project root)
cd <project-root>
source venv/bin/activate
python src/main.py

# Stop
# Press Ctrl+C, or:
pkill -f "python.*src/main.py"
```

### Frontend Dev Server

```bash
# Start (from frontend directory)
cd frontend
npm run dev

# Stop
# Press Ctrl+C, or:
pkill -f "vite"
```

## Complete Startup Sequence

1. **Start infrastructure services:**
   ```bash
   ./scripts/manage.sh start
   ```

2. **Start backend (in terminal 1):**
   ```bash
   source venv/bin/activate
   python src/main.py
   ```

3. **Start frontend (in terminal 2):**
   ```bash
   cd frontend
   npm run dev
   ```

## Complete Shutdown Sequence

1. **Stop application servers:**
   - Press `Ctrl+C` in backend terminal
   - Press `Ctrl+C` in frontend terminal

2. **Stop infrastructure services:**
   ```bash
   ./scripts/manage.sh stop
   ```

## Checking Service Health

### Quick Health Check

```bash
./scripts/manage.sh status
```

### Manual Checks

```bash
# PostgreSQL
psql -d semantic_lineage -c "SELECT 1"

# Ollama
curl http://localhost:11434/api/tags

# FastAPI Backend
curl http://localhost:8000/health

# Frontend
curl http://localhost:5173
```

## Troubleshooting

### PostgreSQL won't start
```bash
# Check if port is already in use
lsof -i :5432

# Check PostgreSQL logs
brew services info postgresql@15
```

### Ollama not responding
```bash
# Restart Ollama
brew services restart ollama

# Check if model is available
ollama list

# Pull model if missing
ollama pull mistral
```

### Port conflicts
```bash
# Check what's using a port
lsof -i :8000   # FastAPI
lsof -i :5173   # Frontend
lsof -i :11434  # Ollama
lsof -i :5432   # PostgreSQL

# Kill process using a port
kill -9 <PID>
```

## Development Workflow

### Daily Development
1. `./scripts/manage.sh start` - Start infrastructure
2. Start backend and frontend in separate terminals
3. Work on your code
4. Stop backend/frontend with `Ctrl+C` when done
5. `./scripts/manage.sh stop` - Stop infrastructure (optional, PostgreSQL can stay running)

### Testing
```bash
# Make sure services are running
./scripts/manage.sh status

# Run tests
pytest tests/ -v
```

### Evaluation
```bash
# Ensure all services are running
./scripts/manage.sh start

# Run evaluation
pytest tests/test_evaluation_pipeline.py -v
```

## Notes

- **PostgreSQL**: Can stay running between sessions (low resource usage)
- **Ollama**: Uses significant memory (~4-8GB for mistral model). Stop when not needed.
- **DuckDB**: File-based, no service needed. File: `semantic_lineage.duckdb`
- **FastAPI/Frontend**: Start only when actively developing/testing

## Environment Variables

The following environment variables can be set:

```bash
# Database connection
export DATABASE_URL="postgresql://postgres:postgres@localhost/semantic_lineage"

# Enable tracing (optional)
export TRACING_ENABLED=true
```

