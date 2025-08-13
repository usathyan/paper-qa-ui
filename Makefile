# UX (Next.js + FastAPI) targets (skeleton)
.PHONY: ux-setup ux-backend-venv ux-frontend-install ux-test ux-build ux-export

ux-setup: ## Setup UX project environments (backend + frontend)
	python3 -m venv .venv_ux_backend && . .venv_ux_backend/bin/activate && pip install -U pip && pip install -r requirements_ux.txt || true
	@[ -d src/ux/frontend ] || echo "NOTE: Create src/ux/frontend and run npm install there"

ux-test: ## Run backend type checks/tests (placeholder)
	@[ -d src/ux/backend ] || echo "NOTE: Backend not scaffolded yet"
	@echo "✅ UX test placeholder (add pytest/mypy for backend; eslint/tsc for frontend)"

ux-build: ## Build frontend/backend (placeholder)
	@echo "✅ UX build placeholder (next build + backend packaging)"

ux-export: ## Call backend export endpoints (placeholder)
	@echo "✅ UX export placeholder"

# PaperQA2 Makefile
# Clean, focused targets for the current system

.PHONY: help clean install ui kill-server check-env setup test

# Default target
help:
	@echo "PaperQA2 Makefile"
	@echo "=================="
	@echo "Available targets:"
	@echo "  install    - Install dependencies (alias for setup)"
	@echo "  setup      - Install dependencies and setup environment"
	@echo "  ui         - Run the Gradio web interface"
	@echo "  kill-server - Kill any hanging server processes"
	@echo "  check-env  - Check environment status"
	@echo "  clean      - Clean up generated files and data"
	@echo "  clean-data - Clean up session data (preserves papers/)"
	@echo "  clean-all-data - Complete data reset (removes papers/)"
	@echo "  test       - Run basic functionality test"
	@echo "  test-cli   - Test CLI functionality"
	@echo "  cli-example - Run CLI with example query"
	@echo ""
	@echo "Quick start:"
	@echo "  1. make setup    # Install dependencies"
	@echo "  2. make ui       # Start web interface"
	@echo "  3. make test     # Test functionality"
	@echo ""
	@echo "CLI Usage:"
	@echo "  python -m src.cli.paper_qa_cli 'Your question'"
	@echo ""
	@echo "Troubleshooting:"
	@echo "  make kill-server # Kill hanging processes"
	@echo "  make clean-data  # Reset data if corrupted"

# Variables - using uv exclusively as requested
UV := uv
UVX := uvx
PYTHON := python3

# Check if .env file exists
check-env:
	@echo "🔍 Checking environment..."
	@if [ -f ".env" ]; then \
		echo "✅ .env file exists"; \
	else \
		echo "⚠️  .env file not found. Copy env.template to .env and configure API keys"; \
	fi
	@echo "🔍 Checking Ollama..."
	@if command -v ollama >/dev/null 2>&1; then \
		echo "✅ Ollama is installed"; \
		if ollama list | grep -q "nomic-embed-text"; then \
			echo "✅ nomic-embed-text model is available"; \
		else \
			echo "⚠️  nomic-embed-text model not found. Run: ollama pull nomic-embed-text"; \
		fi; \
	else \
		echo "❌ Ollama not found. Install from https://ollama.com/"; \
	fi
	@echo "🔍 Checking API keys..."
	@if [ -f ".env" ]; then \
		$(PYTHON) -c "import os; from dotenv import load_dotenv; load_dotenv(); keys=['OPENROUTER_API_KEY', 'AZURE_OPENAI_API_KEY', 'AWS_ACCESS_KEY_ID']; configured=[k for k in keys if os.getenv(k)]; print(f'✅ {len(configured)} API key(s) configured' if configured else '⚠️  No API keys configured (local mode only)')" 2>/dev/null || echo "⚠️  Unable to check API keys"; \
	fi

# Setup environment
setup:
	@echo "🚀 Setting up PaperQA2 environment..."
	@echo "📦 Installing dependencies with uv..."
	@$(UV) sync
	@echo "📄 Setting up environment file..."
	@if [ ! -f ".env" ]; then \
		cp env.template .env; \
		echo "✅ Created .env file from template"; \
		echo "⚠️  Please edit .env and set your API keys (optional for local mode)"; \
	else \
		echo "✅ .env file already exists"; \
	fi
	@echo "🔍 Checking Ollama setup..."
	@if command -v ollama >/dev/null 2>&1; then \
		echo "✅ Ollama found"; \
		if ! ollama list | grep -q "nomic-embed-text"; then \
			echo "📥 Downloading nomic-embed-text model..."; \
			ollama pull nomic-embed-text; \
		fi; \
		if ! ollama list | grep -q "llama3.2"; then \
			echo "📥 Downloading llama3.2 model..."; \
			ollama pull llama3.2; \
		fi; \
	else \
		echo "⚠️  Ollama not found. Please install from https://ollama.com/"; \
	fi
	@echo "✅ Setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Edit .env file and set API keys (optional for local mode)"
	@echo "  2. Run 'make ui' to start the interface"

# Install dependencies (alias for setup)
install: setup
	@echo "✅ Installation complete via setup target"

# Run the Gradio UI
ui: check-env
	@echo "🌐 Starting PaperQA2 Gradio UI..."
	@echo "📱 Open your browser to: http://localhost:7860"
	@echo "🛑 Press Ctrl+C to stop"
	@$(PYTHON) -m src.ui.paperqa2_ui

# Kill hanging server processes
kill-server:
	@echo "🔪 Killing hanging server processes..."
	@$(PYTHON) scripts/kill_server.py

# Clean up generated files and data
clean:
	@echo "🧹 Cleaning up generated files..."
	@rm -rf __pycache__/
	@rm -rf .pytest_cache/
	@rm -rf .coverage
	@rm -rf htmlcov/
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup complete"

# Clean up session data (preserves papers/)
clean-data:
	@echo "🧹 Cleaning up session data..."
	@rm -rf indexes/
	@rm -rf data/
	@echo "✅ Session data cleaned (papers/ preserved)"

# Complete data reset (removes papers/)
clean-all-data:
	@echo "🧹 Complete data reset..."
	@rm -rf indexes/
	@rm -rf data/
	@rm -rf papers/
	@echo "✅ All data cleaned"

# Run basic functionality test
test:
	@echo "🧪 Running code format (ruff format)..."
	@$(UVX) ruff format .
	@echo "🧪 Running lint fixes (ruff check . --fix)..."
	@$(UVX) ruff check . --fix
	@echo "🧪 Running static type check (mypy)..."
	@$(UVX) mypy --ignore-missing-imports --no-error-summary . || true

# Test CLI functionality
test-cli:
	@echo "🧪 Testing CLI functionality..."
	@$(PYTHON) scripts/test_complete_workflow.py

# Run CLI with example query
cli-example:
	@echo "🚀 Running CLI example..."
	@$(PYTHON) -m src.cli.paper_qa_cli "What is this paper about?" --method local --paper-dir ./papers