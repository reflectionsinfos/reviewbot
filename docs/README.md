# AI Tech & Delivery Review Agent - Documentation Hub

Welcome to the comprehensive documentation for the AI-powered project review system.

---

## 📚 Documentation Categories

### 🔒 Internal Documentation (For Developers)

For team members working on the codebase, architecture, and deployment.

| Topic | Description | Link |
|-------|-------------|------|
| **Architecture** | System design, components, data flow | [`docs/internal/architecture/`](internal/architecture/) |
| **Development** | Setup guide, testing, code style | [`docs/internal/development/`](internal/development/) |
| **Deployment** | Docker, production, CI/CD | [`docs/internal/deployment/`](internal/deployment/) |
| **API Reference** | Complete API documentation | [`docs/internal/api/`](internal/api/) |
| **Services** | Service layer documentation | [`docs/internal/services/`](internal/services/) |
| **Database** | Schema, models, migrations | [`docs/internal/database/`](internal/database/) |
| **Agent** | LangGraph workflow, states, RAG | [`docs/internal/agent/`](internal/agent/) |

---

### 📖 External Documentation (For End Users)

For project managers, reviewers, and stakeholders using the system.

| Topic | Description | Link |
|-------|-------------|------|
| **Getting Started** | Quick start and onboarding | [`docs/external/getting-started.md`](external/getting-started.md) |
| **Workflows** | Step-by-step usage guides | [`docs/external/workflows/`](external/workflows/) |
| **Features** | Feature documentation | [`docs/external/features/`](external/features/) |
| **Troubleshooting** | Common issues and solutions | [`docs/external/troubleshooting.md`](external/troubleshooting.md) |

---

### 🔌 API Documentation

For API consumers and integrators.

| Topic | Description | Link |
|-------|-------------|------|
| **OpenAPI Spec** | Machine-readable API spec | [`docs/api/openapi.yaml`](api/openapi.yaml) |
| **Interactive Docs** | Swagger UI (running server) | [http://localhost:8000/docs](http://localhost:8000/docs) |

---

## 🚀 Quick Links

### For New Users
1. [Getting Started Guide](external/getting-started.md)
2. [First Review Workflow](external/workflows/first-review.md)
3. [Quick Reference](../QUICK_REFERENCE.md)

### For Developers
1. [Architecture Overview](internal/architecture/overview.md)
2. [Development Setup](internal/development/setup-guide.md)
3. [API Reference](internal/api/reference.md)

### For DevOps
1. [Docker Deployment](internal/deployment/docker-guide.md)
2. [Production Readiness](internal/deployment/production-readiness.md)
3. [Troubleshooting](internal/deployment/troubleshooting.md)

---

## 📁 Documentation Structure

```
docs/
├── README.md                        # This file
├── internal/                        # For developers/maintainers
│   ├── architecture/
│   │   ├── overview.md
│   │   ├── components.md
│   │   └── data-flow.md
│   ├── development/
│   │   ├── setup-guide.md
│   │   ├── testing.md
│   │   └── code-style.md
│   ├── deployment/
│   │   ├── docker-guide.md
│   │   ├── production-readiness.md
│   │   └── ci-cd.md
│   ├── api/
│   │   └── reference.md
│   ├── services/
│   │   ├── checklist-parser.md
│   │   └── report-generator.md
│   ├── database/
│   │   ├── schema.md
│   │   └── models.md
│   └── agent/
│       ├── workflow.md
│       └── rag-assessment.md
├── external/                        # For end users
│   ├── getting-started.md
│   ├── workflows/
│   │   ├── first-review.md
│   │   ├── checklist-upload.md
│   │   └── approval-process.md
│   ├── features/
│   │   ├── voice-interface.md
│   │   └── report-generation.md
│   └── troubleshooting.md
└── api/                             # API documentation
    └── openapi.yaml
```

---

## 🎯 Documentation Standards

### Internal vs External

| Aspect | Internal Docs | External Docs |
|--------|---------------|---------------|
| **Audience** | Developers, DevOps | End users, PMs, Stakeholders |
| **Content** | Code, architecture, deployment | Features, workflows, how-to |
| **Tone** | Technical, detailed | User-friendly, task-oriented |
| **Examples** | Code snippets, configs | Screenshots, step-by-step |

### Writing Guidelines

1. **Use clear headings** - Each page should have a clear purpose
2. **Include examples** - Show, don't just tell
3. **Keep updated** - Outdated docs are worse than no docs
4. **Link liberally** - Cross-reference related content
5. **Use tables** - For comparisons and quick reference
6. **Add diagrams** - Architecture and flow diagrams help understanding

---

## 🤖 AI/LLM Context Files

For AI assistants and coding agents:

| File | Purpose | Link |
|------|---------|------|
| **llms.txt** | Full project context for AI agents | [`../llms.txt`](../llms.txt) |
| **llms-public.txt** | Public-only context (no secrets) | [`../llms-public.txt`](../llms-public.txt) |

### AI Agent Folders

| Agent | Configuration | Skills |
|-------|---------------|--------|
| **Qwen** | [`.qwen/`](../.qwen/) | [`.qwen/skills/`](../.qwen/skills/) |
| **Claude** | [`.claude/`](../.claude/) | [`.claude/skills/`](../.claude/skills/) |
| **Generic** | [`.agent/`](../.agent/) | [`.agent/skills/`](../.agent/skills/) |

---

## 📞 Related Resources

- **Main README** - Project overview and quick start
- **QUICK_REFERENCE** - Command quick reference
- **WORKFLOWS** - Detailed usage workflows
- **GitHub Repo** - Source code and issues

---

*Last updated: March 27, 2026*  
*AI Tech & Delivery Review Agent v1.0.0*
