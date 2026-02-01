# Testing Guide

## Overview

This project uses **pytest** for comprehensive testing of all modules. Given the financial nature of this application, we prioritize **accuracy**, **reliability**, and **data integrity** in our test suite.

## Test Categories

| Marker | Description | Run Time |
|--------|-------------|----------|
| `@pytest.mark.unit` | Fast, isolated tests with mocks | < 100ms |
| `@pytest.mark.integration` | Tests hitting real external APIs | 1-30s |
| `@pytest.mark.slow` | Long-running tests | > 30s |
| `@pytest.mark.critical` | **Financial accuracy tests** - must never fail | Varies |

## Running Tests

### Quick Start

```bash
# Install test dependencies
uv sync --group dev

# Run all unit tests (fast, recommended for development)
uv run pytest -m unit -v

# Run all tests (including integration)
uv run pytest tests/ -v
```

### Specific Test Commands

```bash
# Run tests for a specific module
uv run pytest tests/test_market_data.py -v
uv run pytest tests/test_analysis.py -v
uv run pytest tests/test_news_scraper.py -v

# Run only critical financial accuracy tests
uv run pytest -m critical -v

# Run with coverage report
uv run pytest --cov=. --cov-report=html tests/

# Skip slow integration tests
uv run pytest -m "not slow" -v

# Run tests in parallel (if pytest-xdist installed)
uv run pytest -n auto tests/
```

## Test Structure

```
tests/
├── conftest.py           # Shared fixtures and mocks
├── test_config.py        # Configuration validation
├── test_market_data.py   # Stock price, info, historical data
├── test_analysis.py      # Technical indicators (RSI, MACD, BB)
├── test_news_scraper.py  # News scraping and aggregation
├── test_institutional.py # FII/DII, promoter holdings
├── test_fundamental.py   # Fundamental ratios (PE, ROE)
├── test_agents.py        # CrewAI agent configuration
├── test_crews.py         # Research crew workflows
└── test_integration.py   # End-to-end pipelines
```

## Testing Strategy

### 1. Unit Tests (Mocked)
- Isolated from external dependencies
- Use fixtures from `conftest.py` for reproducible test data
- Fast execution for rapid development feedback

### 2. Integration Tests
- Hit real APIs (Yahoo Finance, NSE, news sites)
- Marked with `@pytest.mark.slow` for selective running
- Verify actual data structure and response handling

### 3. Critical Financial Tests
- Marked with `@pytest.mark.critical`
- **Must pass before any release**
- Validate:
  - RSI bounds (0-100)
  - Bollinger Band ordering (upper ≥ middle ≥ lower)
  - OHLC consistency (high ≥ close, low ≤ open)
  - Positive price values
  - No data contamination between stocks

## Key Fixtures

| Fixture | Description |
|---------|-------------|
| `sample_stock_symbols` | List of valid NIFTY50 symbols |
| `valid_symbol` | Single valid symbol (RELIANCE) |
| `invalid_symbol` | Invalid symbol for error testing |
| `mock_yfinance` | Mocked yfinance for unit tests |
| `mock_httpx_client` | Mocked HTTP client for news tests |
| `sample_historical_data` | Realistic OHLCV DataFrame |

## Coverage Goals

- **Target: 100%** for core financial modules
- `tools/` - Must have complete coverage
- `agents/` - Configuration and creation tested
- `crews/` - Workflow definitions tested

## CI/CD Integration

```yaml
# Example GitHub Actions workflow
- name: Run Unit Tests
  run: uv run pytest -m unit -v --tb=short

- name: Run Critical Tests
  run: uv run pytest -m critical -v --tb=short

- name: Run Full Suite (nightly)
  run: uv run pytest tests/ -v --cov=. --cov-fail-under=80
```

## Debugging Failed Tests

```bash
# Run with detailed output
uv run pytest -v --tb=long

# Run single test with debug
uv run pytest tests/test_analysis.py::TestRSI::test_rsi_valid_range -v -s

# Show local variables on failure
uv run pytest --tb=locals
```

## Adding New Tests

1. Create test in appropriate `test_*.py` file
2. Add relevant markers (`@pytest.mark.unit`, etc.)
3. Use fixtures from `conftest.py`
4. For financial calculations, add `@pytest.mark.critical`
5. Mock external dependencies for unit tests

---

*Last updated: June 2025*
