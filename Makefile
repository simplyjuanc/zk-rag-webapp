.PHONY: help install test run-pipeline run-test clean

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -e .

test: ## Run pipeline tests
	python -m libs.pipeline.test_pipeline

run-pipeline: ## Run the data pipeline
	python scripts/run_pipeline.py

run-test: ## Run a quick test of the pipeline components
	python -c "import asyncio; from libs.pipeline.test_pipeline import main; asyncio.run(main())"

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

setup-ollama: ## Setup Ollama with required models
	@echo "Setting up Ollama..."
	@echo "1. Make sure Ollama is installed and running"
	@echo "2. Pull the embedding model:"
	ollama pull nomic-embed-text
	@echo "3. Start Ollama server:"
	@echo "   ollama serve"

check-ollama: ## Check if Ollama is running and accessible
	@echo "Checking Ollama connection..."
	@curl -s http://localhost:11434/api/tags > /dev/null && echo "✓ Ollama is running" || echo "✗ Ollama is not running or not accessible"

dev-setup: ## Setup development environment
	@echo "Setting up development environment..."
	pip install -e .
	@echo "✓ Dependencies installed"
	@echo "Run 'make setup-ollama' to setup Ollama models"
	@echo "Run 'make run-pipeline' to start the pipeline" 