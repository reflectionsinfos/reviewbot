# Generic AI Agent - Skills Repository

> Reusable skills for any AI assistant working on this project

---

## 📚 Available Skills

### Development Skills

| Skill | Description | Location |
|-------|-------------|----------|
| **Code Review** | Systematic code review checklist | `skills/code-review.md` |
| **Testing** | Writing effective unit/integration tests | `skills/testing.md` |
| **Debugging** | Systematic debugging approach | `skills/debugging.md` |
| **Refactoring** | Safe refactoring techniques | `skills/refactoring.md` |
| **Documentation** | Writing clear documentation | `skills/documentation.md` |

### Domain Skills

| Skill | Description | Location |
|-------|-------------|----------|
| **FastAPI** | FastAPI best practices | `skills/fastapi.md` |
| **SQLAlchemy** | Async database patterns | `skills/sqlalchemy.md` |
| **LangGraph** | Building stateful workflows | `skills/langgraph.md` |
| **OpenAI** | LLM integration patterns | `skills/openai.md` |
| **Voice Interface** | STT/TTS integration | `skills/voice-interface.md` |

### Process Skills

| Skill | Description | Location |
|-------|-------------|----------|
| **Task Planning** | Breaking down complex tasks | `skills/task-planning.md` |
| **Git Workflow** | Git best practices | `skills/git-workflow.md` |
| **Security Review** | Security-focused analysis | `skills/security-review.md` |
| **Performance** | Performance optimization | `skills/performance.md` |

---

## 🎯 Skill Usage

### How to Use Skills

1. **Identify the task** - What needs to be done?
2. **Select appropriate skill** - Choose from the list above
3. **Follow the skill guide** - Apply the techniques
4. **Adapt to context** - Adjust based on project specifics

### Example: Code Review

```markdown
Task: Review pull request #42

1. Open skill guide: skills/code-review.md
2. Follow checklist:
   - Correctness ✓
   - Security ✓
   - Performance ✓
   - Readability ✓
   - Testing ✓
3. Provide feedback using template
```

---

## 📖 Skill Templates

### Code Review Template

```markdown
## Code Review: [PR Title]

### Summary
[Brief overview]

### Review Status
[✅ Approved | ⚠️ Changes Requested | 📝 Commented]

### Feedback

#### Critical Issues
1. [Issue + fix]

#### Medium Priority
1. [Issue + suggestion]

#### Suggestions
1. [Optional improvement]

### Testing
- [ ] Tests added
- [ ] Tests passing
- [ ] Edge cases covered

### Security
- [ ] No hardcoded secrets
- [ ] Input validation
- [ ] SQL parameterized
```

### Test Writing Template

```python
import pytest

class TestFeature:
    """Test feature functionality"""
    
    @pytest.fixture
    def setup_data(self):
        """Prepare test data"""
        return {"key": "value"}
    
    def test_happy_path(self, setup_data):
        """Test normal operation"""
        # Arrange
        # Act
        # Assert
    
    def test_edge_case(self):
        """Test boundary condition"""
        # Arrange
        # Act
        # Assert
    
    def test_error_handling(self):
        """Test error scenarios"""
        with pytest.raises(ExpectedError):
            # Code that should raise
```

---

## 🛠️ Skill Development

### Adding New Skills

1. **Identify pattern** - Common task that needs standardization
2. **Document approach** - Write step-by-step guide
3. **Add examples** - Show practical application
4. **Link related skills** - Cross-reference
5. **Update index** - Add to this file

### Skill Format

```markdown
# Skill Name

> Brief description

---

## Purpose
What this skill does

## When to Use
Situations where this skill applies

## How to Apply
Step-by-step instructions

## Examples
Practical examples

## Common Pitfalls
What to avoid

## Related Skills
Links to other relevant skills
```

---

## 📚 Learning Resources

### Internal
- [Architecture Overview](../../docs/internal/architecture/overview.md)
- [API Reference](../../docs/internal/api/reference.md)
- [Database Schema](../../docs/internal/database/schema.md)

### External
- FastAPI Docs: https://fastapi.tiangolo.com/
- LangGraph Docs: https://langchain-ai.github.io/langgraph/
- SQLAlchemy Docs: https://docs.sqlalchemy.org/
- OpenAI Docs: https://platform.openai.com/docs/

---

*Last updated: March 27, 2026*  
*AI Agent Skills Repository v1.0.0*
