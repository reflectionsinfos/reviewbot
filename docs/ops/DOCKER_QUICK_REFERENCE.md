# Docker Quick Reference

## 🚀 One-Liner Commands

### Start Development
```bash
docker-compose up --build
```

### Start Production
```bash
docker-compose --profile production up -d --build
```

### Stop Everything
```bash
docker-compose down
```

---

## 📋 Common Scenarios

### First Time Setup
```bash
copy .env.docker .env
notepad .env  # Add OPENAI_API_KEY
docker-compose up --build
```

### View Logs
```bash
# All services
docker-compose logs -f

# App only
docker-compose logs -f app

# Last 100 lines
docker-compose logs --tail=100 app
```

### Open Shell
```bash
# In app container
docker-compose exec app bash

# In database container
docker-compose exec db bash
```

### Run Commands
```bash
# Initialize database
docker-compose exec app python -c "from app.db.session import init_db; import asyncio; asyncio.run(init_db())"

# Create templates
docker-compose exec app python scripts/create_templates.py

# Run tests
docker-compose exec app pytest tests/ -v
```

### Database Operations
```bash
# Connect to PostgreSQL
docker-compose exec db psql -U review_user -d reviews_db

# Backup
docker-compose exec db pg_dump -U review_user reviews_db > backup.sql

# Restore
docker-compose exec -T db psql -U review_user reviews_db < backup.sql
```

### Cleanup
```bash
# Stop and remove containers
docker-compose down

# Stop and remove volumes (WARNING: deletes data!)
docker-compose down -v

# Remove all unused Docker resources
docker system prune -a --volumes
```

---

## 🔧 Troubleshooting

### App Won't Start
```bash
# Check logs
docker-compose logs app

# Restart app
docker-compose restart app

# Rebuild
docker-compose up -d --build --force-recreate app
```

### Database Issues
```bash
# Check database status
docker-compose ps db

# Restart database
docker-compose restart db

# Reset (WARNING: deletes data!)
docker-compose down -v
docker-compose up -d db
```

### Port Conflicts
```bash
# Find what's using port 8000
netstat -ano | findstr :8000

# Change port in .env
APP_PORT=8001
```

### Permission Errors
```bash
# Fix ownership (Linux/Mac)
sudo chown -R $USER:$USER .

# Fix permissions
chmod -R 755 uploads reports data
```

---

## 📊 Monitoring

### Service Status
```bash
docker-compose ps
```

### Resource Usage
```bash
docker stats
```

### Health Check
```bash
curl http://localhost:8000/health
```

### Container Inspect
```bash
docker inspect ai-review-agent
```

---

## 🎯 Production Deployment

### 1. Configure Environment
```bash
# Generate secure keys
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Edit .env with production values
nano .env
```

### 2. Deploy
```bash
docker-compose --profile production up -d --build
```

### 3. Verify
```bash
docker-compose ps
curl http://localhost/health
```

### 4. Monitor
```bash
docker-compose logs -f
docker stats
```

---

## 📦 Volume Management

### List Volumes
```bash
docker volume ls
```

### Inspect Volume
```bash
docker volume inspect ai-review-agent_postgres_data
```

### Backup Volume
```bash
docker run --rm \
  -v ai-review-agent_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/db_backup.tar.gz /data
```

### Restore Volume
```bash
docker run --rm \
  -v ai-review-agent_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/db_backup.tar.gz -C /
```

---

## 🔐 Security Checklist

- [ ] Change `POSTGRES_PASSWORD` in .env
- [ ] Change `SECRET_KEY` in .env
- [ ] Change `PGADMIN_PASSWORD` in .env
- [ ] Add `OPENAI_API_KEY` in .env
- [ ] Remove database port exposure (production)
- [ ] Enable HTTPS (production)
- [ ] Use secrets management (production)

---

## 📈 Performance Tips

### Scale Workers
```bash
# In production, scale app workers
docker-compose up -d --scale app=4
```

### Resource Limits
```yaml
# In docker-compose.yml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

### Connection Pooling
```python
# In app/db/session.py
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40
)
```

---

## 🎓 Learning Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [PostgreSQL Docker Hub](https://hub.docker.com/_/postgres)
- [Nginx Docker Hub](https://hub.docker.com/_/nginx)

---

*For complete documentation, see DOCKER_GUIDE.md*
