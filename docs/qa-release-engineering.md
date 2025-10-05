# QA/Release Engineering for NicheRadar v1.5

## Overview

This document describes the comprehensive testing strategy and release engineering practices for NicheRadar v1.5. The testing framework includes unit tests, integration tests, E2E UI tests, and comprehensive reporting.

## Testing Architecture

### Test Types

1. **Unit Tests** (`tests/test_niche_units.py`)
   - Test individual components in isolation
   - Deterministic tests with mocked dependencies
   - Fast execution (< 1 second per test)

2. **Integration Tests** (`tests/test_niche_integration.py`)
   - Test component interactions
   - Web access pipeline testing
   - Cache, allowlist, and security testing

3. **E2E UI Tests** (`e2e/test_niche_ui.spec.ts`)
   - Full user workflow testing
   - Playwright-based browser automation
   - Cross-browser compatibility testing

### Test Configuration

#### Staging Profile (`config/staging.yaml`)
```yaml
# Web Access Settings
web_search:
  enabled: true
  timeout: 5
  retry_count: 2

# Cache Settings
cache:
  enabled: true
  default_ttl: 300
  max_size: 1000

# Tool Gate Settings
tool_gate:
  enabled: true
  log_decisions: true
```

#### Pytest Configuration (`pytest.ini`)
- HTML report generation
- Coverage reporting (minimum 65%)
- Test discovery and markers
- Parallel execution support

## Test Execution

### Prerequisites

1. **Python Dependencies**
   ```bash
   pip install -r requirements-test.txt
   ```

2. **Playwright Setup**
   ```bash
   npx playwright install
   ```

3. **Backend Running**
   ```bash
   python app.py
   ```

4. **Frontend Running**
   ```bash
   npm run dev
   ```

### Running Tests

#### Quick Tests (Unit + Integration)
```bash
python scripts/run_tests.py --quick
```

#### All Tests with Reports
```bash
python scripts/run_tests.py --all
```

#### Individual Test Suites
```bash
# Unit tests only
python scripts/run_tests.py --unit

# Integration tests only
python scripts/run_tests.py --integration

# E2E tests only
python scripts/run_tests.py --e2e
```

#### Manual Test Execution
```bash
# Unit & Integration
pytest -q tests/test_niche_units.py
pytest -q tests/test_niche_integration.py

# Full suite with reports
pytest -q --maxfail=1 --disable-warnings --cov=stillme --cov=niche_radar --cov=policy --cov=security --cov=cache --cov=metrics --cov-report=html:reports/coverage --cov-report=term-missing --cov-report=xml:reports/coverage.xml --html=reports/test_report.html --self-contained-html --junitxml=reports/junit.xml

# E2E UI tests
npx playwright test e2e/test_niche_ui.spec.ts --headed
```

## Test Coverage

### Coverage Requirements

- **Minimum Coverage**: 65% for `niche_radar/*` modules
- **Critical Modules**: 80%+ coverage for scoring, collectors, playbook
- **Security Modules**: 90%+ coverage for content wrap, tool gate

### Coverage Reports

- **HTML Report**: `reports/coverage/index.html`
- **XML Report**: `reports/coverage.xml`
- **Terminal Output**: Missing lines displayed during test run

## Test Data and Fixtures

### Fixtures Directory (`tests/fixtures/`)

- `github_trending_sample.json` - GitHub trending data
- `hackernews_sample.json` - HackerNews data
- `news_sample.json` - News API data
- `google_trends_sample.json` - Google Trends data
- `reddit_sample.json` - Reddit engagement data

### VCR Cassettes (`tests/cassettes/`)

- HTTP interactions recorded for deterministic testing
- Automatic recording on first run
- Replay mode for subsequent runs
- Sensitive data filtered (API keys, tokens)

## Security Testing

### Content Security

1. **Prompt Injection Detection**
   - Test malicious instruction patterns
   - Verify content wrapping
   - Check injection tagging

2. **XSS Protection**
   - Test HTML/JS injection
   - Verify content sanitization
   - Check Markdown image security

3. **URL Security**
   - Test homoglyph domains
   - Verify redirect limits
   - Check allowlist enforcement

### Tool Gate Testing

1. **Parameter Validation**
   - Test strange parameters
   - Verify sanitization
   - Check cost estimation

2. **Tool Name Validation**
   - Test malicious tool names
   - Verify allowlist enforcement
   - Check decision logging

## Performance Testing

### Metrics Tracking

- **Request Latency**: P50, P95 percentiles
- **Cache Hit Ratio**: Target > 70%
- **Success Rate**: Target > 95%
- **Memory Usage**: Monitor for leaks

