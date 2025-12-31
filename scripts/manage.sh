#!/bin/bash
# Service management script for LineageGraph project
# Usage: ./scripts/manage.sh [start|stop|status|restart]

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Function to check if a service is running
check_service() {
    local service=$1
    local check_cmd=$2
    
    if eval "$check_cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $service is running"
        return 0
    else
        echo -e "${RED}✗${NC} $service is not running"
        return 1
    fi
}

# Function to start all services
start_all() {
    echo -e "${YELLOW}Starting LineageGraph services...${NC}\n"
    
    # Start PostgreSQL
    echo "Starting PostgreSQL..."
    if brew services list | grep -q "postgresql.*started"; then
        echo -e "${GREEN}✓${NC} PostgreSQL already running"
    else
        brew services start postgresql@15 || brew services start postgresql
        sleep 2
    fi
    
    # Start Ollama
    echo "Starting Ollama..."
    if pgrep -x "ollama" > /dev/null; then
        echo -e "${GREEN}✓${NC} Ollama already running"
    else
        brew services start ollama || ollama serve > /dev/null 2>&1 &
        sleep 2
    fi
    
    # Check if Ollama model is available
    echo "Checking Ollama model..."
    if ollama list | grep -q "mistral"; then
        echo -e "${GREEN}✓${NC} Mistral model available"
    else
        echo -e "${YELLOW}⚠${NC} Mistral model not found. Run: ollama pull mistral"
    fi
    
    echo -e "\n${GREEN}All services started!${NC}"
    echo -e "\nTo start the backend server:"
    echo "  cd $PROJECT_ROOT && source venv/bin/activate && python src/main.py"
    echo -e "\nTo start the frontend (in another terminal):"
    echo "  cd $PROJECT_ROOT/frontend && npm run dev"
}

# Function to stop all services
stop_all() {
    echo -e "${YELLOW}Stopping LineageGraph services...${NC}\n"
    
    # Stop FastAPI server (if running)
    echo "Stopping FastAPI server..."
    pkill -f "python.*src/main.py" || pkill -f "uvicorn" || true
    echo -e "${GREEN}✓${NC} FastAPI server stopped"
    
    # Stop frontend dev server (if running)
    echo "Stopping frontend dev server..."
    pkill -f "vite" || pkill -f "npm.*dev" || true
    echo -e "${GREEN}✓${NC} Frontend dev server stopped"
    
    # Stop Ollama
    echo "Stopping Ollama..."
    brew services stop ollama || pkill ollama || true
    sleep 1
    echo -e "${GREEN}✓${NC} Ollama stopped"
    
    # Stop PostgreSQL (optional - comment out if you want to keep it running)
    echo "Stopping PostgreSQL..."
    read -p "Stop PostgreSQL? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        brew services stop postgresql@15 || brew services stop postgresql || true
        echo -e "${GREEN}✓${NC} PostgreSQL stopped"
    else
        echo -e "${YELLOW}⚠${NC} PostgreSQL kept running"
    fi
    
    echo -e "\n${GREEN}All services stopped!${NC}"
}

# Function to show status
show_status() {
    echo -e "${YELLOW}LineageGraph Service Status${NC}\n"
    
    # Check PostgreSQL
    check_service "PostgreSQL" "psql -h localhost -U postgres -d semantic_lineage -c 'SELECT 1' > /dev/null 2>&1 || psql -h localhost -d semantic_lineage -c 'SELECT 1' > /dev/null 2>&1"
    
    # Check Ollama
    check_service "Ollama" "curl -s http://localhost:11434/api/tags > /dev/null"
    
    # Check FastAPI backend
    check_service "FastAPI Backend" "curl -s http://localhost:8000/health > /dev/null"
    
    # Check Frontend
    check_service "Frontend Dev Server" "curl -s http://localhost:5173 > /dev/null"
    
    # Check DuckDB file
    if [ -f "$PROJECT_ROOT/semantic_lineage.duckdb" ]; then
        echo -e "${GREEN}✓${NC} DuckDB database file exists"
    else
        echo -e "${YELLOW}⚠${NC} DuckDB database file not found"
    fi
    
    echo ""
}

# Function to restart all services
restart_all() {
    echo -e "${YELLOW}Restarting LineageGraph services...${NC}\n"
    stop_all
    sleep 2
    start_all
}

# Main script logic
case "${1:-}" in
    start)
        start_all
        ;;
    stop)
        stop_all
        ;;
    status)
        show_status
        ;;
    restart)
        restart_all
        ;;
    *)
        echo "Usage: $0 [start|stop|status|restart]"
        echo ""
        echo "Commands:"
        echo "  start    - Start all required services (PostgreSQL, Ollama)"
        echo "  stop     - Stop all services"
        echo "  status   - Show status of all services"
        echo "  restart  - Restart all services"
        exit 1
        ;;
esac

