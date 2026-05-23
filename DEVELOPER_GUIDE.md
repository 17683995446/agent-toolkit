# Agent Toolkit Developer Guide

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- Git

### Local Development Setup

1. **Clone the repository**
```bash
git clone https://github.com/your-org/agent-toolkit.git
cd agent-toolkit
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# OR
.\venv\Scripts\activate  # Windows
```

3. **Install dependencies**
```bash
pip install -e .
pip install -r dev-requirements.txt
```

4. **Set up git hooks**
```bash
./scripts/setup-hooks.sh
```

5. **Run tests**
```bash
pytest
```

## 📁 Project Structure

### Core Modules

Each core module follows the same structure:
- `adapter/` - Tool execution adapters (HTTP, CLI, SDK)
- `orchestrator/` - Tool chain orchestration
- `registry/` - Tool registry and discovery
- `runtime/` - Execution environments (Docker, K8s)
- `observability/` - Metrics, logs, tracing
- `shared/` - Common utilities and types

## 🏗️ Architecture Overview

### Layered Architecture

```
┌─────────────────────────────────────────────┐
│        API Layer (FastAPI)                   │
│  - REST endpoints                           │
│  - Authentication                           │
│  - Rate limiting                            │
└─────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────┐
│     Service Layer                            │
│  - Business logic                           │
│  - Data validation                          │
│  - Orchestration                            │
└─────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────┐
│     Repository Layer                         │
│  - Database access                          │
│  - Cache layer                              │
└─────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────┐
│     Infrastructure Layer                     │
│  - Database (PostgreSQL/Redis)              │
│  - Message queues (Redis/Kafka)             │
└─────────────────────────────────────────────┘
```

## 💻 Development Workflow

### 1. Feature Development

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Implement the feature following architecture standards
3. Write tests
4. Run tests locally
5. Create pull request

### 2. Code Reviews

All pull requests must:
- Pass CI checks
- Have at least one approval
- Include documentation updates
- Have sufficient test coverage

### 3. Releases

Follow semantic versioning: `MAJOR.MINOR.PATCH`

## 🧪 Testing

### Running Tests

```bash
# Unit tests (fast)
pytest agent_toolkit/tests/unit/

# Integration tests
pytest agent_toolkit/tests/integration/

# All tests
pytest

# With coverage
pytest --cov=agent_toolkit --cov-report=html
```

### Writing Tests

See [ARCHITECTURE_STANDARDS.md](ARCHITECTURE_STANDARDS.md) for testing standards.

## 🐳 Docker Development

```bash
# Build and run all services
docker-compose up -d

# Check logs
docker-compose logs -f

# Run tests in container
docker-compose exec web pytest
```

## 🔧 Debugging

### Logging

```python
from agent_toolkit.shared.structured_logging import get_logger

logger = get_logger(__name__)
logger.debug("Debug info", extra={"user": user_id})
logger.info("Operation completed", extra={"tool_id": tool_id})
logger.warning("Potential issue", extra={"detail": warning_msg})
logger.error("Error occurred", exc_info=True)
```

### Debug Mode

```bash
# Run with debug logging
LOG_LEVEL=DEBUG python -m agent_toolkit.main
```

## 📊 Architecture Decisions (ADR)

### ADR-001: Layered Architecture
- **Date**: 2026-05-23
- **Status**: Accepted
- **Context**: Need for clean separation of concerns
- **Decision**: Adopt 4-layer architecture

### ADR-002: Pydantic for Validation
- **Date**: 2026-05-23
- **Status**: Accepted
- **Context**: Need for data validation and serialization
- **Decision**: Use Pydantic

## 📚 Additional Resources

- [API Documentation](API_DOCUMENTATION.md)
- [Architecture Standards](ARCHITECTURE_STANDARDS.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Deployment Guide](DEPLOYMENT.md)

## 💬 Community & Support

- GitHub Issues: Bug reports and feature requests
- Discussions: Q&A and community support
