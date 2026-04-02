# Sample Projects for Hybrid LLM Testing

**Purpose:** Small, realistic codebases to validate ReviewBot reviews complete quickly
on a local Ollama instance during development.

**Location:** `C:\projects\nexus-ai\sample-projects\`

---

## Why Small Projects?

A full review with 103 checklist items on a large codebase (500+ files) at Ollama
CPU speeds (~3-5 tok/sec) would take 2-3 hours per run. These sample projects have:

- 5-8 source files each
- Clear architecture patterns (easy for the checklist to find evidence)
- Intentional gaps (missing tests, no CI, no auth) to generate amber/red items
- Clean naming so `file_presence` and `pattern_scan` strategies work well

---

## Projects

### 1. python-api-sample
**Stack:** Python 3.11, FastAPI, SQLAlchemy  
**Path:** `C:\projects\nexus-ai\sample-projects\python-api-sample\`  
**Files:** 7 files

```
python-api-sample/
├── main.py               # FastAPI app entry point
├── models.py             # SQLAlchemy User model
├── routes/
│   └── users.py          # CRUD endpoints
├── database.py           # DB session setup
├── requirements.txt
└── README.md
```

**Intentional gaps for review:**
- No tests directory
- No Dockerfile
- Passwords stored as plain text in model (security gap → red)
- No input validation on email field

---

### 2. java-service-sample
**Stack:** Java 17, Spring Boot 3, Maven  
**Path:** `C:\projects\nexus-ai\sample-projects\java-service-sample\`  
**Files:** 7 files

```
java-service-sample/
├── pom.xml
├── src/main/java/com/sample/
│   ├── Application.java          # Spring Boot main
│   ├── controller/
│   │   └── ProductController.java
│   ├── service/
│   │   └── ProductService.java
│   └── model/
│       └── Product.java
└── README.md
```

**Intentional gaps for review:**
- No unit tests (`src/test/` is empty)
- No exception handling in controller
- No API versioning
- No logging configuration

---

### 3. nodejs-service-sample
**Stack:** Node.js 20, Express, JavaScript  
**Path:** `C:\projects\nexus-ai\sample-projects\nodejs-service-sample\`  
**Files:** 6 files

```
nodejs-service-sample/
├── package.json
├── server.js             # Express app + routes inline
├── middleware/
│   └── auth.js           # JWT validation stub
├── services/
│   └── orderService.js   # Business logic
├── .env.example
└── README.md
```

**Intentional gaps for review:**
- No error handling middleware
- JWT secret hardcoded as string literal (security → red)
- No input sanitization
- No package-lock.json

---

## How to Use for Testing

1. Start a ReviewBot review via the UI
2. Set **Source Path** to one of:
   - `C:\projects\nexus-ai\sample-projects\python-api-sample`
   - `C:\projects\nexus-ai\sample-projects\java-service-sample`
   - `C:\projects\nexus-ai\sample-projects\nodejs-service-sample`
3. Select the **Standard Technical Checklist**
4. The review will complete in 5-15 minutes on Ollama CPU

## Expected Review Outcomes (approximate)

| Project | Green | Amber | Red | Human | Score |
|---|---|---|---|---|---|
| python-api-sample | 30-40 | 20-30 | 5-10 | 30-40 | 35-50% |
| java-service-sample | 25-35 | 25-35 | 5-10 | 30-40 | 30-45% |
| nodejs-service-sample | 20-30 | 25-35 | 8-12 | 35-45 | 25-40% |

Scores are intentionally low due to the gaps — useful for testing override, action plan,
and report generation features alongside the hybrid LLM routing.
