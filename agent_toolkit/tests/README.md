# Tests Directory Structure
# This directory contains all tests for the Agent Toolkit project.

## Directory Structure

```
tests/
├── unit/              # Unit tests - individual components
│   ├── adapter/
│   ├── orchestrator/
│   ├── registry/
│   ├── runtime/
│   ├── observability/
│   └── shared/
├── integration/       # Integration tests - multiple components
├── e2e/              # End-to-end tests - full flows
├── stress/           # Stress/performance tests
├── chaos/            # Chaos engineering tests
├── boundary/         # Boundary and edge case tests
└── conftest.py       # Pytest fixtures and configuration
```

## Test Classification

### 1. Unit Tests (`unit/`)
- Tests individual functions and classes in isolation
- Fast execution (milliseconds)
- No external dependencies
- High coverage required

### 2. Integration Tests (`integration/`)
- Tests interactions between components
- May use test databases or mock external services
- Slower than unit tests

### 3. End-to-End Tests (`e2e/`)
- Tests complete user workflows
- Uses real infrastructure where possible
- Slowest, run less frequently

### 4. Stress Tests (`stress/`)
- Performance and scalability testing
- Concurrent operations
- Load testing
- Long-running stability

### 5. Chaos Tests (`chaos/`)
- Failure scenario testing
- Network interruptions
- Resource starvation
- Recovery mechanisms

### 6. Boundary Tests (`boundary/`)
- Edge case validation
- Input limits
- Type validation
- Exception handling

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test Type
```bash
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
pytest tests/stress/
pytest tests/chaos/
```

### Run Tests with Coverage
```bash
pytest --cov=agent_toolkit --cov-report=term --cov-report=html
```

### Run with Verbosity
```bash
pytest -v
pytest -v tests/unit/
```

## Test Best Practices

1. **Isolation**: Tests should not depend on each other
2. **Speed**: Fast tests, run often
3. **Readability**: Clear test names and assertions
4. **Maintainability**: Easy to update and extend
5. **Deterministic**: Same inputs → same output
