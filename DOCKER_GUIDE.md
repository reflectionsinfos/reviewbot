# Docker Deployment Guide

## 📋 Overview

This guide covers Docker deployment for the AI Tech & Delivery Review Agent.

---

## 🚀 Quick Start

### **1. Clone and Configure**

```bash
cd c:\projects\project-reviews

# Copy environment template
copy .env.docker .env

# Edit .env and add your API keys
notepad .env
```

### **2. Start with Docker Compose**

```bash
# Development (with hot reload)
docker-compose --profile tools up --build

# Production
docker-compose --profile production up -d --build
```

### **3. Verify**

```bash
# Check status
docker-compose ps

# View logs
docker-compose logs -f app

# Test health endpoint
curl http://localhost:8000/health
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Network                        │
│                                                         │
│  ┌─────────────┐     ┌─────────────┐                   │
│  │   Nginx     │────▶│    App      │                   │
│  │   (Proxy)   │     │  (FastAPI)  │                   │
│  │  :80, :443  │     │    :8000    │                   │
│  └─────────────┘     └──────┬──────┘                   │
│                             │                           │
│                      ┌──────▼──────┐                   │
│                      │  PostgreSQL │                   │
│                      │    :5432    │                   │
│                      └─────────────┘                   │
│                                                         │
│  ┌─────────────┐     (Optional)                        │
│  │   pgAdmin   │                                       │
│  │    :5050    │                                       │
│  └─────────────┘                                       │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 Docker Compose Profiles

### **Development**
```bash
docker-compose up --build
```
- App with hot reload
- PostgreSQL database
- pgAdmin (optional)

### **Production**
```bash
docker-compose --profile production up -d --build
```
- App (optimized)
- PostgreSQL database
- Nginx reverse proxy
- SSL termination

### **With Tools**
```bash
docker-compose --profile tools up --build
```
- Includes pgAdmin for database management

---

## 🔧 Configuration

### **Environment Variables**

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_PORT` | App port | 8000 |
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `SECRET_KEY` | JWT signing key | Change me! |
| `DATABASE_URL` | Database connection | PostgreSQL |
| `POSTGRES_USER` | DB username | review_user |
| `POSTGRES_PASSWORD` | DB password | Change me! |
| `PGADMIN_EMAIL` | pgAdmin email | admin@example.com |
| `PGADMIN_PASSWORD` | pgAdmin password | Change me! |
| `BUILD_TARGET` | production/development | production |

---

## 🎯 Common Commands

### **Start Services**
```bash
# Development
docker-compose up --build

# Production (detached)
docker-compose --profile production up -d --build

# Specific service only
docker-compose up db
```

### **Stop Services**
```bash
# Stop all
docker-compose down

# Stop and remove volumes (WARNING: deletes data!)
docker-compose down -v
```

### **View Logs**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app
docker-compose logs -f db
```

### **Execute Commands**
```bash
# Run migrations
docker-compose exec app python -c "from app.db.session import init_db; import asyncio; asyncio.run(init_db())"

# Open shell
docker-compose exec app bash

# Run tests
docker-compose exec app pytest tests/ -v
```

### **Database Access**
```bash
# Connect to PostgreSQL
docker-compose exec db psql -U review_user -d reviews_db

# Export database
docker-compose exec db pg_dump -U review_user reviews_db > backup.sql

# Import database
docker-compose exec -T db psql -U review_user reviews_db < backup.sql
```

---

## 🔐 Security

### **Production Checklist**

1. **Change all passwords:**
   ```bash
   # In .env
   POSTGRES_PASSWORD=secure-random-password
   SECRET_KEY=secure-random-secret-key
   PGADMIN_PASSWORD=secure-random-password
   ```

2. **Enable HTTPS:**
   - Get SSL certificates (Let's Encrypt)
   - Uncomment HTTPS server in `nginx/nginx.conf`
   - Mount certificates in docker-compose.yml

3. **Restrict database access:**
   ```yaml
   # In docker-compose.yml, remove or restrict:
   ports:
     - "5432:5432"  # Remove for production
   ```

4. **Use secrets management:**
   ```yaml
   # docker-compose.yml
   secrets:
     - openai_key
     - db_password
   
   services:
     app:
       secrets:
         - openai_key
   ```

---

## 📊 Monitoring

### **Health Checks**

```bash
# Check service health
docker-compose ps

# Health endpoint
curl http://localhost:8000/health

# Database health
docker-compose exec db pg_isready
```

### **Resource Usage**

```bash
# View resource usage
docker stats

# Container inspect
docker inspect ai-review-agent
```

---

## 🔄 Updates

### **Update Application**

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose up -d --build --force-recreate app

# View logs
docker-compose logs -f app
```

### **Database Migrations**

```bash
# Run Alembic migrations (if using)
docker-compose exec app alembic upgrade head

# Or initialize via Python
docker-compose exec app python -c "from app.db.session import init_db; import asyncio; asyncio.run(init_db())"
```

---

## 🐛 Troubleshooting

### **App Won't Start**

```bash
# Check logs
docker-compose logs app

# Common issues:
# 1. Database not ready - wait for db health check
# 2. Missing .env variables - check .env file
# 3. Port conflicts - change APP_PORT in .env
```

### **Database Connection Failed**

```bash
# Check database is running
docker-compose ps db

# Test connection
docker-compose exec app python -c "from app.db.session import engine; print(engine)"

# Reset database (WARNING: deletes data!)
docker-compose down -v
docker-compose up -d db
```

### **Port Already in Use**

```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process or change port in .env
APP_PORT=8001
```

---

## 📦 Backup & Restore

### **Backup Database**

```bash
# PostgreSQL backup
docker-compose exec db pg_dump -U review_user reviews_db > backup_$(date +%Y%m%d).sql

# Backup volumes
docker run --rm \
  -v ai-review-agent_postgres_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/postgres_data.tar.gz /data
```

### **Restore Database**

```bash
# Restore from SQL dump
docker-compose exec -T db psql -U review_user reviews_db < backup_20260327.sql

# Restore from volume backup
docker run --rm \
  -v ai-review-agent_postgres_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/postgres_data.tar.gz -C /
```

---

## 🚀 Production Deployment

### **1. Prepare Server**

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
pip install docker-compose
```

### **2. Deploy**

```bash
# Clone repository
git clone <your-repo>
cd project-reviews

# Configure environment
cp .env.docker .env
nano .env  # Edit with production values

# Start services
docker-compose --profile production up -d --build

# Verify
docker-compose ps
curl http://localhost/health
```

### **3. SSL with Let's Encrypt**

```bash
# Install Certbot
apt install certbot python3-certbot-nginx

# Get certificates
certbot --nginx -d your-domain.com

# Certificates auto-mounted to nginx/ssl
```

---

## 📈 Performance Tuning

### **App Workers**

```bash
# In docker-compose.yml, modify CMD:
command: >
  uvicorn main:app
  --host 0.0.0.0
  --port 8000
  --workers 4
  --worker-class uvicorn.workers.UvicornWorker
```

### **Database Connection Pool**

```python
# In app/db/session.py
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)
```

---

## 🎯 Next Steps

1. ✅ Configure `.env` with your settings
2. ✅ Run `docker-compose up --build`
3. ✅ Access http://localhost:8000/docs
4. ✅ Create global templates
5. ✅ Start reviewing projects!

---

*For more information, see QWEN.md and PRODUCTION_READINESS.md*
