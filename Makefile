.PHONY: help start stop status restart backend frontend test clean

help: ## Show this help message
	@echo "LineageGraph Service Management"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

start: ## Start all infrastructure services (PostgreSQL, Ollama)
	@./scripts/manage.sh start

stop: ## Stop all services
	@./scripts/manage.sh stop

status: ## Show status of all services
	@./scripts/manage.sh status

restart: ## Restart all services
	@./scripts/manage.sh restart

backend: ## Start FastAPI backend server
	@echo "Starting FastAPI backend..."
	@cd $(shell pwd) && source venv/bin/activate && python src/main.py

frontend: ## Start frontend dev server
	@echo "Starting frontend dev server..."
	@cd frontend && npm run dev

test: ## Run all tests
	@echo "Running tests..."
	@pytest tests/ -v

test-eval: ## Run evaluation pipeline tests
	@echo "Running evaluation tests..."
	@pytest tests/test_evaluation_pipeline.py -v

test-unit: ## Run unit tests only
	@echo "Running unit tests..."
	@pytest tests/test_agent_tools.py tests/test_agent_graph.py -v

test-integration: ## Run integration tests only
	@echo "Running integration tests..."
	@pytest tests/test_week1_5_integration.py -v

clean: ## Clean up temporary files and caches
	@echo "Cleaning up..."
	@find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	@echo "Cleanup complete"

install: ## Install Python dependencies
	@echo "Installing Python dependencies..."
	@pip install -r requirements.txt

install-frontend: ## Install frontend dependencies
	@echo "Installing frontend dependencies..."
	@cd frontend && npm install

setup: install install-frontend ## Initial setup: install all dependencies
	@echo "Setup complete!"