### Load Testing

- **Concurrent Requests**: Test with 10+ simultaneous requests
- **Cache Performance**: Test cache eviction and TTL
- **Database Performance**: Test with large datasets

## E2E Testing

### Browser Coverage

- **Desktop**: Chrome, Firefox, Safari, Edge
- **Mobile**: Chrome Mobile, Safari Mobile
- **Viewport**: Responsive design testing

### User Workflows

1. **Niche Discovery**
   - Navigate to Niche Radar tab
   - View Top 10 table
   - Check score/confidence display

2. **Playbook Generation**
   - Click Generate Playbook
   - Verify file creation
   - Check toast notifications

3. **Source Attribution**
   - Open Sources modal
   - Verify source information
   - Check URL accessibility

4. **Experiment Management**
   - Start experiment
   - Verify checklist creation
   - Check progress tracking

## Reporting and Artifacts

### Test Reports

1. **HTML Report** (`reports/test_report.html`)
   - Test results with pass/fail status
   - Error details and stack traces
   - Test execution timeline

2. **Coverage Report** (`reports/coverage/index.html`)
   - Line-by-line coverage analysis
   - Missing coverage highlights
   - Coverage trends over time

3. **JUnit XML** (`reports/junit.xml`)
   - CI/CD integration format
   - Test result metadata
   - Failure details

### Playwright Reports

1. **HTML Report** (`reports/playwright-report/index.html`)
   - Screenshots and videos
   - Test execution timeline
   - Browser-specific results

2. **JSON Results** (`reports/playwright-results.json`)
   - Machine-readable test results
   - Performance metrics
   - Error details

### Log Files

1. **Web Metrics** (`logs/web_metrics.log`)
   - Request/response metrics
   - Cache performance
   - Error rates

2. **Tool Gate** (`logs/tool_gate.log`)
   - Tool validation decisions
   - Allow/deny reasons
   - Parameter sanitization

3. **Test Summary** (`reports/test_summary.json`)
   - Test execution summary
   - Report generation status
   - Coverage metrics

## CI/CD Integration

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run hooks
pre-commit run --all-files
```

### GitHub Actions

```yaml
name: NicheRadar Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements-test.txt
          npx playwright install
      - name: Run tests
        run: python scripts/run_tests.py --all
      - name: Upload reports
        uses: actions/upload-artifact@v3
        with:
          name: test-reports
          path: reports/
```

## Troubleshooting

### Common Issues

1. **Backend Not Running**
   - Check `python app.py` is running
   - Verify port 5000 is accessible
   - Check health endpoint: `http://localhost:5000/health`

2. **Frontend Not Running**
   - Check `npm run dev` is running
   - Verify port 3000 is accessible
   - Check staging profile: `http://localhost:3000?profile=staging`

3. **Test Failures**
   - Check test logs in `logs/` directory
   - Verify test data in `tests/fixtures/`
   - Check VCR cassettes in `tests/cassettes/`

4. **Coverage Issues**
   - Ensure all modules are imported in tests
   - Check coverage configuration in `pytest.ini`
   - Verify source paths are correct

### Debug Mode

```bash
# Run tests with debug output
pytest -v -s tests/test_niche_units.py

# Run specific test with debug
pytest -v -s tests/test_niche_units.py::TestCollectors::test_github_trending_schema

# Run with coverage debug
pytest --cov=niche_radar --cov-report=term-missing --cov-report=html tests/
```

## Best Practices

### Test Writing

1. **Test Isolation**
   - Each test should be independent
   - Use fixtures for common setup
   - Clean up after each test

2. **Descriptive Names**
   - Test names should describe the scenario
   - Use clear assertions
   - Document expected behavior

3. **Mock External Dependencies**
   - Use VCR for HTTP requests
   - Mock file system operations
   - Isolate database operations

### Test Maintenance

1. **Regular Updates**
   - Update fixtures when APIs change
   - Refresh VCR cassettes periodically
   - Update test data for new features

2. **Performance Monitoring**
   - Track test execution time
   - Monitor memory usage
   - Optimize slow tests

3. **Coverage Monitoring**
   - Track coverage trends
   - Identify uncovered code
   - Set coverage goals

## Conclusion

This comprehensive testing framework ensures NicheRadar v1.5 meets quality standards and provides reliable functionality. The multi-layered approach covers unit testing, integration testing, E2E testing, and security validation, providing confidence in the system's reliability and performance.

For questions or issues, refer to the troubleshooting section or check the test logs for detailed error information.
