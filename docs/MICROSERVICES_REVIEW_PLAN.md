# Autonomous Review — Microservices Support Plan

## Current Status

| Capability | Status | Notes |
|-----------|--------|-------|
| Scan a single-service folder | ✅ Works | One service path, flat recursive walk |
| Scan monolithic project | ✅ Works | All code in one tree |
| Scan entire microservices root | ❌ Fails | File limit hit, no service isolation |
| Per-service compliance results | ❌ Not built | One result per checklist item (global) |
| Cross-service dependency analysis | ❌ Not built | No inter-service rules |
| Docker path access | ⚠️ Requires mount | Host paths need `C:\projects:/host-projects:ro` volume |

### Immediate Workaround (works today)
Point the review at **one service at a time**:
- Source path: `/host-projects/hatch-pay/backend/hatch-pay-accounting-day-service`
- This works with the current scanner — 1 service ≈ 100–150 files, well within the 2,000 file limit
- Run separate jobs per service

---

## Root Cause: Why Full Microservices Scan Fails

### 1. File budget exhaustion
`MAX_FILES_SCAN = 2000` — with 20+ services × ~100–150 files each, the scanner stops mid-fleet. Later services are never indexed.

### 2. No service boundaries
All files are mixed into one flat `FileIndex`. The LLM receives 3 files that may come from 3 different services — it cannot form a coherent picture of any single service.

### 3. File presence gives false GREEN
"Does a Dockerfile exist?" → returns GREEN if **any** service has one. Cannot tell which services are missing it.

### 4. One result per checklist item
The schema stores one `AutonomousReviewResult` per `(job, checklist_item)`. There is no axis for "which service". A report cannot say "Auth service: GREEN, Payment service: RED".

### 5. No microservices-specific checklist rules
The strategy router has no rules for: API contract testing, service-to-service auth, distributed tracing, per-service health endpoints, etc.

---

## Enhancement Plan

### Phase 1 — Docker Path Access (Done ✅)
Mount host projects folder into the container so reviewers can scan local code.

**Delivered:** `C:\projects:/host-projects:ro` volume in `docker-compose.yml`

**Usage in UI:** `/host-projects/hatch-pay/backend/<service-name>`

---

### Phase 2 — Multi-Service Job Mode
**Goal:** One job scans all services in a root folder, producing per-service results.

#### 2a. Schema change
Add `service_name` column to `AutonomousReviewResult`:
```sql
ALTER TABLE autonomous_review_results ADD COLUMN service_name VARCHAR;
```

#### 2b. New API field
`StartReviewRequest` gets an optional `scan_mode` field:
```json
{
  "project_id": 5,
  "checklist_id": 12,
  "source_path": "/host-projects/hatch-pay/backend",
  "scan_mode": "microservices",          // new
  "service_pattern": "hatch-pay-*"       // glob to identify service dirs
}
```

#### 2c. Orchestrator changes
```
For each service_dir matching service_pattern:
    Create FileIndex(service_dir)          ← isolated per-service index
    For each checklist_item:
        Run analyzer → AnalysisResult
        Save AutonomousReviewResult(service_name=service_dir.name, ...)
    Broadcast per-service progress
```

#### 2d. Report changes
New report sections:
- **Per-service summary table** — rows = services, columns = checklist areas, cell = RAG
- **Fleet compliance score** — % of services GREEN per checklist item
- **Services needing attention** — list of services below threshold

**Effort estimate:** ~3–4 days

---

### Phase 3 — Per-Service LLM Context Quality
**Goal:** LLM gets coherent context from within one service, not 3 random files from 3 services.

#### Changes
- Increase `MAX_FILES_PER_ITEM` from 3 → 8 within a single service FileIndex
- Increase `MAX_TOKENS_PER_FILE` from 2500 → 4000 chars for Java files (larger than Python)
- Add Java/Spring Boot keyword maps to `_AREA_KEYWORD_MAP` in strategy router:
  - `@RestController`, `@Service`, `@Repository`, `application.yml`, `pom.xml`
  - `@SpringBootTest`, `@WebMvcTest`, `@DataJpaTest` for test coverage detection
  - `bootstrap.yml`, `Dockerfile`, `.github/workflows/` for DevOps checks

**Effort estimate:** ~1 day

---

### Phase 4 — Microservices-Specific Checklist Rules
**Goal:** Detect patterns that only matter in distributed systems.

New strategy rules to add to `strategy_router.py`:

| Checklist Area | New Rule | Strategy | Patterns |
|---------------|----------|----------|---------|
| Inter-service auth | JWT / OAuth in service-to-service calls | pattern_scan | `@FeignClient`, `WebClient`, `RestTemplate` + auth headers |
| API contracts | OpenAPI / Swagger per service | file_presence | `openapi.yml`, `swagger.yml`, `*Api.java` |
| Distributed tracing | Trace IDs propagated | pattern_scan | `@Span`, `Tracer`, `MDC.put`, `X-B3-TraceId` |
| Health endpoints | Actuator / health check | file_presence + pattern | `/actuator/health`, `HealthIndicator` |
| Circuit breakers | Resilience4j / Hystrix | pattern_scan | `@CircuitBreaker`, `@Retry`, `resilience4j` |
| Config externalised | No hardcoded config | pattern_scan (invert) | hardcoded IPs, DB URLs in source |
| Service versioning | API versioning strategy | pattern_scan | `/v1/`, `/v2/`, `@RequestMapping("/api/v")` |
| Contract testing | Consumer-driven contracts | file_presence | `pact/`, `*.pact.json`, `@PactTest` |

**Effort estimate:** ~1 day

---

### Phase 5 — UI Enhancements
**Goal:** Show per-service results in the live progress table and report.

#### Progress view changes
- Add **service column** to results table
- Add **service filter** dropdown (alongside existing RAG filter)
- Show per-service progress bars during scan

#### Report view changes
- **Heat map table**: services × checklist areas, colour-coded RAG
- **Fleet summary**: total services, % compliant per area
- **Drill-down**: click a service row to see its item-level results

**Effort estimate:** ~2 days

---

## Summary Roadmap

| Phase | What | Effort | Unblocks |
|-------|------|--------|---------|
| ✅ Phase 1 | Docker volume mount | Done | Any local path scanning |
| Phase 2 | Multi-service job mode | 3–4 days | Per-service compliance |
| Phase 3 | LLM context quality for Java | 1 day | Accurate analysis |
| Phase 4 | Microservices-specific rules | 1 day | Distributed systems checks |
| Phase 5 | UI heat map + service filter | 2 days | Usable fleet reporting |

**Total to full microservices support: ~8–9 days**

---

## Recommended Immediate Approach

Until Phase 2 is built, the most productive path is:

1. **Run one job per service** pointing at individual service folders
2. Use path `/host-projects/hatch-pay/backend/<service-name>` in the UI
3. Select the **Technical Checklist** for code quality checks
4. Results per service are complete and accurate — the scanner was designed for this granularity
