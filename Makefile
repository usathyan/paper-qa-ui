# PaperQA2 Makefile
# Clean, focused targets for the current system

.PHONY: help clean install ui kill-server check-env setup test lint format

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
	@echo "  test       - Run tests (if available)"
	@echo "  test-cli   - Test CLI functionality"
	@echo "  cli-example - Run CLI with example query"
	@echo "  cli-demo   - Show CLI demo and usage"
	@echo "  lint       - Run code linting"
	@echo "  format     - Format code"
	@echo ""
	@echo "Quick start:"
	@echo "  1. make setup    # Install dependencies"
	@echo "  2. make ui       # Start web interface"
	@echo "  3. make test-cli # Test CLI functionality"
	@echo ""
	@echo "CLI Usage:"
	@echo "  paper-qa-cli 'Your question' --paper-dir ./papers"
	@echo "  python scripts/paper_qa_cli.py 'Your question'"
	@echo ""
	@echo "Troubleshooting:"
	@echo "  make kill-server # Kill hanging processes"
	@echo "  make clean-data  # Reset data if corrupted"

# Variables - using uv exclusively as requested
UV := uv
PYTHON := python3

# Check if .env file exists
check-env:
	@echo "🔍 Checking environment..."
	@if [ -f ".env" ]; then \
		echo "✅ .env file exists"; \
	else \
		echo "⚠️  .env file not found. Copy env.template to .env and configure OPENROUTER_API_KEY"; \
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
	@echo "🔍 Checking OpenRouter connectivity..."
	@if [ -f ".env" ]; then \
		$(PYTHON) -c "import os; from dotenv import load_dotenv; load_dotenv(); print('✅ OPENROUTER_API_KEY configured' if os.getenv('OPENROUTER_API_KEY') else '⚠️  OPENROUTER_API_KEY not set in .env')" 2>/dev/null || echo "⚠️  Unable to check API key"; \
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
		echo "⚠️  Please edit .env and set your OPENROUTER_API_KEY"; \
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
	else \
		echo "⚠️  Ollama not found. Please install from https://ollama.com/"; \
	fi
	@echo "✅ Setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Edit .env file and set OPENROUTER_API_KEY"
	@echo "  2. Run 'make ui' to start the interface"

# Install dependencies (alias for setup)
install: setup
	@echo "✅ Installation complete via setup target"

# Run the Gradio UI
ui: check-env
	@echo "🌐 Starting PaperQA2 Gradio UI..."
	@echo "📱 Open your browser to: http://localhost:7860"
	@echo "🛑 Press Ctrl+C to stop"
	@$(PYTHON) src/paperqa2_ui.py

# Kill hanging server processes
kill-server:
	@echo "🔪 Killing hanging server processes..."
	@$(PYTHON) scripts/kill_server.py

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
	@rm -rf .gradio/
	@rm -f .env.local
	@rm -f .env.backup
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type f -name "*.log" -delete
	@find . -type f -name "*.tmp" -delete
	@echo "✅ Cleanup complete"

# Clean data files only (papers and indexes)
clean-data:
	@echo "🗂️  Cleaning data files..."
	@echo "  Removing session directories..."
	@if [ -d "papers/" ]; then \
		find papers/ -name "session_*" -type d -exec rm -rf {} + 2>/dev/null || true; \
	fi
	@if [ -d "indexes/" ]; then \
		rm -rf indexes/; \
	fi
	@echo "✅ Data cleanup complete (preserved non-session files in papers/)"

# Complete data reset (removes everything including papers/)
clean-all-data:
	@echo "🗂️  Complete data reset..."
	@rm -rf papers/
	@rm -rf indexes/
	@echo "✅ All data removed (including papers/)"

# Deep clean (includes virtual environment and data)
clean-all: clean clean-data
	@echo "🧹 Deep cleaning..."
	@rm -rf .venv/
	@rm -f .env
	@echo "✅ Deep cleanup complete"
	@echo "Run 'make setup' to reinstall"

# Run tests (if available)
test:
	@echo "🧪 Running tests..."
	@if [ -d "tests/" ]; then \
		$(PYTHON) -m pytest tests/ -v; \
	else \
		echo "⚠️  No tests directory found"; \
	fi

