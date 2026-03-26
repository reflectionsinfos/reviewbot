# Architectural Decisions

## Decision Log

### ADR-001: Use FastAPI as Web Framework

**Date:** 2026-03-25  
**Status:** Accepted

**Context:**
Need a modern, fast web framework for building REST APIs with automatic documentation.

**Decision:**
Use FastAPI instead of Flask or Django REST Framework.

**Rationale:**
- Async/await support for better performance
- Automatic OpenAPI/Swagger documentation
- Built-in request validation with Pydantic
- Type hints for better IDE support
- High performance (on par with Node.js and Go)

**Consequences:**
- Requires Python 3.7+
- Team needs to learn async patterns
- Smaller ecosystem than Django

---

### ADR-002: Use SQLite for Development, PostgreSQL for Production

**Date:** 2026-03-25  
**Status:** Accepted

**Context:**
Need a database solution that's easy for development but scalable for production.

**Decision:**
- Development: SQLite with aiosqlite
- Production: PostgreSQL with asyncpg

**Rationale:**
- SQLite: Zero configuration, file-based, perfect for local dev
- PostgreSQL: Robust, scalable, production-proven
- SQLAlchemy abstraction makes switching easy

**Consequences:**
- Need to test migrations on both databases
- Some PostgreSQL-specific features won't be available in dev

---

### ADR-003: Use LangGraph for Agent Orchestration

**Date:** 2026-03-25  
**Status:** Accepted

**Context:**
Need to orchestrate complex AI workflows with state management.

**Decision:**
Use LangGraph (from LangChain) for agent workflow management.

**Rationale:**
- Built for stateful, multi-step AI workflows
- Visual graph representation
- Integrates with LangChain ecosystem
- Supports conditional edges and loops
- Active development and community support

**Alternatives Considered:**
- Custom state machine: More control but more work
- Airflow: Overkill for this use case
- Temporal: More complex than needed

**Consequences:**
- Dependency on LangChain ecosystem
- Learning curve for team
- Additional abstraction layer

---

### ADR-004: Use OpenAI for LLM and Voice

**Date:** 2026-03-25  
**Status:** Accepted

**Context:**
Need LLM for intelligence and voice capabilities.

**Decision:**
Use OpenAI APIs for:
- GPT-4o for reasoning and analysis
- Whisper for speech-to-text
- OpenAI TTS for text-to-speech

**Rationale:**
- Best-in-class quality for all three services
- Single vendor for all AI needs
- Well-documented APIs
- Reliable and scalable

**Alternatives Considered:**
- Anthropic Claude: Good for LLM, no voice
- Google Cloud AI: Good but more complex setup
- Azure Cognitive Services: Enterprise-focused, complex pricing

**Consequences:**
- Vendor lock-in to OpenAI
- API costs scale with usage
- Requires internet connectivity

---

### ADR-005: Require Human Approval for All Reports

**Date:** 2026-03-25  
**Status:** Accepted

**Context:**
AI-generated reports need oversight before distribution.

**Decision:**
All reports require explicit human approval before being sent to stakeholders.

**Rationale:**
- AI can make mistakes or miss context
- Human judgment for sensitive findings
- Accountability and governance
- Builds trust in the system

**Implementation:**
- Report status: `pending` → `approved` or `rejected`
- Approval tracked with approver ID and timestamp
- Rejection allows comments for revision

**Consequences:**
- Adds step to workflow
- Requires approver availability
- Potential bottleneck if approver unavailable

---

### ADR-006: Use Async Database Operations

**Date:** 2026-03-25  
**Status:** Accepted

**Context:**
Need to handle concurrent requests efficiently.

**Decision:**
Use SQLAlchemy with async support (aiosqlite/asyncpg).

**Rationale:**
- Better resource utilization
- Handles concurrent requests without blocking
- Aligns with FastAPI async architecture
- Future-proof for high-traffic scenarios

**Consequences:**
- Requires async/await throughout codebase
- Some SQLAlchemy features not available in async
- Slightly more complex error handling

---

### ADR-007: Store Files Locally (Not Cloud Storage)

**Date:** 2026-03-25  
**Status:** Accepted

**Context:**
Need to store uploaded files and generated reports.

**Decision:**
Store files locally in `uploads/` and `reports/` directories.

