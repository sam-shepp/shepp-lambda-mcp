.PHONY: help install install-dev test lint format clean build deploy-lambda run-local

help:
	@echo "Simple Tools MCP Server - Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  install       - Install package in production mode"
	@echo "  install-dev   - Install package with dev dependencies"
	@echo "  test          - Run tests with pytest"
	@echo "  lint          - Run linting (ruff, mypy)"
	@echo "  format        - Format code with black"
	@echo "  clean         - Remove build artifacts"
	@echo "  build         - Build package for distribution"
	@echo "  deploy-lambda - Deploy to AWS Lambda (requires SAM)"
	@echo "  run-local     - Run as standalone MCP server"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --cov=simple_tools_mcp --cov-report=term-missing

lint:
	ruff check src/ tests/
	mypy src/

format:
	black src/ tests/

clean:
	rm -rf build/ dist/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

deploy-lambda:
	cd .. && sam build && sam deploy

run-local:
	python -m simple_tools_mcp.server
