# Makefile for PaperQA Discovery

.PHONY: run stop backend frontend

# This will run both servers concurrently in the same terminal.
# Output from both will be interleaved.
# For a cleaner output, run `make backend` and `make frontend` in separate terminals.
# Press Ctrl+C to stop both servers.
run:
	@echo "Starting backend and frontend servers..."
	@trap 'kill 0' SIGINT; \
	uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000 & \
	npm start --prefix frontend & \
	wait

# Target to stop all running servers
stop:
	@echo "Stopping servers..."
	@# Find and kill the process using port 8000 (backend)
	@lsof -t -i:8000 | xargs kill -9 > /dev/null 2>&1 || true
	@# Find and kill the process using port 3000 (frontend)
	@lsof -t -i:3000 | xargs kill -9 > /dev/null 2>&1 || true
	@echo "Servers stopped."

# Optional: Run servers individually
backend:
	@echo "Starting backend API server on http://localhost:8000"
	@uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	@echo "Starting frontend development server on http://localhost:3000"
	@npm start --prefix frontend
