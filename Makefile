# ============================================
# AI Review Agent - Docker Makefile
# ============================================

.PHONY: help build up down logs shell test prod clean

# Default target
help:
	@echo "AI Tech & Delivery Review Agent - Docker Commands"
	@echo ""
	@echo "Development:"
	@echo "  make build        - Build Docker images"
	@echo "  make up           - Start all services (development)"
	@echo "  make down         - Stop all services"
	@echo "  make logs         - View logs"
	@echo "  make shell        - Open shell in app container"
	@echo "  make db-shell     - Open PostgreSQL shell"
	@echo ""
	@echo "Production:"
	@echo "  make prod         - Start in production mode"
	@echo "  make prod-build   - Build and start production"
	@echo ""
	@echo "Testing:"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linters"
	@echo ""
	@echo "Database:"
	@echo "  make db-backup    - Backup database"
	@echo "  make db-restore   - Restore database"
	@echo "  make db-init      - Initialize database"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean        - Remove containers and volumes"
	@echo "  make prune        - Remove all unused Docker resources"

# Build images
build:
	docker-compose build

# Start development
up:
	docker-compose --profile tools up --build

# Start production
prod:
	docker-compose --profile production up -d

prod-build:
	docker-compose --profile production up --build -d

# Stop services
down:
	docker-compose down

# View logs
logs:
	docker-compose logs -f

logs-app:
	docker-compose logs -f app

logs-db:
	docker-compose logs -f db

# Open shell in app container
shell:
	docker-compose exec app bash

# Open PostgreSQL shell
db-shell:
	docker-compose exec db psql -U review_user -d reviews_db

# Run tests
test:
	docker-compose exec app pytest tests/ -v --tb=short

test-cov:
	docker-compose exec app pytest tests/ -v --cov=app --cov-report=html

# Run linters
lint:
	docker-compose exec app black app/ --check
	docker-compose exec app isort app/ --check-only
	docker-compose exec app flake8 app/

# Initialize database
db-init:
	docker-compose exec app python -c "from app.db.session import init_db; import asyncio; asyncio.run(init_db())"

# Create templates
create-templates:
	docker-compose exec app python scripts/create_templates.py

# Backup database
db-backup:
	@echo "Backing up database..."
	docker-compose exec db pg_dump -U review_user reviews_db > backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Backup created!"

# Restore database (provide filename)
db-restore:
	@echo "Restoring database from $(FILE)..."
	docker-compose exec -T db psql -U review_user reviews_db < $(FILE)
	@echo "Database restored!"

# Clean up containers and volumes
clean:
	docker-compose down -v
	docker-compose rm -f

# Prune all unused Docker resources
prune:
	docker system prune -a --volumes

# Health check
health:
	@echo "Checking service health..."
	docker-compose ps
	@echo ""
	@echo "Testing endpoints..."
	@echo "Health: $$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health)"
	@echo "API Docs: $$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/docs)"

# View resource usage
stats:
	docker stats

# Restart services
restart:
	docker-compose restart

# Scale app workers (production only)
scale:
	docker-compose up -d --scale app=$(WORKERS)

# Show environment
env:
	docker-compose config

# Validate docker-compose
validate:
	docker-compose config --quiet
	@echo "✓ docker-compose.yml is valid"
