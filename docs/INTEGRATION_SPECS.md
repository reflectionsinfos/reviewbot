# ReviewBot v2.0 - Integration Specifications

> API contracts and integration patterns for GitHub, SonarQube, Jenkins, and other tools

**Version:** 1.0  
**Date:** March 27, 2026  
**Status:** Ready for Implementation  
**Owner:** Integration Team

---

## 🔌 Integration Overview

### Supported Integrations

| Integration | Purpose | Priority | Status |
|-------------|---------|----------|--------|
| **GitHub** | Code repository access | Must Have | Designed |
| **GitLab** | Code repository access | Must Have | Designed |
| **SonarQube** | Code quality metrics | Must Have | Designed |
| **Jenkins** | CI/CD pipeline analysis | Must Have | Designed |
| **GitHub Actions** | CI/CD pipeline analysis | Must Have | Designed |
| **Confluence** | Documentation analysis | Should Have | Designed |
| **AWS** | Infrastructure analysis | Should Have | Designed |

---

## 🔗 GitHub Integration

### Authentication

```yaml
Method: OAuth 2.0
Authorization URL: https://github.com/login/oauth/authorize
Token URL: https://github.com/login/oauth/access_token
Scopes Required:
  - repo (Full control of private repositories)
  - read:org (Read org and team membership)
  - read:user (Read user profile data)
```

### API Endpoints

```yaml
# Repository Access
GET /api/v1/integrations/github/repos/{repo_id}
Response:
  id: integer
  name: string
  full_name: string
  private: boolean
  default_branch: string
  created_at: timestamp
  updated_at: timestamp

# File Content
GET /api/v1/integrations/github/repos/{repo_id}/contents/{path}
Parameters:
  ref: string (branch/tag, default: main)
Response:
  path: string
  sha: string
  size: integer
  download_url: string
  content: string (base64 encoded)

# Pull Requests
GET /api/v1/integrations/github/repos/{repo_id}/pulls
Parameters:
  state: string (open, closed, all)
  base: string (branch name)
Response:
  - id: integer
    number: integer
    title: string
    state: string
    created_at: timestamp
    merged: boolean
    merge_commit_sha: string

# Commits
GET /api/v1/integrations/github/repos/{repo_id}/commits
Parameters:
  sha: string (branch/tag)
  since: timestamp
  until: timestamp
Response:
  - sha: string
    commit:
      message: string
      author:
        name: string
        date: timestamp
    stats:
      additions: integer
      deletions: integer
      total: integer

# Coverage Report (if available)
GET /api/v1/integrations/github/repos/{repo_id}/check-runs/{check_run_id}
Response:
  name: string
  status: string
  conclusion: string
  output:
    summary: string
    text: string (may contain coverage data)
```

### Rate Limiting

```yaml
Rate Limit: 5000 requests per hour (authenticated)
Headers:
  X-RateLimit-Limit: 5000
  X-RateLimit-Remaining: 4990
  X-RateLimit-Reset: 1679900000

Strategy:
  - Cache responses where possible
  - Use conditional requests (ETag)
  - Implement exponential backoff
  - Queue requests when approaching limit
```

---

## 🔗 GitLab Integration

### Authentication

```yaml
Method: OAuth 2.0
Authorization URL: https://gitlab.com/oauth/authorize
Token URL: https://gitlab.com/oauth/token
Scopes Required:
  - api (Full API access)
  - read_repository (Read repository data)
```

### API Endpoints

