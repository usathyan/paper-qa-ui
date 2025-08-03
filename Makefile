# Paper-QA Makefile
# Targets: clean, test, run, install

.PHONY: help clean test run install lint pytest setup check-env

# Default target
help:
	@echo "Paper-QA Makefile"
	@echo "=================="
	@echo "Available targets:"
	@echo "  install    - Install dependencies and setup environment"
	@echo "  test       - Run linting and pytest"
	@echo "  lint       - Run linting only"
	@echo "  pytest     - Run pytest only"
	@echo "  run        - Run the demo"
	@echo "  ui         - Run the Gradio web interface"
	@echo "  run-query  - Run custom query with QUESTION and METHOD"
	@echo "  run-local  - Run query on local papers only"
	@echo "  run-public - Run query on public sources only"
	@echo "  run-combined - Run query on both local and public sources"
	@echo "  clean      - Clean up generated files"
	@echo "  setup      - Setup environment and install dependencies"
	@echo "  check-env  - Check environment status"
	@echo "  test-rate-limits - Test rate limit handling"
	@echo ""
	@echo "Query examples:"
	@echo "  make run-query QUESTION='Your question' METHOD=local"
	@echo "  make run-query QUESTION='Your question' METHOD=public"
	@echo "  make run-query QUESTION='Your question' METHOD=combined"
	@echo "  make run-query QUESTION='Your question' METHOD=public CONFIG=public_only"
	@echo ""
	@echo "Parameters:"
	@echo "  QUESTION - Your research question (required)"
	@echo "  METHOD   - local, public, or combined (required)"
	@echo "  CONFIG   - default, local_only, public_only, or combined (optional)"

# Variables
PYTHON := .venv/bin/python
PIP := .venv/bin/pip
UV := uv
PYTEST := .venv/bin/pytest
BLACK := .venv/bin/black
ISORT := .venv/bin/isort
RUFF := .venv/bin/ruff

# Check if virtual environment exists
check-venv:
	@if [ ! -d ".venv" ]; then \
		echo "❌ Virtual environment not found. Run 'make setup' first."; \
		exit 1; \
	fi

# Check environment variables
check-env:
	@echo "🔍 Checking environment..."
	@if [ -f ".env" ]; then \
		echo "✅ .env file exists"; \
	else \
		echo "⚠️  .env file not found. Copy env.template to .env and configure."; \
	fi
	@$(PYTHON) -c "from src.utils import print_system_status; print_system_status()"

# Install dependencies
install: check-venv
	@echo "📦 Installing dependencies..."
	@$(UV) pip install -e .
	@echo "✅ Dependencies installed"

# Setup environment
setup:
	@echo "🚀 Setting up Paper-QA environment..."
	@$(PYTHON) scripts/setup.py
	@echo "✅ Setup complete"

# Run linting
lint: check-venv
	@echo "🔍 Running linting..."
	@echo "Running black..."
	@$(BLACK) --check src/ tests/ scripts/ || $(BLACK) src/ tests/ scripts/
	@echo "Running isort..."
	@$(ISORT) --check-only src/ tests/ scripts/ || $(ISORT) src/ tests/ scripts/
	@echo "Running ruff..."
	@$(RUFF) check src/ tests/ scripts/
	@echo "✅ Linting complete"

# Run pytest
pytest: check-venv
	@echo "🧪 Running pytest..."
	@$(PYTEST) tests/ -v --tb=short --asyncio-mode=auto
	@echo "✅ Pytest complete"

# Run all tests (linting + pytest)
test: check-venv lint pytest
	@echo "✅ All tests passed!"

# Run the demo
run: check-venv check-env
	@echo "🎬 Running Paper-QA demo..."
	@$(PYTHON) scripts/paper_qa_cli.py --demo

# Run the Gradio UI
ui: check-venv check-env
	@echo "🌐 Starting Paper-QA Gradio UI..."
	@echo "📱 Open your browser to: http://localhost:7860"
	@$(PYTHON) scripts/run_gradio_ui.py

# Run with custom question
run-query: check-venv check-env
	@echo "🔍 Running custom query..."
	@if [ -z "$(CONFIG)" ]; then \
		$(PYTHON) scripts/paper_qa_cli.py --question "$(QUESTION)" --method "$(METHOD)" --config "default"; \
	else \
		$(PYTHON) scripts/paper_qa_cli.py --question "$(QUESTION)" --method "$(METHOD)" --config "$(CONFIG)"; \
	fi

# Clean up generated files
clean:
	@echo "🧹 Cleaning up..."
	@rm -rf __pycache__/
	@rm -rf .pytest_cache/
	@rm -rf .coverage
	@rm -rf htmlcov/
	@rm -rf dist/
	@rm -rf build/
	@rm -rf *.egg-info/
	@rm -rf src/*.egg-info/
	@rm -rf .mypy_cache/
	@rm -rf .ruff_cache/
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@echo "✅ Cleanup complete"

# Deep clean (includes virtual environment)
clean-all: clean
	@echo "🧹 Deep cleaning (including virtual environment)..."
	@rm -rf .venv/
	@rm -rf indexes/
	@rm -rf results/
	@rm -f .env
	@echo "✅ Deep cleanup complete"

# Install development dependencies
install-dev: check-venv
	@echo "📦 Installing development dependencies..."
	@$(UV) pip install black isort ruff pytest pytest-asyncio pytest-cov
	@echo "✅ Development dependencies installed"

# Format code
format: check-venv
	@echo "🎨 Formatting code..."
	@$(BLACK) src/ tests/ scripts/
	@$(ISORT) src/ tests/ scripts/
	@echo "✅ Code formatting complete"

# Check code quality
quality: check-venv
	@echo "🔍 Checking code quality..."
	@$(RUFF) check src/ tests/ scripts/ --fix
	@echo "✅ Code quality check complete"

# Run with specific configuration
run-local: check-venv check-env
	@echo "📚 Running with local papers..."
	@$(PYTHON) scripts/paper_qa_cli.py --question "$(QUESTION)" --method local --config local_only

run-public: check-venv check-env
	@echo "🌐 Running with public sources..."
	@$(PYTHON) scripts/paper_qa_cli.py --question "$(QUESTION)" --method public --config public_only

run-combined: check-venv check-env
	@echo "🔄 Running with combined sources..."
	@$(PYTHON) scripts/paper_qa_cli.py --question "$(QUESTION)" --method combined --config combined

# Quick status check
status: check-venv
	@echo "📊 System Status:"
	@$(PYTHON) scripts/paper_qa_cli.py --status

# Test rate limit handling
test-rate-limits: check-venv check-env
	@echo "🧪 Testing rate limit handling..."
	@$(PYTHON) scripts/test_rate_limits.py

# Show help for running queries
help-run:
	@echo "Usage examples:"
	@echo "  make run                                    # Run demo"
	@echo "  make run-query QUESTION='Your question' METHOD=public"
	@echo "  make run-local QUESTION='Your question'"
	@echo "  make run-public QUESTION='Your question'"
	@echo "  make run-combined QUESTION='Your question'"
	@echo "  make test-rate-limits                       # Test rate limit handling"
	@echo ""
	@echo "Available methods: local, public, combined"
	@echo "Available configs: default, local_only, public_only, combined" 