**Rationale:**
- Simpler setup for development
- No cloud storage costs
- Faster local file access
- Easier debugging

**Alternatives Considered:**
- AWS S3: Better for production scale
- Azure Blob Storage: Good for Azure deployments
- Google Cloud Storage: Good for GCP deployments

**Consequences:**
- Need backup strategy for files
- Doesn't scale horizontally
- Migration needed for cloud deployment

**Future Consideration:**
For production, consider cloud storage with local fallback.

---

### ADR-008: Use JWT for Authentication

**Date:** 2026-03-25  
**Status:** Accepted

**Context:**
Need stateless authentication for API.

**Decision:**
Use JWT (JSON Web Tokens) with HS256 algorithm.

**Rationale:**
- Stateless (no session storage needed)
- Works well with microservices
- Built-in expiration
- Widely supported

**Implementation:**
- Token expiration: 30 minutes
- HS256 algorithm (symmetric)
- Store secret in environment variable

**Consequences:**
- Can't revoke tokens before expiration (short TTL mitigates)
- Secret key must be secured
- Consider asymmetric (RS256) for distributed systems

---

### ADR-009: Use RAG Status for Compliance Scoring

**Date:** 2026-03-25  
**Status:** Accepted

**Context:**
Need a simple, visual way to communicate compliance status.

**Decision:**
Use RAG (Red/Amber/Green) status with numeric scoring:
- Green: 100 points (fully compliant)
- Amber: 50 points (partially compliant)
- Red: 0 points (not compliant)
- NA: Excluded from calculation

**Rationale:**
- Industry-standard visual indicator
- Easy to understand
- Combines qualitative and quantitative
- Supports trend analysis

**Consequences:**
- Simplifies complex situations
- May need nuance for edge cases
- Threshold decisions (80/50) may need tuning

---

### ADR-010: Domain-Specific Checklist Enhancements

**Date:** 2026-03-25  
**Status:** Accepted

**Context:**
Different project domains have different compliance needs.

**Decision:**
Automatically suggest domain-specific checklist additions:
- Fintech: PCI-DSS, SOX, fraud detection
- Healthcare: HIPAA, PHI protection
- E-commerce: Peak load, inventory consistency
- Data Migration: Rollback, reconciliation

**Rationale:**
- Improves review relevance
- Catches domain-specific risks
- Demonstrates AI intelligence
- Reduces manual checklist customization

**Implementation:**
- Domain detection from project metadata
- Pre-defined domain additions
- LLM-powered contextual suggestions

**Consequences:**
- Need to maintain domain knowledge base
- May suggest irrelevant items initially
- Requires domain classification accuracy

---

### ADR-011: Use Markdown and PDF for Reports

**Date:** 2026-03-25  
**Status:** Accepted

**Context:**
Need report formats for different use cases.

**Decision:**
Generate reports in both Markdown and PDF formats.

**Rationale:**
- Markdown: Easy to version control, diff, edit
- PDF: Professional, printable, universal
- Covers both technical and business audiences

**Consequences:**
- Need to maintain two generators
- PDF styling requires extra work
- Markdown may not render consistently

---

### ADR-012: Use ChromaDB for Vector Storage

**Date:** 2026-03-25  
**Status:** Accepted

**Context:**
Need vector database for AI embeddings (future features).

**Decision:**
Use ChromaDB for vector storage.

**Rationale:**
- Lightweight, easy to set up
- No external dependencies
- Good for development and small production
- Can migrate to Pinecone/Weaviate for scale

**Consequences:**
- May need migration for large-scale deployments
- Limited advanced features vs. dedicated vector DBs

---

## Summary of Key Technologies

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Web Framework | FastAPI | Async, auto-docs, validation |
| Database ORM | SQLAlchemy | Abstraction, async support |
| AI Orchestration | LangGraph | Stateful workflows |
| LLM | OpenAI GPT-4o | Best quality |
| Voice STT/TTS | OpenAI Whisper/TTS | Integrated, high quality |
| Vector DB | ChromaDB | Simple, no dependencies |
| Authentication | JWT | Stateless, standard |
| File Storage | Local FS | Simple for now |
| Report Formats | Markdown + PDF | Both audiences |

---

*Last Updated: 2026-03-25*