```yaml
# Repository Access
GET /api/v1/integrations/gitlab/projects/{project_id}
Response:
  id: integer
  name: string
  path_with_namespace: string
  default_branch: string
  created_at: timestamp
  last_activity_at: timestamp

# Files
GET /api/v1/integrations/gitlab/projects/{project_id}/repository/files/{file_path}
Parameters:
  ref: string (branch name)
Response:
  file_name: string
  file_path: string
  size: integer
  encoding: string
  content: string
  last_commit_id: string

# Merge Requests
GET /api/v1/integrations/gitlab/projects/{project_id}/merge_requests
Parameters:
  state: string (opened, closed, merged)
  target_branch: string
Response:
  - id: integer
    iid: integer
    title: string
    state: string
    created_at: timestamp
    merged_at: timestamp
    merged_by:
      id: integer
      name: string

# Commits
GET /api/v1/integrations/gitlab/projects/{project_id}/repository/commits
Parameters:
  ref_name: string
  since: timestamp
  until: timestamp
Response:
  - id: string
    short_id: string
    title: string
    created_at: timestamp
    stats:
      additions: integer
      deletions: integer
      total: integer

# Coverage
GET /api/v1/integrations/gitlab/projects/{project_id}/badges
Response:
  - id: integer
    link_url: string
    image_url: string (may contain coverage badge)
```

---

## 🔗 SonarQube Integration

### Authentication

```yaml
Method: Basic Auth or Token
Header: Authorization: Basic {base64(token:)}
or
Header: Authorization: Bearer {token}
```

### API Endpoints

```yaml
# Project Quality Gate
GET /api/v1/integrations/sonarqube/qualitygates/project
Parameters:
  projectKey: string
Response:
  projectStatus:
    status: string (OK, WARN, ERROR)
    conditions:
      - metricKey: string (coverage, reliability, security)
        operator: string (GT, LT, EQ, NE)
        periodIndex: integer
        threshold: string
        actualValue: string
        status: string (OK, WARN, ERROR)

# Project Measures
GET /api/v1/integrations/sonarqube/measures/component
Parameters:
  componentKey: string
  metricKeys: string (comma-separated)
    - coverage
    - ncloc
    - violations
    - code_smells
    - bugs
    - vulnerabilities
    - security_rating
    - reliability_rating
    - sqale_rating
Response:
  component:
    measures:
      - metric: string
        value: string
        bestValue: string

# Issues
GET /api/v1/integrations/sonarqube/issues/search
Parameters:
  projects: string
  severities: string (comma-separated: BLOCKER, CRITICAL, MAJOR)
  types: string (CODE_SMELL, BUG, VULNERABILITY)
  ps: integer (page size, default: 25)
  p: integer (page number)
Response:
  total: integer
  p: integer
  ps: integer
  issues:
    - key: string
      rule: string
      severity: string
      type: string
      status: string
      message: string
      line: integer
      component: string
      creationDate: timestamp
      updateDate: timestamp

# Hotspots (Security)
GET /api/v1/integrations/sonarqube/hotspots/search
Parameters:
  projectKey: string
  status: string (TO_REVIEW, IN_REVIEW, FIXED, SAFE)
Response:
  total: integer
  hotspots:
    - key: string
      message: string
      line: integer
      severity: string
      status: string
      creationDate: timestamp
```

### Quality Thresholds

```yaml
Default Thresholds:
  coverage:
    min: 80  # percentage
  security_rating:
    min: "A"  # A, B, C, D, E
  reliability_rating:
    min: "A"
  security_review_rating:
    min: "A"
  blocker_issues:
    max: 0
  critical_issues:
    max: 0
  major_issues:
    max: 5
```

---

## 🔗 Jenkins Integration

### Authentication

```yaml
Method: API Token
Header: Authorization: Basic {base64(username:token)}
```

### API Endpoints

