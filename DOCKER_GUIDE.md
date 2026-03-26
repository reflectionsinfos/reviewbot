# ReviewBot v2.0 - Docker Development Guide

> Complete Docker setup for Phase 1 implementation

**Version:** 2.0  
**Last Updated:** March 27, 2026  
**Status:** Ready for Phase 1  
**Owner:** DevOps Team

---

## 🚀 Quick Start for Phase 1

### **Step 1: Setup Environment**

```bash
# Navigate to project
cd c:\projects\reviewbot

# Copy environment template
copy .env.docker .env

# Edit .env with your configuration
notepad .env
```

### **Step 2: Add Required Environment Variables**

Minimum required for Phase 1:

```env
# Application
APP_NAME="ReviewBot v2.0"
DEBUG=true
ENVIRONMENT=development

# Database (PostgreSQL)
DATABASE_URL="postgresql+asyncpg://review_user:review_password_change_me@localhost:5432/reviews_db"
POSTGRES_USER=review_user
POSTGRES_PASSWORD=review_password_change_me
POSTGRES_DB=reviews_db

# API Keys
OPENAI_API_KEY="sk-your-actual-api-key-here"

# Security (CHANGE IN PRODUCTION!)
SECRET_KEY="your-super-secret-key-change-this"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis (for Celery caching)
REDIS_URL="redis://localhost:6379/0"
```

### **Step 3: Start Development Environment**

```bash
# Development mode (with hot reload and tools)
docker-compose --profile tools up --build

# Or in background
docker-compose --profile tools up -d --build
```

### **Step 4: Verify Setup**

```bash
# Check all services are running
docker-compose ps

# View application logs
docker-compose logs -f app

# Test health endpoint
curl http://localhost:8000/health

# Access pgAdmin (database management)
# Open browser: http://localhost:5050
# Login: admin@example.com / admin_change_me
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              ReviewBot v2.0 - Docker Architecture           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐                                           │
│  │   Browser   │                                           │
│  └──────┬──────┘                                           │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Docker Network                         │   │
│  │                                                     │   │
│  │  ┌──────────┐     ┌──────────┐     ┌──────────┐   │   │
│  │  │   App    │────▶│PostgreSQL│     │  Redis   │   │   │
│  │  │ FastAPI  │     │    DB    │     │  Cache   │   │   │
│  │  │  :8000   │     │  :5432   │     │  :6379   │   │   │
│  │  └──────────┘     └──────────┘     └──────────┘   │   │
│  │       │                  │                         │   │
│  │       ▼                  ▼                         │   │
│  │  ┌──────────┐     ┌──────────┐                    │   │
│  │  │ pgAdmin  │     │  Volume  │                    │   │
│  │  │  :5050   │     │ Storage  │                    │   │
│  │  └──────────┘     └──────────┘                    │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Docker Compose Services

### **1. Application Service (app)**

```yaml
app:
  build: .
  ports:
    - "8000:8000"
  environment:
    - DATABASE_URL=postgresql+asyncpg://review_user:review_password@db:5432/reviews_db
    - REDIS_URL=redis://redis:6379/0
    - OPENAI_API_KEY=${OPENAI_API_KEY}
  volumes:
    - .:/app:cached  # Hot reload for development
    - app_data:/app/data
  depends_on:
    - db
    - redis
```

**Features:**
- ✅ Hot reload (code changes auto-restart)
- ✅ Port 8000 exposed
- ✅ Depends on PostgreSQL and Redis
- ✅ Health checks enabled

---

### **2. PostgreSQL Database (db)**

```yaml
db:
  image: postgres:15-alpine
  ports:
    - "5432:5432"
  environment:
    - POSTGRES_USER=review_user
    - POSTGRES_PASSWORD=review_password_change_me
    - POSTGRES_DB=reviews_db
  volumes:
    - postgres_data:/var/lib/postgresql/data
    - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
```

**Features:**
- ✅ PostgreSQL 15 Alpine (lightweight)
- ✅ Persistent data volume
- ✅ Port 5432 exposed (local access)
- ✅ Auto-run init script

---

### **3. Redis Cache (redis)** - NEW for v2.0

```yaml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
  command: redis-server --appendonly yes
```

**Features:**
- ✅ Redis 7 Alpine
- ✅ AOF persistence enabled
- ✅ Used by Celery for task queue
- ✅ Response caching

---

### **4. pgAdmin (tools profile)**

```yaml
pgadmin:
  image: dpage/pgadmin4:latest
  ports:
    - "5050:80"
  environment:
    - PGADMIN_DEFAULT_EMAIL=admin@example.com
    - PGADMIN_DEFAULT_PASSWORD=admin_change_me
  profiles:
    - tools
```

**Access:**
- URL: http://localhost:5050
- Email: admin@example.com
- Password: admin_change_me

---

## 🔧 Common Commands

### **Start Services**

```bash
# Development (with tools)
docker-compose --profile tools up --build

# Development (background)
docker-compose --profile tools up -d --build

# Production
docker-compose --profile production up -d --build

# Only app service
docker-compose up app

