.PHONY: help install start stop test lint typecheck clean celery

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make start      - Start the Flask application"
	@echo "  make stop       - Stop the running Flask application"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run linters"
	@echo "  make typecheck  - Run type checker"
	@echo "  make clean      - Clean up cache files"
	@echo "  make celery     - Start Celery worker"

install:
	uv sync

start:
	@echo "Starting Flask application..."
	@.venv/bin/gunicorn --bind 0.0.0.0:$$(grep PORT .env 2>/dev/null | cut -d= -f2 || echo "5000") --log-level debug --access-logfile - --error-logfile - --enable-stdio-inheritance wsgi:app

celery:
	@echo "Starting Celery worker..."
	@.venv/bin/celery -A app.celery_config worker --loglevel=info --concurrency=2

stop:
	@echo "Stopping Flask application..."
	@pid=$$(lsof -ti:$$(grep PORT .env 2>/dev/null | cut -d= -f2) 2>/dev/null); \
		if [ -n "$$pid" ]; then \
			kill $$pid; \
			echo "Stopped process $$pid"; \
		else \
			echo "No process found on port"; \
		fi

test:
	@echo "Running tests..."
	@.venv/bin/python -m pytest tests/ -v

lint:
	@echo "Running linters..."
	@.venv/bin/python -m ruff check .

typecheck:
	@echo "Running type checker..."
	@.venv/bin/python -m mypy app/

clean:
	@echo "Cleaning up..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Clean complete"