```yaml
# Job Information
GET /api/v1/integrations/jenkins/jobs/{job_name}
Response:
  name: string
  color: string (blue, red, yellow, etc.)
  buildable: boolean
  builds:
    - number: integer
      url: string
      timestamp: integer

# Build Details
GET /api/v1/integrations/jenkins/jobs/{job_name}/builds/{build_number}
Response:
  number: integer
  result: string (SUCCESS, FAILURE, UNSTABLE)
  duration: integer (milliseconds)
  timestamp: integer
  building: boolean
  actions:
    - causes: [...]
      parameters: [...]

# Test Results
GET /api/v1/integrations/jenkins/jobs/{job_name}/builds/{build_number}/testReport
Response:
  duration: integer
  empty: boolean
  failCount: integer
  passCount: integer
  skipCount: integer
  suites:
    - cases:
        - className: string
          testName: string
          status: string (PASSED, FAILED, SKIPPED)
          duration: integer
          errorDetails: string (if failed)

# Deployment History
GET /api/v1/integrations/jenkins/jobs/{job_name}/deployments
Parameters:
  environment: string (staging, production)
  limit: integer (default: 10)
Response:
  - build_number: integer
    environment: string
    status: string (success, failed, rolled_back)
    timestamp: integer
    duration: integer
    deployed_by: string
```

### Pipeline Analysis

```yaml
Metrics to Collect:
  - Build success rate (last 10 builds)
  - Average build duration
  - Test pass rate
  - Deployment frequency
  - Deployment success rate
  - Rollback frequency

Thresholds:
  build_success_rate:
    min: 95  # percentage
  test_pass_rate:
    min: 100  # percentage
  deployment_success_rate:
    min: 95  # percentage
```

---

## 🔗 GitHub Actions Integration

### Authentication

```yaml
Method: GitHub Token (from OAuth)
Same token as GitHub repository access
```

### API Endpoints

```yaml
# Workflow Runs
GET /api/v1/integrations/github-actions/repos/{repo_id}/actions/runs
Parameters:
  branch: string
  event: string (push, pull_request, schedule)
  status: string (completed, in_progress, queued)
Response:
  total_count: integer
  workflow_runs:
    - id: integer
      name: string
      status: string
      conclusion: string
      created_at: timestamp
      updated_at: timestamp
      run_attempt: integer
      run_number: integer

# Workflow Usage
GET /api/v1/integrations/github-actions/repos/{repo_id}/actions/workflows/{workflow_id}
Response:
  id: integer
  name: string
  path: string
  state: string (active, disabled)
  created_at: timestamp
  updated_at: timestamp

# Job Details
GET /api/v1/integrations/github-actions/repos/{repo_id}/actions/runs/{run_id}/jobs
Response:
  total_count: integer
  jobs:
    - id: integer
      name: string
      status: string
      conclusion: string
      started_at: timestamp
      completed_at: timestamp
      steps:
        - name: string
          status: string
          conclusion: string
          number: integer
```

---

## 🔗 Confluence Integration

### Authentication

```yaml
Method: Basic Auth or Token
Header: Authorization: Basic {base64(email:token)}
```

### API Endpoints

```yaml
# Space Information
GET /api/v1/integrations/confluence/spaces/{space_key}
Response:
  key: string
  name: string
  description: string
  homepage:
    id: integer
    title: string
    type: string

# Page Content
GET /api/v1/integrations/confluence/pages/{page_id}
Parameters:
  expand: string (body.storage, version, history)
Response:
  id: integer
  title: string
  type: string
  status: string (current, draft)
  version:
    number: integer
    when: timestamp
    by:
      displayName: string
  space:
    key: string
    name: string
  body:
    storage:
      value: string (HTML)
      representation: string

# Search Pages
GET /api/v1/integrations/confluence/search
Parameters:
  cql: string (Confluence Query Language)
    Example: "type=page AND space=DEV AND title~'Architecture'"
  limit: integer (default: 25)
Response:
  results:
    - content:
        id: integer
        type: string
        title: string
      excerpt: string
      url: string
  size: integer
  totalSize: integer
```

### Documentation Analysis

```yaml
Checks:
  - ADR presence (title contains "Architecture Decision")
  - Last updated timestamp
  - View count (engagement)
  - Comments count (collaboration)
  - Attachments (diagrams, specs)

Thresholds:
  adr_count:
    min: 1
  last_updated:
    max_days_ago: 90
  critical_docs_present:
    required:
      - Architecture Overview
      - Deployment Guide
      - API Documentation
      - Runbooks
```

