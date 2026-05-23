# Agent Toolkit Architecture and Development Standards

## 🏗️ Core Architecture

Agent Toolkit follows a **modular, layered architecture** with clear separation of concerns:

```
agent_toolkit/
├── adapter/          # Adapter Layer - HTTP, CLI, SDK, Local Function
├── orchestrator/     # Orchestration Layer - Tool chain execution
├── registry/         # Registry Layer - Tool registration
├── runtime/          # Runtime Layer - Execution environments
├── observability/    # Observability Layer - Metrics, Logs, Tracing
└── shared/           # Shared - Common utilities and types
```

## 📦 Module Structure Standards

### 1. Each Module MUST Follow:

```
module_name/
├── __init__.py
├── module_name_api_routes.py
├── module_name_cli_commands.py
├── module_name_service.py
├── module_name_models.py
├── module_name_repository.py
├── pyproject.toml
└── tests/
    ├── __init__.py
    ├── test_service.py
    ├── test_models.py
    └── test_integration.py
```

### 2. File Naming Conventions:

| File Type | Pattern | Example |
|-----------|---------|---------|
| API Routes | `{module}_api_routes.py` | `registry_api_routes.py` |
| CLI Commands | `{module}_cli_commands.py` | `observability_cli_commands.py` |
| Service Logic | `{module}_service.py` | `orchestrator_service.py` |
| Data Models | `{module}_models.py` | `adapter_models.py` |
| Repository | `{module}_repository.py` | `runtime_repository.py` |
| Tests | `test_*.py` | `test_registry_service.py` |

## 🔧 Development Standards

### 1. Type Hints

**ALL** public functions MUST have full type annotations:

```python
from typing import Dict, List, Optional, Union
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str

def get_user(user_id: int) -> Optional[User]:
    """Get user by ID.

    Args:
        user_id: Unique identifier for the user.

    Returns:
        User object if found, None otherwise.
    """
    # Implementation
    pass
```

### 2. Error Handling

Use custom exceptions from `shared/custom_exceptions.py`:

```python
from agent_toolkit.shared.custom_exceptions import (
    NotFoundError,
    ValidationError,
    AgentToolkitTimeoutError
)

def process_tool(tool_id: int) -> None:
    if not tool_exists(tool_id):
        raise NotFoundError(
            message="Tool not found",
            resource_type="tool",
            resource_id=tool_id
        )
```

### 3. Logging

Use structured logging with levels:

```python
from agent_toolkit.shared.structured_logging import get_logger

logger = get_logger(__name__)

logger.info("Operation completed", extra={
    "operation": "tool_execution",
    "tool_id": tool_id,
    "duration_ms": duration_ms
})
```

### 4. Metrics

Use metrics collector for observability:

```python
from agent_toolkit.shared.metrics_api import MetricsCollector

metrics = MetricsCollector()

def execute_tool(tool_id: int) -> Result:
    metrics.increment_counter("tool_executions", labels={"tool_id": str(tool_id)})
    
    start_time = time.time()
    try:
        result = run_tool(tool_id)
        metrics.record_histogram("tool_execution_duration", (time.time() - start_time) * 1000)
        return result
    except Exception as e:
        metrics.increment_counter("tool_execution_errors", labels={"tool_id": str(tool_id)})
        raise
```

## 🧪 Testing Standards

### 1. Test Structure

```
tests/
├── unit/
│   ├── test_adapter_service.py
│   ├── test_registry_repository.py
│   └── ...
├── integration/
│   ├── test_api_endpoints.py
│   └── ...
├── e2e/
│   ├── test_end_to_end_flow.py
│   └── ...
├── stress/
│   ├── test_concurrent_execution.py
│   └── ...
├── chaos/
│   ├── test_failure_scenarios.py
│   └── ...
└── conftest.py
```

### 2. Test Naming

Pattern: `test_{method/function}_{condition}_{result}`

```python
def test_get_tool_existing_tool_returns_correct_data():
def test_get_tool_non_existing_raises_not_found_error():
def test_execute_tool_with_invalid_input_raises_validation_error():
```

### 3. Test Coverage Requirements

| Component | Minimum Coverage |
|-----------|-----------------|
| Core Services | 80% |
| API Routes | 70% |
| Shared Libraries | 90% |

## 🔌 API Design Standards

### 1. RESTful Endpoints

```
GET    /api/v1/{resource}        # List
POST   /api/v1/{resource}        # Create
GET    /api/v1/{resource}/{id}   # Get
PUT    /api/v1/{resource}/{id}   # Update
DELETE /api/v1/{resource}/{id}   # Delete
```

### 2. Response Format

```json
{
  "success": true,
  "data": {},
  "message": "Operation completed",
  "metadata": {
    "timestamp": "2026-05-23T10:00:00Z",
    "request_id": "uuid"
  }
}
```

### 3. Error Responses

```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Resource not found",
    "details": {}
  }
}
```

## 📊 Architecture Principles

### 1. Single Responsibility

Each class/function should have **one and only one reason to change**.

### 2. Open/Closed

Modules should be **open for extension, closed for modification**.

### 3. Dependency Inversion

Depend on abstractions, not concrete implementations.

### 4. Interface Segregation

Many client-specific interfaces are better than one general-purpose interface.

### 5. Liskov Substitution

Subtypes must be substitutable for their base types.

## 🔐 Security Standards

### 1. Input Validation

Use Pydantic models to validate ALL inputs:

```python
from pydantic import BaseModel, Field, field_validator

class ToolRegistration(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: str
    
    @field_validator('name')
    def name_must_not_contain_special_chars(cls, v):
        if any(c in v for c in '<>{}'):
            raise ValueError('Invalid characters in name')
        return v
```

### 2. Secret Management

Never hardcode secrets, use environment variables.

### 3. Rate Limiting

All public endpoints should implement rate limiting.

## 📝 Documentation Standards

### 1. Module Level

Every module must have a `__init__.py` with docstring:

```python
"""Adapter Module.

Provides interfaces for different tool execution environments.

Public API:
    - BaseAdapter: Abstract base class
    - HTTPAdapter: HTTP endpoint execution
    - CLIAdapter: Command-line execution
    - SDKAdapter: SDK-based execution
"""
```

### 2. Function/Method Level

All public functions must have docstrings:

```python
def execute_tool(tool_id: int, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a registered tool.

    Args:
        tool_id: Unique identifier for the tool
        inputs: Dictionary of input parameters

    Returns:
        Result of the tool execution

    Raises:
        NotFoundError: If tool doesn't exist
        ValidationError: If inputs are invalid
        AgentToolkitTimeoutError: If execution times out

    Examples:
        >>> result = execute_tool(123, {"query": "search"})
        >>> print(result)
        {"output": "search result"}
    """
```

## 🚀 Deployment Standards

### 1. Docker Best Practices

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY agent_toolkit ./agent_toolkit

# Expose port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run
CMD ["uvicorn", "agent_toolkit.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🔄 Release Process

1. **Bump version** in `pyproject.toml`
2. **Create release tag** following semantic versioning (vX.Y.Z)
3. **Run full test suite** (all tests must pass)
4. **Create GitHub Release** with changelog
5. **Build and publish** to package registry

---

## 📋 Compliance Checklist

Before merging a PR:
- [ ] Type hints complete
- [ ] Tests written and passing
- [ ] Documentation updated
- [ ] Code follows standards
- [ ] Security reviews complete
- [ ] CI checks passing
