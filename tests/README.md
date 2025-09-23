# NicheRadar v1.5 Testing Guide

## Quick Start

### Prerequisites
```bash
# Install Python dependencies
pip install -r requirements-test.txt

# Install Playwright browsers
npx playwright install

# Start backend
python app.py

# Start frontend (in another terminal)
npm run dev
```

### Run Tests
```bash
# Quick tests (unit + integration)
python scripts/run_tests.py --quick

# All tests with reports
python scripts/run_tests.py --all

# Individual test suites
python scripts/run_tests.py --unit
python scripts/run_tests.py --integration
python scripts/run_tests.py --e2e
```

## Test Structure

```
tests/
├── conftest.py              # Pytest configuration and fixtures
├── test_niche_units.py      # Unit tests
├── test_niche_integration.py # Integration tests
├── fixtures/                # Test data fixtures
│   ├── github_trending_sample.json
│   ├── hackernews_sample.json
│   ├── news_sample.json
│   ├── google_trends_sample.json
│   └── reddit_sample.json
└── cassettes/               # VCR HTTP recordings
    └── (auto-generated)

e2e/
├── test_niche_ui.spec.ts    # E2E UI tests
├── global-setup.ts          # Global test setup
└── global-teardown.ts       # Global test cleanup
```

## Test Types

### Unit Tests (`test_niche_units.py`)
- **Collectors**: Test data collection from various sources
- **Scoring**: Test NicheScore calculation and normalization
- **Feasibility**: Test StillMe capability alignment
- **Content Security**: Test injection detection and content wrapping

### Integration Tests (`test_niche_integration.py`)
- **Pipeline**: Test collect→score→top10 workflow
- **Cache**: Test caching behavior and TTL
- **Security**: Test allowlist, redirects, homoglyph protection
- **Tool Gate**: Test tool validation and decision logging
- **Playbook**: Test playbook generation and file creation

### E2E Tests (`test_niche_ui.spec.ts`)
- **UI Navigation**: Test Niche Radar tab and table display
- **User Actions**: Test Generate Playbook and Start Experiment
- **Attribution**: Test source modal and information display
- **Responsive**: Test mobile and desktop layouts

## Test Data

### Fixtures
Test data is stored in `tests/fixtures/` as JSON files:
- **GitHub Trending**: Repository data with stars, forks, language
- **HackerNews**: Story data with scores, comments, heat
- **News**: Article data with relevance, sentiment, engagement
- **Google Trends**: Search data with volume, growth, related queries
- **Reddit**: Post data with upvotes, comments, engagement

### VCR Cassettes
HTTP interactions are recorded in `tests/cassettes/`:
- **First Run**: Records real HTTP requests
- **Subsequent Runs**: Replays recorded responses
- **Deterministic**: Ensures consistent test results
- **Filtered**: Removes sensitive data (API keys, tokens)

## Configuration

### Staging Profile (`config/staging.yaml`)
```yaml
web_search:
  enabled: true
  timeout: 5
  retry_count: 2

cache:
  enabled: true
  default_ttl: 300
  max_size: 1000

tool_gate:
  enabled: true
  log_decisions: true
```

### Pytest Configuration (`pytest.ini`)
- HTML report generation
- Coverage reporting (minimum 65%)
- Test discovery and markers
- Parallel execution support

### Playwright Configuration (`playwright.config.ts`)
- Cross-browser testing
- Mobile viewport testing
- Screenshot and video recording
- Global setup/teardown

## Reports and Artifacts

### Test Reports
- **HTML Report**: `reports/test_report.html`
- **Coverage Report**: `reports/coverage/index.html`
- **JUnit XML**: `reports/junit.xml`
- **Playwright Report**: `reports/playwright-report/index.html`

### Log Files
- **Web Metrics**: `logs/web_metrics.log`
- **Tool Gate**: `logs/tool_gate.log`
- **Test Summary**: `reports/test_summary.json`

## Security Testing

### Content Security
- **Prompt Injection**: Test malicious instruction patterns
- **XSS Protection**: Test HTML/JS injection
- **Content Wrapping**: Verify LLM content isolation

### Network Security
- **Allowlist**: Test domain restrictions
- **Redirects**: Test redirect limit enforcement
- **Homoglyph**: Test deceptive domain detection
- **HTTPS**: Test secure connection requirements

### Tool Validation
- **Parameter Sanitization**: Test input validation
- **Tool Names**: Test malicious tool detection
- **Cost Estimation**: Test resource limit enforcement

## Performance Testing

### Metrics
- **Latency**: P50, P95 percentiles
- **Cache Hit Ratio**: Target > 70%
- **Success Rate**: Target > 95%
- **Memory Usage**: Monitor for leaks

### Load Testing
- **Concurrent Requests**: Test with 10+ simultaneous requests
- **Cache Performance**: Test cache eviction and TTL
- **Database Performance**: Test with large datasets

## Troubleshooting

### Common Issues

1. **Backend Not Running**
   ```bash
   # Check if backend is running
   curl http://localhost:5000/health
   
   # Start backend if not running
   python app.py
   ```

2. **Frontend Not Running**
   ```bash
   # Check if frontend is running
   curl http://localhost:3000
   
   # Start frontend if not running
   npm run dev
   ```

3. **Test Failures**
   ```bash
   # Check test logs
   tail -f logs/test.log
   
   # Run specific test with debug
   pytest -v -s tests/test_niche_units.py::TestCollectors::test_github_trending_schema
   ```

4. **Coverage Issues**
   ```bash
   # Check coverage report
   open reports/coverage/index.html
   
   # Run with coverage debug
   pytest --cov=niche_radar --cov-report=term-missing tests/
   ```

### Debug Mode
```bash
# Run tests with debug output
pytest -v -s tests/test_niche_units.py

# Run with coverage debug
pytest --cov=niche_radar --cov-report=term-missing --cov-report=html tests/

# Run E2E tests in headed mode
npx playwright test e2e/test_niche_ui.spec.ts --headed
```

## Best Practices

### Test Writing
1. **Test Isolation**: Each test should be independent
2. **Descriptive Names**: Test names should describe the scenario
3. **Mock Dependencies**: Use fixtures and VCR for external dependencies
4. **Clear Assertions**: Use specific assertions with helpful error messages

### Test Maintenance
1. **Regular Updates**: Update fixtures when APIs change
2. **Performance Monitoring**: Track test execution time
3. **Coverage Monitoring**: Track coverage trends and identify gaps
4. **Security Testing**: Regularly test security features

### Test Data
1. **Realistic Data**: Use realistic test data that reflects production
2. **Sensitive Data**: Never include real API keys or tokens
3. **Data Freshness**: Update test data periodically
4. **Data Validation**: Verify test data structure and content

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

## Conclusion

This testing framework provides comprehensive coverage for NicheRadar v1.5, ensuring reliability, security, and performance. The multi-layered approach covers unit testing, integration testing, E2E testing, and security validation.

For questions or issues, refer to the troubleshooting section or check the test logs for detailed error information.