---

## 🔗 AWS Integration

### Authentication

```yaml
Method: IAM Role or Access Keys
SDK: boto3 (Python)
Required Permissions:
  - cloudformation:DescribeStacks
  - cloudwatch:GetMetricData
  - ec2:DescribeInstances
  - s3:GetBucketPolicy
  - iam:GetPolicy
  - securityhub:GetFindings
```

### API Endpoints (via boto3)

```python
# CloudFormation Stacks
import boto3
cf = boto3.client('cloudformation')

response = cf.describe_stacks(StackName='neu-money-prod')
Checks:
  - Stack status (CREATE_COMPLETE, UPDATE_COMPLETE)
  - Template validation
  - Resource drift detection
  - Outputs (endpoints, ARNs)

# CloudWatch Metrics
cw = boto3.client('cloudwatch')

response = cw.get_metric_data(
    MetricDataQueries=[
        {
            'Id': 'error_rate',
            'MetricStat': {
                'Metric': {
                    'Namespace': 'AWS/ApplicationELB',
                    'MetricName': 'HTTPCode_Target_5XX_Count',
                    'Dimensions': [{'Name': 'LoadBalancer', 'Value': lb_arn}]
                },
                'Period': 3600,
                'Stat': 'Sum'
            }
        }
    ]
)
Checks:
  - Error rates
  - Latency metrics
  - Request counts
  - Health check status

# Security Hub
sh = boto3.client('securityhub')

response = sh.get_findings(
    Filters={
        'RecordState': ['ACTIVE'],
        'Severity': [{'Label': 'CRITICAL'}, {'Label': 'HIGH'}]
    }
)
Checks:
  - Critical findings count
  - High findings count
  - Unresolved findings age
  - Compliance status
```

---

## 🛡️ Security & Error Handling

### Security Best Practices

```yaml
Credentials:
  - Never store in code
  - Use environment variables or secrets manager
  - Rotate tokens regularly (90 days)
  - Use least-privilege access

API Calls:
  - Always use HTTPS
  - Validate SSL certificates
  - Implement request signing (AWS SigV4)
  - Log all API calls (audit trail)

Data Protection:
  - Encrypt sensitive data at rest
  - Mask tokens in logs
  - Implement data retention policies
  - GDPR compliance for user data
```

### Error Handling Strategy

```yaml
Retry Logic:
  - Exponential backoff (1s, 2s, 4s, 8s, 16s)
  - Max retries: 5
  - Retry on: 429 (rate limit), 5xx (server error)
  - Don't retry on: 4xx (client error)

Error Responses:
  401 Unauthorized:
    Action: Refresh token, notify user
  403 Forbidden:
    Action: Check permissions, notify admin
  404 Not Found:
    Action: Log error, skip check
  429 Rate Limit:
    Action: Backoff, retry later
  500 Server Error:
    Action: Backoff, retry, escalate if persistent

Fallback Strategies:
  - Cache last known good state
  - Graceful degradation (skip non-critical checks)
  - Manual review trigger if all automated checks fail
```

---

## 📊 Integration Status Dashboard

```yaml
Health Checks:
  - Connection status (connected, disconnected, error)
  - Last sync timestamp
  - API quota remaining
  - Error rate (last 24h)

Metrics to Track:
  - Total API calls per day
  - Average response time
  - Error rate by integration
  - Cache hit rate
  - Rate limit utilization

Alerts:
  - Connection lost
  - API quota > 80% utilized
  - Error rate > 5%
  - Response time > 2s (p95)
```

---

## 🔗 Related Documents

- [Autonomous Code Review Spec](AUTONOMOUS_CODE_REVIEW.md)
- [Database Schema](DATABASE_SCHEMA_V2.md)
- [Design Phase Kickoff](DESIGN_PHASE_KICKOFF.md)

---

*Document Owner: Integration Team*  
*Status: Ready for Implementation*  
*Next: Implement GitHub integration*
