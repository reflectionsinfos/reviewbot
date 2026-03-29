# Test Strategy

> AI Tech & Delivery Review Agent - Testing Approach and Standards

**Version:** 1.0.0  
**Last Updated:** March 27, 2026  
**Status:** Approved  
**Owner:** QA Team

---

## 📋 Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Test Pyramid](#test-pyramid)
3. [Testing Levels](#testing-levels)
4. [Test Types](#test-types)
5. [Test Infrastructure](#test-infrastructure)
6. [Test Data Management](#test-data-management)
7. [Code Coverage](#code-coverage)
8. [CI/CD Integration](#cicd-integration)
9. [Test Standards](#test-standards)

---

## Testing Philosophy

### Core Principles

1. **Test Early, Test Often**
   - Write tests before/during development (TDD where appropriate)
   - Run tests on every commit
   - Fail fast, fix immediately

2. **Automate Everything**
   - Manual testing only for exploratory testing
   - Automated regression suite
   - CI/CD pipeline runs all tests

3. **Test Behavior, Not Implementation**
   - Test what the code does, not how it does it
   - Avoid testing private methods
   - Focus on public APIs

4. **Keep Tests Independent**
   - Each test should run in isolation
   - No dependencies between tests
   - Tests can run in any order

5. **Make Tests Maintainable**
   - Clear, descriptive names
   - Follow AAA pattern (Arrange-Act-Assert)
   - DRY in tests (but not at cost of clarity)

---

## Test Pyramid

```
                    ┌─────────┐
                   /           \
                  /  E2E Tests  \
                 /   (Few)       \
                ├─────────────────┤
               /                   \
              /  Integration Tests  \
             /    (Some)            \
            ├─────────────────────────┤
           /                           \
          /      Unit Tests             \
         /       (Many)                 \
        └─────────────────────────────────┘
```

### Distribution

| Test Type | Percentage | Execution Time | Purpose |
|-----------|------------|----------------|---------|
| **Unit Tests** | 70% | < 10ms each | Test individual functions/methods |
| **Integration Tests** | 20% | < 100ms each | Test component interactions |
| **E2E Tests** | 10% | < 5s each | Test complete user workflows |

---

## Testing Levels

### Level 1: Unit Tests

**Purpose:** Test individual functions, methods, and classes in isolation

**Scope:**
- Pure functions
- Service methods
- Utility functions
- Model validators

**Tools:**
- pytest (test runner)
- pytest-asyncio (async support)
- unittest.mock (mocking)

**Example:**

```python
import pytest
from app.services.report_generator import ReportGenerator

class TestReportGenerator:
    """Unit tests for ReportGenerator"""
    
    @pytest.fixture
    def generator(self):
        return ReportGenerator()
    
    def test_calculate_compliance_score_all_green(self, generator):
        """Test compliance score calculation with all green responses"""
        # Arrange
        responses = [
            {"rag_status": "green", "weight": 1.0},
            {"rag_status": "green", "weight": 1.0},
            {"rag_status": "green", "weight": 1.0}
        ]
        
        # Act
        score = generator.calculate_compliance_score(responses, [])
        
        # Assert
        assert score == 100.0
    
    def test_calculate_compliance_score_mixed(self, generator):
        """Test compliance score with mixed responses"""
        # Arrange
        responses = [
            {"rag_status": "green", "weight": 1.0},  # 100
            {"rag_status": "amber", "weight": 1.0},  # 50
            {"rag_status": "red", "weight": 1.0}     # 0
        ]
        
        # Act
        score = generator.calculate_compliance_score(responses, [])
        
        # Assert
        assert score == 50.0  # (100 + 50 + 0) / 3
    
    def test_calculate_compliance_score_excludes_na(self, generator):
        """Test that NA responses are excluded from score"""
        # Arrange
        responses = [
            {"rag_status": "green", "weight": 1.0},
            {"rag_status": "na", "weight": 1.0},  # Excluded
            {"rag_status": "green", "weight": 1.0}
        ]
        
        # Act
        score = generator.calculate_compliance_score(responses, [])
        
        # Assert
        assert score == 100.0
```

**Best Practices:**
- Test one thing per test
- Use descriptive names (test_method_scenario_expected)
- Mock external dependencies
- Keep tests fast (< 10ms each)
- Test edge cases and error conditions

---

### Level 2: Integration Tests

**Purpose:** Test interactions between components

**Scope:**
- API endpoints
- Database operations
- Service orchestration
- External integrations

**Tools:**
- pytest
- FastAPI TestClient
- Test containers (PostgreSQL)
- Mock servers (for external APIs)

**Example:**

```python
import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)

@pytest.fixture
def test_user(client):
    """Create test user for authentication"""
    response = client.post(
        "/api/auth/register",
        data={
            "email": "test@example.com",
            "password": "testpass123",
            "full_name": "Test User"
        }
    )
    return response.json()

def test_create_project_endpoint(client, test_user):
    """Integration test for project creation endpoint"""
    # Arrange
    login_response = client.post(
        "/api/auth/login",
        data={
            "username": "test@example.com",
            "password": "testpass123"
        }
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Act
    response = client.post(
        "/api/projects/",
        data={
            "name": "Test Project",
            "domain": "fintech",
            "description": "Test description"
        },
        headers=headers
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["domain"] == "fintech"
    assert "id" in data
```

**Best Practices:**
- Use test database (isolated from dev/prod)
- Clean up after tests
- Test happy path and error scenarios
- Verify database state changes
- Test authentication and authorization

---

### Level 3: E2E Tests

**Purpose:** Test complete user workflows

**Scope:**
- Full review workflow
- Approval process
- Report generation and download
- Voice interaction flow

**Tools:**
- pytest
- Playwright (for UI testing, if applicable)
- Test data fixtures

**Example:**

```python
import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def authenticated_client():
    """Create authenticated client for E2E tests"""
    client = TestClient(app)
    
    # Register and login
    client.post(
        "/api/auth/register",
        data={
            "email": "e2e@example.com",
            "password": "testpass123",
            "full_name": "E2E User"
        }
    )
    login_response = client.post(
        "/api/auth/login",
        data={
            "username": "e2e@example.com",
            "password": "testpass123"
        }
    )
    token = login_response.json()["access_token"]
    client.headers = {"Authorization": f"Bearer {token}"}
    
    return client

def test_complete_review_workflow(authenticated_client):
    """E2E test: Complete review from start to report"""
    client = authenticated_client
    
    # Step 1: Create project
    project_response = client.post(
        "/api/projects/",
        data={
            "name": "E2E Test Project",
            "domain": "fintech",
            "description": "E2E testing"
        }
    )
    project_id = project_response.json()["project_id"]
    
    # Step 2: Upload checklist (mock file)
    # ... upload checklist ...
    
    # Step 3: Create review
    review_response = client.post(
        "/api/reviews/",
        json={
            "project_id": project_id,
            "checklist_id": 1,
            "title": "E2E Review",
            "voice_enabled": False
        }
    )
    review_id = review_response.json()["id"]
    
    # Step 4: Start review
    start_response = client.post(f"/api/reviews/{review_id}/start")
    assert start_response.status_code == 200
    
    # Step 5: Submit responses
    for i in range(3):
        client.post(
            f"/api/reviews/{review_id}/respond",
            json={
                "question_index": i,
                "answer": "Yes, fully implemented",
                "comments": f"Response {i}"
            }
        )
    
    # Step 6: Complete review
    complete_response = client.post(f"/api/reviews/{review_id}/complete")
    assert complete_response.status_code == 200
    
    # Step 7: Verify report generated
    reports_response = client.get(f"/api/reports/?project_id={project_id}")
    reports = reports_response.json()
    assert len(reports) > 0
    assert reports[0]["approval_status"] == "pending"
    
    # Step 8: Approve report
    report_id = reports[0]["id"]
    approve_response = client.post(
        f"/api/reports/{report_id}/approve",
        json={
            "approver_id": 1,
            "comments": "Approved in E2E test"
        }
    )
    assert approve_response.status_code == 200
    
    # Step 9: Download report
    download_response = client.get(
        f"/api/reports/{report_id}/download/markdown"
    )
    assert download_response.status_code == 200
```

**Best Practices:**
- Test real user scenarios
- Include setup and teardown
- Keep E2E tests minimal (critical paths only)
- Make tests resilient to UI changes
- Run E2E tests in staging environment

---

## Test Types

### Functional Tests

**Purpose:** Verify functional requirements

**Examples:**
- User can create project
- Checklist is parsed correctly
- RAG status is assessed accurately
- Report is generated with correct data
- Approval workflow functions properly

---

### Non-Functional Tests

#### Performance Tests

**Purpose:** Verify performance requirements

**Tools:**
- pytest-benchmark
- locust (load testing)
- pytest-asyncio

**Examples:**

```python
import pytest
from pytest_benchmark.fixture import BenchmarkFixture

def test_parse_large_checklist(benchmark: BenchmarkFixture):
    """Benchmark: Parse large Excel file"""
    def parse():
        parser = ChecklistParser("tests/data/large_checklist.xlsx")
        return parser.parse_delivery_checklist()
    
    result = benchmark(parse)
    assert len(result) > 0
    assert benchmark.stats["mean"] < 1.0  # Should complete in < 1 second
```

**Performance Targets:**
- API response time (p95): < 500ms
- Report generation: < 30s
- Voice transcription: < 5s
- Database queries (p95): < 100ms

---

#### Security Tests

**Purpose:** Verify security controls

**Tools:**
- bandit (static analysis)
- safety (dependency vulnerabilities)
- OWASP ZAP (penetration testing)

**Examples:**

```python
def test_sql_injection_prevention():
    """Test: SQL injection is prevented"""
    # Attempt SQL injection
    malicious_input = "'; DROP TABLE users; --"
    
    # Should not raise exception or execute malicious SQL
    response = client.post(
        "/api/projects/",
        data={"name": malicious_input}
    )
    
    # Should be handled gracefully
    assert response.status_code in [200, 400, 422]
    
    # Verify table still exists
    assert db.execute("SELECT COUNT(*) FROM users").scalar() >= 0

def test_authentication_required():
    """Test: Endpoints require authentication"""
    # Try to access protected endpoint without token
    response = client.get("/api/projects/")
    assert response.status_code == 401
```

**Security Checklist:**
- [ ] Authentication required for all protected endpoints
- [ ] Authorization checks for resource access
- [ ] Input validation on all user inputs
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (HTML escaping)
- [ ] CSRF protection
- [ ] Rate limiting
- [ ] Secrets not hardcoded
- [ ] Passwords hashed
- [ ] HTTPS in production

---

#### Accessibility Tests (Future)

**Purpose:** Ensure accessibility compliance

**Tools:**
- axe-core
- pa11y
- WAVE

**Target:** WCAG 2.1 Level AA

---

### Regression Tests

**Purpose:** Ensure new changes don't break existing functionality

**Strategy:**
- Run full test suite on every PR
- Automated in CI/CD pipeline
- Tag regression tests with `@regression`

```python
@pytest.mark.regression
def test_existing_functionality():
    """Regression test for critical functionality"""
    ...
```

---

## Test Infrastructure

### Test Directory Structure

```
tests/
├── __init__.py
├── conftest.py                    # Shared fixtures
├── pytest.ini                     # Pytest configuration
│
├── unit/                          # Unit tests
│   ├── __init__.py
│   ├── test_checklist_parser.py
│   ├── test_report_generator.py
│   ├── test_voice_interface.py
│   └── test_agents/
│       ├── test_review_agent.py
│       └── test_states.py
│
├── integration/                   # Integration tests
│   ├── __init__.py
│   ├── test_api/
│   │   ├── test_auth.py
│   │   ├── test_projects.py
│   │   ├── test_reviews.py
│   │   └── test_reports.py
│   ├── test_database/
│   │   ├── test_models.py
│   │   └── test_repositories.py
│   └── test_services/
│       ├── test_checklist_optimizer.py
│       └── test_approval_workflow.py
│
├── e2e/                           # E2E tests
│   ├── __init__.py
│   ├── test_review_workflow.py
│   ├── test_approval_workflow.py
│   └── test_report_generation.py
│
├── performance/                   # Performance tests
│   ├── __init__.py
│   ├── test_api_performance.py
│   └── test_database_performance.py
│
├── security/                      # Security tests
│   ├── __init__.py
│   ├── test_authentication.py
│   └── test_input_validation.py
│
├── fixtures/                      # Test fixtures
│   ├── __init__.py
│   ├── sample_checklists.py
│   ├── sample_projects.py
│   └── sample_responses.py
│
└── data/                          # Test data
    ├── checklists/
    ├── voice_samples/
    └── expected_outputs/
```

---

### Fixtures and Helpers

**conftest.py:**

```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models import Base
from app.core.config import settings

@pytest.fixture(scope="session")
def test_db_url():
    """Test database URL"""
    return "sqlite+aiosqlite:///:memory:"

@pytest.fixture
async def db_session(test_db_url):
    """Create async database session for testing"""
    engine = create_async_engine(test_db_url, echo=True)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
def sample_project_data():
    """Sample project data for tests"""
    return {
        "name": "Test Project",
        "domain": "fintech",
        "description": "Test description",
        "tech_stack": ["Python", "FastAPI", "PostgreSQL"],
        "stakeholders": {
            "product_owner": "John Doe",
            "tech_lead": "Jane Smith"
        }
    }

@pytest.fixture
def sample_checklist_items():
    """Sample checklist items for tests"""
    return [
        {
            "item_code": "1.1",
            "area": "Scope, Planning & Governance",
            "question": "Are scope / SoW / baselines clearly defined?",
            "category": "delivery",
            "weight": 1.0,
            "is_review_mandatory": True
        },
        {
            "item_code": "1.2",
            "area": "Scope, Planning & Governance",
            "question": "Are change requests captured?",
            "category": "delivery",
            "weight": 1.0,
            "is_review_mandatory": True
        }
    ]
```

---

## Test Data Management

### Test Data Strategy

**Principles:**
1. **Isolation:** Each test has its own data
2. **Repeatability:** Tests produce same results every time
3. **Realistic:** Data resembles production (but anonymized)
4. **Minimal:** Only include necessary data

### Data Sources

| Source | Purpose | Status |
|--------|---------|--------|
| **Factories** | Create test data programmatically | ✅ Done |
| **Fixtures** | Pre-defined test data | ✅ Done |
| **Sample Files** | Excel checklists, voice samples | ✅ Done |
| **Production Snapshots** | Anonymized production data | ⏳ TODO |

### Data Cleanup

```python
@pytest.fixture
def cleanup_after_test():
    """Cleanup fixture"""
    yield
    # Cleanup code runs after test
    cleanup_test_data()
```

---

## Code Coverage

### Coverage Targets

| Metric | Target | Status |
|--------|--------|--------|
| **Line Coverage** | > 80% | ⏳ TODO |
| **Branch Coverage** | > 70% | ⏳ TODO |
| **Function Coverage** | > 90% | ⏳ TODO |
| **Critical Paths** | 100% | ⏳ TODO |

### Coverage Configuration

**pytest.ini:**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts = 
    -v
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
    -m "not slow"
markers =
    asyncio: mark test as async
    slow: mark test as slow (skip in CI by default)
    integration: mark as integration test
    e2e: mark as e2e test
    regression: mark as regression test
```

### Coverage Reports

```bash
# Run tests with coverage
pytest --cov=app --cov-report=html

# View HTML report
open htmlcov/index.html

# Check coverage summary
pytest --cov=app --cov-report=term-missing
```

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: testpass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      
      - name: Run linting
        run: |
          black --check app/
          isort --check-only app/
          flake8 app/
      
      - name: Run unit tests
        run: |
          pytest tests/unit/ -v --cov=app --cov-report=xml
      
      - name: Run integration tests
        run: |
          pytest tests/integration/ -v
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

### Test Execution Strategy

**Local Development:**
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_report_generator.py -v

# Run specific test
pytest tests/unit/test_report_generator.py::TestReportGenerator::test_calculate_compliance_score -v

# Run tests matching pattern
pytest -k "test_compliance" -v

# Run with coverage
pytest --cov=app --cov-report=html

# Run only fast tests (exclude slow)
pytest -m "not slow" -v
```

**CI/CD Pipeline:**
1. Lint check (Black, isort, flake8)
2. Unit tests (parallel)
3. Integration tests
4. Security scan (bandit, safety)
5. Coverage report
6. Build artifact

---

## Test Standards

### Naming Conventions

```python
# Test classes
class Test<Component>:
    """Docstring"""

# Test methods
def test_<method>_<scenario>_<expected>(self):
    """Docstring explaining test"""

# Fixtures
@pytest.fixture
def <component>_<purpose>():
    """Create <component> for <purpose>"""
```

**Examples:**

```python
class TestReportGenerator:
    """Tests for ReportGenerator service"""
    
    def test_calculate_compliance_score_all_green(self):
        """Test score is 100 when all responses are green"""
    
    def test_calculate_compliance_score_excludes_na(self):
        """Test NA responses are excluded from score calculation"""
    
    @pytest.fixture
    def generator_with_sample_data(self):
        """Create generator with sample responses for testing"""
```

---

### Test Structure (AAA Pattern)

```python
def test_example():
    # Arrange - Setup test data and mocks
    input_data = {"key": "value"}
    expected = "expected_result"
    
    # Act - Execute the code being tested
    result = process_data(input_data)
    
    # Assert - Verify the outcome
    assert result == expected
```

---

### Test Documentation

**Every test should have:**
1. **Descriptive name** - What is being tested
2. **Docstring** - Scenario and expected behavior
3. **Clear assertions** - What is being verified
4. **Comments** - For complex setup or edge cases

**Example:**

```python
def test_voice_response_with_background_noise(self):
    """
    Test voice transcription handles background noise gracefully.
    
    Scenario: User responds via voice with background noise present.
    Expected: Transcription succeeds with minor accuracy loss.
    """
    # Arrange
    audio_file = "tests/data/voice_samples/noisy_response.wav"
    
    # Act
    transcript = await self.voice_interface.speech_to_text(audio_file)
    
    # Assert
    assert transcript is not None
    assert len(transcript) > 0
    # Note: Exact match not required due to noise
    assert "yes" in transcript.lower()
```

---

## Appendix

### A. Test Checklist

**Before Merging:**
- [ ] All new code has tests
- [ ] All tests pass
- [ ] Coverage meets target (>80%)
- [ ] No flaky tests
- [ ] Security tests included
- [ ] Performance tests included (if applicable)

### B. References

- [PRD](requirements.md)
- [Design Specification](design.md)
- [Architecture Overview](internal/architecture/overview.md)

### C. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-03-27 | QA Team | Initial release |

---

*Document Owner: QA Team*  
*Next Review: June 2026*  
*AI Tech & Delivery Review Agent v1.0.0*