# Test CLI functionality
test-cli:
	@echo "🧪 Testing CLI functionality..."
	@$(PYTHON) scripts/test_cli.py

test-ui:
	@echo "🧪 Testing UI approach..."
	@$(PYTHON) scripts/test_ui_approach.py

test-ui-optimized:
	@echo "🧪 Testing optimized UI configuration..."
	@$(PYTHON) scripts/test_optimized_config.py

test-complete-workflow:
	@echo "🧪 Testing complete workflow with local Ollama..."
	@$(PYTHON) scripts/test_complete_workflow.py

test-ui-functionality:
	@echo "🧪 Testing UI functionality..."
	@$(PYTHON) scripts/test_ui_functionality.py

test-file-upload:
	@echo "🧪 Testing file upload functionality..."
	@$(PYTHON) scripts/test_file_upload.py

# Run CLI with example
cli-example:
	@echo "🚀 Running CLI example..."
	@echo "Make sure you have PDF files in ./papers/ directory"
	@echo "Example: paper-qa-cli 'What is the main finding?'"
	@echo ""
	@if [ -d "papers/" ] && [ "$$(find papers/ -name '*.pdf' | wc -l)" -gt 0 ]; then \
		echo "Found PDF files, running example query..."; \
		$(PYTHON) scripts/paper_qa_cli.py "What is this paper about?"; \
	else \
		echo "No PDF files found in ./papers/ directory"; \
		echo "Please add some PDF files and try again"; \
	fi

# Show CLI demo
cli-demo:
	@echo "🎬 Running CLI demo..."
	@$(PYTHON) scripts/demo_cli.py

# Format code
format:
	@echo "🎨 Formatting code..."
	@if command -v black >/dev/null 2>&1; then \
		black src/ scripts/; \
		echo "✅ Black formatting complete"; \
	else \
		echo "⚠️  Black not installed. Run: uv add --dev black"; \
	fi
	@if command -v isort >/dev/null 2>&1; then \
		isort src/ scripts/; \
		echo "✅ Import sorting complete"; \
	else \
		echo "⚠️  isort not installed. Run: uv add --dev isort"; \
	fi

# Lint code
lint:
	@echo "🔍 Linting code..."
	@if command -v ruff >/dev/null 2>&1; then \
		ruff check src/ scripts/; \
		echo "✅ Ruff linting complete"; \
	else \
		echo "⚠️  Ruff not installed. Run: uv add --dev ruff"; \
	fi

# Install development dependencies
install-dev:
	@echo "📦 Installing development dependencies..."
	@$(UV) add --dev black isort ruff pytest pytest-asyncio
	@echo "✅ Development dependencies installed"

# Download demo papers
demo-data:
	@echo "📚 Downloading demo papers..."
	@$(PYTHON) scripts/download_demo_papers.py
	@echo "✅ Demo data downloaded"

# System status check
status:
	@echo "📊 System Status Check"
	@echo "======================"
	@make check-env
	@echo ""
	@echo "📁 Data directories:"
	@if [ -d "papers/" ]; then \
		echo "  Papers: $$(find papers/ -name "*.pdf" | wc -l) PDFs"; \
	else \
		echo "  Papers: No papers directory"; \
	fi
	@if [ -d "indexes/" ]; then \
		echo "  Indexes: $$(find indexes/ -type d -name "session_*" | wc -l) sessions"; \
	else \
		echo "  Indexes: No indexes directory"; \
	fi

# Show current configuration
config:
	@echo "⚙️  Current Configuration"
	@echo "========================"
	@echo "Python: $$($(PYTHON) --version)"
	@echo "UV: $$($(UV) --version 2>/dev/null || echo 'Not found')"
	@echo "Working directory: $$(pwd)"
	@if [ -f "configs/default.json" ]; then \
		echo "Default config: configs/default.json"; \
		echo "LLM: $$(grep '"llm"' configs/default.json | cut -d'"' -f4)"; \
		echo "Embedding: $$(grep '"embedding"' configs/default.json | cut -d'"' -f4)"; \
	fi