# Rebuild and restart
docker-compose up --build --force-recreate
```

---

### **Stop Services**

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data!)
docker-compose down -v

# Stop specific service
docker-compose stop app
```

---

### **View Logs**

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app
docker-compose logs -f db
docker-compose logs -f redis

# Last 100 lines
docker-compose logs --tail=100 app
```

---

### **Execute Commands**

```bash
# Open shell in app container
docker-compose exec app bash

# Run Python commands
docker-compose exec app python -c "print('Hello')"

# Run database migrations
docker-compose exec app alembic upgrade head

# Run tests
docker-compose exec app pytest tests/ -v

# Check database connection
docker-compose exec app python -c "from app.db.session import AsyncSessionLocal; print('DB Connected!')"
```

---

### **Database Management**

```bash
# Connect to PostgreSQL
docker-compose exec db psql -U review_user -d reviews_db

# Backup database
docker-compose exec db pg_dump -U review_user reviews_db > backup.sql

# Restore database
docker-compose exec -T db psql -U review_user -d reviews_db < backup.sql

# Reset database (WARNING: deletes all data!)
docker-compose exec db psql -U review_user -d reviews_db -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
```

---

## 🗄️ Database Migration (Week 1 Task)

### **Task 1.1.2: Create Migration 001**

```bash
# Open shell in app container
docker-compose exec app bash

# Generate migration
alembic revision --autogenerate -m "Initial v2.0 schema - 21 tables"

# Review migration script
# File created in: alembic/versions/001_initial_v2_schema.py

# Apply migration
alembic upgrade head

# Verify tables created
docker-compose exec db psql -U review_user -d reviews_db -c "\dt"
```

**Expected Output:**
```
                     List of relations
 Schema |            Name             | Type  |  Owner   
--------+-----------------------------+-------+----------
 public | users                       | table | review_user
 public | projects                    | table | review_user
 public | project_members             | table | review_user
 public | checklists                  | table | review_user
 public | checklist_items             | table | review_user
 public | review_sessions             | table | review_user
 public | recurring_review_schedules  | table | review_user
 public | milestone_review_triggers   | table | review_user
 public | review_instances            | table | review_user
 public | self_review_sessions        | table | review_user
 public | autonomous_review_results   | table | review_user
 public | human_review_results        | table | review_user
 public | override_requests           | table | review_user
 public | override_approvals          | table | review_user
 public | final_review_results        | table | review_user
 public | consolidated_self_review_reports | table | review_user
 public | reminder_queue              | table | review_user
 public | meeting_blocks              | table | review_user
 public | stakeholder_preparation     | table | review_user
 public | review_trend_analytics      | table | review_user
 public | gap_tracking                | table | review_user
(21 rows)
```

---

## 🔍 Troubleshooting

### **Issue: Port Already in Use**

```bash
# Check what's using the port
netstat -ano | findstr :8000
netstat -ano | findstr :5432

# Stop conflicting service or change port in .env
APP_PORT=8001
DB_PORT=5433
```

---

### **Issue: Database Connection Failed**

```bash
# Check database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Test connection from app
docker-compose exec app python -c "
from app.db.session import AsyncSessionLocal
import asyncio
async def test():
    async with AsyncSessionLocal() as session:
        result = await session.execute('SELECT 1')
        print('Connection successful!')
asyncio.run(test())
"
```

---

### **Issue: Migration Failed**

```bash
# Check current migration version
docker-compose exec app alembic current

# Rollback one migration
docker-compose exec app alembic downgrade -1

# Rollback to specific version
docker-compose exec app alembic downgrade <revision_id>

# Wipe and recreate (development only!)
docker-compose down -v
docker-compose up -d db
docker-compose exec app alembic upgrade head
```

---

## 📊 Phase 1 Docker Tasks

### Week 1 Docker-Related Tasks

- [ ] **1.1.1** Setup PostgreSQL development database
  ```bash
  docker-compose up -d db
  docker-compose logs db  # Verify started
  ```

- [ ] **1.1.2** Create Migration 001 script
  ```bash
  docker-compose exec app alembic revision --autogenerate -m "Initial v2.0 schema"
  ```

- [ ] **1.1.3** Test migration on dev database
  ```bash
  docker-compose exec app alembic upgrade head
  docker-compose exec db psql -U review_user -d reviews_db -c "\dt"
  ```

- [ ] **1.2.1** Setup Docker development environment
  ```bash
  docker-compose --profile tools up --build
  docker-compose ps  # Verify all services running
  ```

- [ ] **1.2.3** Setup Redis for caching
  ```bash
  docker-compose up -d redis
  docker-compose exec redis redis-cli ping  # Should return PONG
  ```

---

## 🔗 Related Documents

- [ROAD_MAP.md](ROAD_MAP.md) - Phase 1 implementation plan
- [DATABASE_SCHEMA_V2.md](DATABASE_SCHEMA_V2.md) - Database schema
- [DESIGN_PHASE_KICKOFF.md](DESIGN_PHASE_KICKOFF.md) - Implementation kickoff

---

*Document Owner: DevOps Team*  
*Last Updated: March 27, 2026*  
*Next Update: After Phase 1 Week 1 completion*
