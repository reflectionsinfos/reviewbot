# Spec-Driven Development Guide

> AI-Powered, Specification-First Development Workflow

**Version:** 1.0.0  
**Last Updated:** March 27, 2026  
**Status:** Active  
**Owner:** Engineering Team

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Development Workflow](#development-workflow)
3. [Specification Documents](#specification-documents)
4. [AI-Assisted Development](#ai-assisted-development)
5. [Code Generation from Specs](#code-generation-from-specs)
6. [Quality Gates](#quality-gates)
7. [Example: Adding a New Feature](#example-adding-a-new-feature)

---

## Overview

### What is Spec-Driven Development?

**Spec-Driven Development** is a methodology where:
1. **Specifications are written first** - Before any code
2. **AI agents use specs for context** - LLMs understand requirements
3. **Code is generated/validated against specs** - Automated compliance
4. **Tests verify spec compliance** - Traceability maintained

### Benefits

| Benefit | Description |
|---------|-------------|
| **Clarity** | Requirements are explicit and documented |
| **Consistency** | AI agents follow the same specifications |
| **Traceability** | Code links back to requirements |
| **Quality** | Automated validation against specs |
| **Speed** | AI can generate code from specifications |
| **Maintainability** | New developers understand system quickly |

### The Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                  Spec-Driven Development Cycle                  │
│                                                                 │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐               │
│  │  Write   │────▶│   AI     │────▶│  Review  │               │
│  │   Spec   │     │ Generate │     │  & Test  │               │
│  └──────────┘     └──────────┘     └──────────┘               │
│       ▲                                      │                 │
│       │                                      │                 │
│       │                                      ▼                 │
│       │     ┌──────────┐     ┌──────────┐                     │
│       └─────│  Update  │◀────│  Validate│                     │
│             │   Spec   │     │  vs Spec │                     │
│             └──────────┘     └──────────┘                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Development Workflow

### Phase 1: Requirements → Spec

**Input:** Product requirements (PRD), user stories  
**Output:** Technical specification

**Steps:**

1. **Read PRD** - Understand requirements
2. **Write/Update Design Spec** - `docs/design.md`
3. **Define API Contracts** - OpenAPI specification
4. **Create Agent Specs** - For AI agents involved
5. **Review Specs** - Team approval

**Template:**

```markdown
# Feature Specification: [Feature Name]

## Requirements (from PRD)
- [Link to PRD section]

## Design
- Architecture changes
- Component modifications
- Data model changes

## API Changes
- New endpoints
- Modified endpoints
- Request/Response schemas

## Agent Changes
- Which agents are affected
- New prompts/workflows

## Testing Requirements
- Unit tests needed
- Integration tests needed
- E2E tests needed

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
```

---

### Phase 2: Spec → Code (AI-Assisted)

**Input:** Approved specification  
**Output:** Implementation code

**Steps:**

1. **Provide spec to AI** - Context for code generation
2. **Generate code** - AI writes initial implementation
3. **Generate tests** - AI writes tests from spec
4. **Review code** - Human review
5. **Iterate** - Fix issues

**AI Prompt Template:**

```markdown
Based on the specification below, implement the feature:

## Specification
[Link to spec document]

## Requirements
- [List key requirements]

## Constraints
- Follow existing code patterns
- Include type hints
- Add docstrings
- Write tests

## Generate:
1. Implementation code
2. Unit tests
3. Integration tests
4. Documentation updates
```

---

### Phase 3: Code → Validation

**Input:** Generated code  
**Output:** Validated, merged code

**Steps:**

1. **Run tests** - Verify functionality
2. **Check coverage** - Ensure adequate testing
3. **Validate against spec** - Traceability check
4. **Code review** - Human approval
5. **Merge** - Add to codebase

**Validation Checklist:**

```markdown
## Pre-Merge Checklist

### Code Quality
- [ ] Type hints present
- [ ] Docstrings added
- [ ] Code formatted (Black, isort)
- [ ] No linting errors

### Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Coverage > 80%
- [ ] No flaky tests

### Spec Compliance
- [ ] All requirements implemented
- [ ] API matches specification
- [ ] Agent behavior matches spec
- [ ] Documentation updated

### Security
- [ ] No hardcoded secrets
- [ ] Input validation added
- [ ] Authentication checks present
- [ ] Security review completed
```

---

## Specification Documents

### Document Hierarchy

```
docs/
├── requirements.md              # PRD - Product requirements
│   └── Links to user stories
│
├── design.md                    # Technical design
│   ├── Architecture decisions
│   ├── Component design
│   └── API design
│
├── test-strategy.md             # Testing approach
│   └── Test requirements
│
└── internal/
    ├── architecture/
    │   └── overview.md          # System architecture
    │
    └── api/
        └── reference.md         # API documentation
```

### Specification Traceability

```
PRD (requirements.md)
    │
    ├── User Story US-1.1
    │   └── Design Section 3.2
    │       └── API Endpoint POST /api/projects
    │           └── Implementation: app/api/routes/projects.py
    │               └── Tests: tests/integration/test_api/test_projects.py
    │
    └── User Story US-2.1
        └── Agent Spec: ReviewAgent
            └── Workflow: initialize_review
                └── Implementation: app/agents/review_agent/agent.py
```

---

## AI-Assisted Development

### Using AI Agents Effectively

#### 1. Provide Context

**Good:**
```markdown
Implement a new endpoint for project deletion.

Context:
- See docs/design.md section 5.3
- Follow pattern in app/api/routes/projects.py
- Use existing authentication (get_current_user)
- Add to tests/integration/test_api/test_projects.py
```

**Bad:**
```markdown
Add delete endpoint
```

---

#### 2. Reference Specifications

**Good:**
```markdown
Based on the agent spec in app/agents/review_agent/AGENT_SPEC.md:

Implement the `assess_rag` node with LLM-based assessment.

Requirements from spec:
- Use gpt-4-turbo-preview
- Follow RAG_ASSESSMENT_PROMPT template
- Return green/amber/red/na
```

**Bad:**
```markdown
Make RAG assessment smarter
```

---

#### 3. Specify Output Format

**Good:**
```markdown
Generate:
1. Implementation in app/services/new_service.py
2. Tests in tests/unit/test_new_service.py
3. Update app/services/__init__.py
4. Add documentation to docs/internal/services/new-service.md

Format:
- Python 3.11+
- Type hints required
- Google-style docstrings
- pytest for tests
```

**Bad:**
```markdown
Create a new service
```

---

### AI Prompt Library

#### Prompt: Implement Feature from Spec

```markdown
## Task
Implement [feature name] based on the specification.

## Specification
- PRD: docs/requirements.md#FR-X.X
- Design: docs/design.md#section-x
- Agent Spec: app/agents/[agent]/AGENT_SPEC.md

## Requirements
1. [Requirement 1]
2. [Requirement 2]

## Constraints
- Follow existing patterns
- Include error handling
- Add logging
- Write tests

## Deliverables
1. Implementation code
2. Unit tests
3. Integration tests
4. Documentation updates
```

---

#### Prompt: Generate Tests from Spec

```markdown
## Task
Write comprehensive tests for [component] based on specification.

## Specification
- [Link to spec section]

## Test Requirements
- Unit tests for all public methods
- Integration tests for API endpoints
- Edge cases from spec
- Performance benchmarks if applicable

## Coverage Target
- Line coverage: > 80%
- Branch coverage: > 70%
- Critical paths: 100%

## Generate
1. Test file with all tests
2. Fixtures needed
3. Test data
```

---

#### Prompt: Review Code Against Spec

```markdown
## Task
Review this code against the specification.

## Specification
- [Link to spec]

## Code
[Code block or file path]

## Review Criteria
1. Does it implement all requirements?
2. Are there any deviations from spec?
3. Is error handling adequate?
4. Are tests comprehensive?
5. Any security concerns?

## Output
- List of compliant items
- List of deviations
- Suggested fixes
```

---

## Code Generation from Specs

### Example: API Endpoint from Spec

**Specification:**

```markdown
## Endpoint: DELETE /api/projects/{project_id}

**Purpose:** Delete a project

**Authentication:** Required (reviewer+)

**Path Parameters:**
- project_id (int): Project ID

**Responses:**
- 200: Project deleted successfully
- 404: Project not found
- 403: Insufficient permissions

**Side Effects:**
- Delete associated checklists
- Delete associated reviews
- Cascade delete all related data
```

**AI Prompt:**

```markdown
Based on the specification above, implement the DELETE endpoint.

Follow the pattern in app/api/routes/projects.py:
- Use Depends(get_current_user) for auth
- Use get_db for database session
- Return standard response format
- Add proper error handling

Generate:
1. Endpoint implementation
2. Unit tests
3. Integration tests
```

**Generated Code:**

```python
@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a project and all associated data.
    
    - **project_id**: Project identifier
    - **current_user**: Authenticated user
    - **Returns**: 200 on success, 404 if not found, 403 if unauthorized
    """
    # Check permissions
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Get project
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Cascade delete
    await db.delete(project)
    await db.commit()
    
    return {
        "message": "Project deleted successfully",
        "project_id": project_id
    }
```

---

### Example: Agent Node from Spec

**Specification:**

```markdown
## Agent Node: optimize_checklist

**Purpose:** Suggest domain-specific checklist additions

**Input:** ReviewState with project_domain

**Process:**
1. Check if domain is known
2. Get domain-specific items from ChecklistOptimizer
3. Add suggested items to checklist
4. Log optimization

**Output:** ReviewState with enhanced checklist

**Prompt:** See AGENT_SPEC.md section 5.3
```

**AI Prompt:**

```markdown
Implement the optimize_checklist node for the ReviewAgent.

Based on AGENT_SPEC.md section 5.3:
- Use ChecklistOptimizer service
- Check project_domain
- Add domain-specific items
- Handle unknown domains gracefully

Generate:
1. Node implementation
2. Tests for each domain
3. Tests for unknown domain
```

---

## Quality Gates

### Gate 1: Spec Review

**Before implementation:**

```markdown
## Spec Review Checklist

- [ ] Requirements are clear and testable
- [ ] Design is feasible and documented
- [ ] API contracts are defined
- [ ] Agent behavior is specified
- [ ] Test requirements are listed
- [ ] Acceptance criteria are defined
- [ ] Team has reviewed and approved
```

---

### Gate 2: Code Review

**Before merge:**

```markdown
## Code Review Checklist

### Spec Compliance
- [ ] All requirements implemented
- [ ] No undocumented features
- [ ] API matches specification
- [ ] Agent behavior matches spec

### Code Quality
- [ ] Follows coding standards
- [ ] Type hints present
- [ ] Docstrings added
- [ ] Error handling adequate

### Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Coverage meets target
- [ ] Edge cases covered

### Security
- [ ] No security vulnerabilities
- [ ] Authentication implemented
- [ ] Input validation present
- [ ] No hardcoded secrets
```

---

### Gate 3: Post-Merge Validation

**After merge:**

```markdown
## Post-Merge Checklist

- [ ] Tests pass in CI/CD
- [ ] No regressions detected
- [ ] Documentation deployed
- [ ] Monitoring configured
- [ ] Rollback plan documented
```

---

## Example: Adding a New Feature

### Scenario: Add "Pause Review" Feature

**Step 1: Update PRD**

```markdown
## FR-2.7: Pause and Resume Review

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-2.7.1 | Pause review session | Should Have | ⏳ TODO |
| FR-2.7.2 | Resume paused review | Should Have | ⏳ TODO |
| FR-2.7.3 | List paused reviews | Could Have | ⏳ TODO |
```

---

**Step 2: Update Design Spec**

```markdown
## Design: Pause/Resume Feature

### State Changes
- Add `paused_at` field to Review model
- Add `resumed_at` field to Review model
- Add `pause_review` node to agent workflow

### API Changes
- POST /api/reviews/{review_id}/pause
- POST /api/reviews/{review_id}/resume
- GET /api/reviews/?status=paused

### Agent Workflow
- Add conditional edge: if paused, save state
- On resume, restore state from database
```

---

**Step 3: Update Agent Spec**

```markdown
## New Node: pause_review

**Purpose:** Save review state and pause

**Trigger:** User requests pause

**Process:**
1. Save current state to database
2. Set session_status = "paused"
3. Record paused_at timestamp
4. Return confirmation

**Implementation:** See app/agents/review_agent/agent.py
```

---

**Step 4: Generate Code (AI-Assisted)**

```markdown
## AI Prompt

Implement the pause/resume review feature.

Specifications:
- PRD: docs/requirements.md#FR-2.7
- Design: docs/design.md#pause-resume-feature
- Agent Spec: app/agents/review_agent/AGENT_SPEC.md#pause_review

Generate:
1. Database migration for new fields
2. API endpoints (pause, resume, list paused)
3. Agent node implementation
4. Tests for all components
```

---

**Step 5: Review and Validate**

```markdown
## Validation Results

### Spec Compliance ✅
- [x] FR-2.7.1: Pause implemented
- [x] FR-2.7.2: Resume implemented
- [x] FR-2.7.3: List paused implemented

### Code Quality ✅
- [x] Type hints present
- [x] Docstrings added
- [x] Error handling adequate

### Testing ✅
- [x] Unit tests pass (15/15)
- [x] Integration tests pass (5/5)
- [x] Coverage: 87%

### Security ✅
- [x] Authentication required
- [x] Authorization checks present
- [x] No security issues
```

---

**Step 6: Merge and Deploy**

```bash
# Merge to develop
git checkout develop
git merge feature/pause-review

# Run full test suite
pytest tests/ -v --cov=app

# Deploy to staging
make deploy-staging

# Validate in staging
# ... manual testing ...

# Deploy to production
make deploy-production
```

---

## Appendix

### A. Specification Templates

**Feature Spec Template:**

```markdown
# Feature Specification: [Name]

## Overview
[Brief description]

## Requirements (PRD Links)
- [Link to PRD section]

## Design
[Architecture, components, data model]

## API Changes
[New/modified endpoints]

## Agent Changes
[Which agents, what changes]

## Testing Requirements
[What tests are needed]

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
```

---

### B. Related Documents

- [PRD](docs/requirements.md)
- [Design Spec](docs/design.md)
- [Test Strategy](docs/test-strategy.md)
- [Architecture](docs/internal/architecture/overview.md)

---

### C. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-03-27 | Engineering | Initial release |

---

*Document Owner: Engineering Team*  
*Next Review: June 2026*  
*AI Tech & Delivery Review Agent v1.0.0*
