# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BananaVoice is a FastAPI-based web application that provides both REST and GraphQL APIs. It includes user authentication, database integration, background task processing, and comprehensive monitoring capabilities.

## Development Commands

### Environment Setup
```bash
# Install dependencies
poetry install

# Install pre-commit hooks
pre-commit install

# Start development server
poetry run python -m bananavoice
```

### Code Quality
```bash
# Format code with Black
poetry run black bananavoice tests

# Lint with Ruff
poetry run ruff check bananavoice tests --fix

# Type checking with MyPy
poetry run mypy bananavoice

# Run all pre-commit checks
pre-commit run --all-files
```

### Testing
```bash
# Run all tests
pytest -vv .

# Run tests with coverage
pytest --cov=bananavoice --cov-report=html

# Run tests in Docker
docker-compose run --build --rm api pytest -vv .
```

### Database Operations
```bash
# Run all pending migrations
alembic upgrade head

# Generate new migration
alembic revision --autogenerate

# Revert to specific migration
alembic downgrade <revision_id>

# Revert all migrations
alembic downgrade base
```

### Docker Development
```bash
# Start all services
docker-compose up --build

# Development mode with autoreload
docker-compose -f docker-compose.yml -f deploy/docker-compose.dev.yml --project-directory . up --build

# With OpenTelemetry monitoring
docker-compose -f docker-compose.yml -f deploy/docker-compose.otlp.yml --project-directory . up
```

## Architecture Overview

### Core Structure
- **bananavoice/**: Main application package
  - **db/**: Database layer with models, DAOs, and migrations
  - **web/**: Web layer with REST API and GraphQL endpoints
  - **services/**: External service integrations (Redis, RabbitMQ)
  - **settings.py**: Configuration management

### API Architecture
- **REST API**: Available at `/api/*` with endpoints for docs, monitoring, and users
- **GraphQL**: Available at `/graphql` with GraphiQL interface
- **Documentation**: Swagger UI at `/api/docs`

### Authentication System
- Uses **fastapi-users** for complete user management
- Supports both JWT and cookie-based authentication
- UUID-based user identification

### Background Processing
- **TaskIQ** with Redis backend for async task processing
- **RabbitMQ** for message queuing
- Dedicated worker containers for background jobs

### Database Layer
- **SQLAlchemy 2.0** with async support
- **MySQL 8.4** as primary database
- **Alembic** for migration management
- Repository pattern via Data Access Objects (DAOs)

## Configuration

Environment variables use the `BANANAVOICE_` prefix. Create a `.env` file for local development:

```bash
BANANAVOICE_RELOAD="True"
BANANAVOICE_PORT="8000"
BANANAVOICE_ENVIRONMENT="dev"
```

## Key Development Notes

- All code changes must pass pre-commit hooks (Black, Ruff, MyPy)
- Database schema changes require Alembic migrations
- Background tasks use TaskIQ with Redis backend
- Tests run with pytest environment configuration
- Docker development exposes port 8000 with autoreload
- Monitoring available via Prometheus and OpenTelemetry

## Deployment

### Kubernetes
```bash
kubectl apply -f deploy/kube
```

### Docker Production
```bash
docker-compose up --build
```

## Testing Database Setup

For local testing, start a MySQL container:
```bash
docker run -p "3306:3306" -e "MYSQL_PASSWORD=bananavoice" -e "MYSQL_USER=bananavoice" -e "MYSQL_DATABASE=bananavoice" -e ALLOW_EMPTY_PASSWORD=yes mysql:8.4
```