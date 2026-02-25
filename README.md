# Watchtowerpy

A Flask-based web application for monitoring website changes and detecting visual/text differences. Uses Playwright, Selenium, and Pyppeteer for browser automation, with Celery for background task processing.

## Features

- Website monitoring and change detection
- Visual and text diff comparison
- AI-powered diff analysis (Anthropic, Cerebras)
- Background task processing with Celery
- SQLite database for persistence

## Quick Start

### Local Development

```bash
# Install dependencies
make install

# Start the application
make start

# Run Celery worker (separate terminal)
make celery

# Run tests
make test

# Run linters
make lint

# Run type checker
make typecheck
```

### Docker

```bash
# Build and start
docker-compose build
docker-compose up
```

The app will be available at `http://localhost:8000`

## Environment Variables

Create a `.env` file based on `.env.example`:

```
DATABASE_PATH=./checkdiff.db
CELERY_BROKER_URL=sqla+sqlite:///./db/celery_broker.db
CELERY_RESULT_BACKEND=db+sqlite:///./db/celery_results.db
ANTHROPIC_API_KEY=your_key
CEREBRAS_API_KEY=your_key
```

## Available Make Commands

| Command | Description |
|---------|-------------|
| `make install` | Install dependencies |
| `make start` | Start Flask application |
| `make stop` | Stop running application |
| `make test` | Run tests |
| `make lint` | Run linters |
| `make typecheck` | Run type checker |
| `make clean` | Clean up cache files |
| `make celery` | Start Celery worker |

## Project Structure

```
.
├── app/
│   ├── models/          # Database models
│   ├── repositories/   # Data access layer
│   ├── routes/         # API endpoints
│   ├── services/       # Business logic
│   ├── tasks/          # Celery tasks
│   └── utils/          # Utilities
├── templates/          # Jinja2 templates
├── static/             # Static assets
├── tests/              # Test suite
├── Dockerfile
├── docker-compose.yml
├── Makefile
└── pyproject.toml
```
