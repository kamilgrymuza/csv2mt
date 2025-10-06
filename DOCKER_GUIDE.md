# Docker Development Guide

This project runs entirely in Docker containers. This guide explains how to work with the Dockerized environment.

## Architecture

```
┌─────────────────────────────────────────┐
│  Host Machine (macOS/Windows/Linux)    │
│  ┌─────────────────────────────────┐   │
│  │  Stripe CLI (port forwarding)   │   │
│  └─────────────────────────────────┘   │
│          ↓                              │
│  ┌─────────────────────────────────┐   │
│  │  Docker Compose Network         │   │
│  │  ┌───────────────────────────┐  │   │
│  │  │  Frontend Container       │  │   │
│  │  │  - React/Vite             │  │   │
│  │  │  - Port 3000              │  │   │
│  │  └───────────────────────────┘  │   │
│  │  ┌───────────────────────────┐  │   │
│  │  │  Backend Container        │  │   │
│  │  │  - FastAPI/Python         │  │   │
│  │  │  - Port 8000              │  │   │
│  │  └───────────────────────────┘  │   │
│  │  ┌───────────────────────────┐  │   │
│  │  │  PostgreSQL Container     │  │   │
│  │  │  - Database               │  │   │
│  │  │  - Port 5432              │  │   │
│  │  └───────────────────────────┘  │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

## Container Details

### Frontend Container
- **Base Image:** Node (from frontend/Dockerfile)
- **Port:** 3000 (mapped to host 3000)
- **Volume:** `./frontend:/app` (hot reload enabled)
- **Command:** `npm run dev -- --host 0.0.0.0 --port 3000`

### Backend Container
- **Base Image:** Python (from backend/Dockerfile)
- **Port:** 8000 (mapped to host 8000)
- **Volume:** `./backend:/app` (hot reload enabled)
- **Command:** `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`

### PostgreSQL Container
- **Base Image:** postgres:15
- **Port:** 5432 (mapped to host 5432)
- **Volume:** `postgres_data` (persistent storage)
- **Database:** micro_saas_db
- **User:** user / password

## Essential Commands

### Starting & Stopping

```bash
# Start all services in background
docker-compose up -d

# Start and view logs
docker-compose up

# Stop all services
docker-compose down

# Stop and remove volumes (deletes database)
docker-compose down -v

# Restart a specific service
docker-compose restart backend
docker-compose restart frontend
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres

# Last 100 lines
docker-compose logs --tail=100 backend

# Filter logs
docker-compose logs backend | grep -i error
docker-compose logs backend | grep -i stripe
```

### Rebuilding

```bash
# Rebuild after code changes
docker-compose up -d --build

# Rebuild specific service
docker-compose up -d --build backend

# Force rebuild (no cache)
docker-compose build --no-cache
docker-compose up -d
```

### Accessing Containers

```bash
# Backend shell
docker-compose exec backend bash

# Frontend shell
docker-compose exec frontend sh

# PostgreSQL shell
docker-compose exec postgres psql -U user -d micro_saas_db

# Run Python command
docker-compose exec backend python -c "print('Hello')"

# Run npm command
docker-compose exec frontend npm list
```

## Database Operations

### Running Migrations

```bash
# Apply migrations
docker-compose exec backend alembic upgrade head

# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "Description"

# Check current migration
docker-compose exec backend alembic current

# Migration history
docker-compose exec backend alembic history

# Downgrade one version
docker-compose exec backend alembic downgrade -1
```

### Database Access

```bash
# Access psql shell
docker-compose exec postgres psql -U user -d micro_saas_db

# Run SQL query
docker-compose exec postgres psql -U user -d micro_saas_db -c "SELECT * FROM users;"

# List tables
docker-compose exec postgres psql -U user -d micro_saas_db -c "\dt"

# Describe table
docker-compose exec postgres psql -U user -d micro_saas_db -c "\d users"

# Export database
docker-compose exec postgres pg_dump -U user micro_saas_db > backup.sql

# Import database
cat backup.sql | docker-compose exec -T postgres psql -U user -d micro_saas_db
```

## Development Workflow

### Daily Workflow

```bash
# Morning: Start everything
docker-compose up -d
stripe listen --forward-to http://localhost:8000/subscription/webhook

# Make code changes (hot reload automatic)
# Edit files in backend/ or frontend/

# View logs while developing
docker-compose logs -f backend frontend

# Evening: Stop everything
docker-compose down
# Ctrl+C to stop Stripe CLI
```

### After Pulling Changes

```bash
# Pull latest code
git pull

# Rebuild containers (new dependencies)
docker-compose up -d --build

# Run new migrations
docker-compose exec backend alembic upgrade head

# Verify
docker-compose ps
```

### Installing New Dependencies

**Backend (Python):**

```bash
# Add package to backend/requirements.txt
echo "new-package==1.0.0" >> backend/requirements.txt

# Rebuild backend container
docker-compose up -d --build backend

# Or install without rebuild (temporary)
docker-compose exec backend pip install new-package
```

**Frontend (Node):**

```bash
# Add package to frontend/package.json or use npm
docker-compose exec frontend npm install new-package

# OR rebuild container
docker-compose up -d --build frontend
```

## Environment Variables

### Location Priority

1. **Root `.env`** - Used by docker-compose.yml
2. **Backend `backend/.env`** - Used by backend container
3. **Frontend `frontend/.env`** - Used by frontend container

### Important Notes

**Database URL in backend/.env must use Docker service name:**
```bash
# ✅ Correct (Docker)
DATABASE_URL=postgresql://user:password@postgres:5432/micro_saas_db

# ❌ Wrong
DATABASE_URL=postgresql://user:password@localhost:5432/micro_saas_db
```

**Frontend API URL must use localhost:**
```bash
# ✅ Correct (accessed from browser)
VITE_API_URL=http://localhost:8000

# ❌ Wrong
VITE_API_URL=http://backend:8000
```

## Troubleshooting

### Containers Won't Start

```bash
# Check status
docker-compose ps

# Check logs for errors
docker-compose logs

# Check for port conflicts
lsof -i :3000  # Frontend
lsof -i :8000  # Backend
lsof -i :5432  # Postgres

# Nuclear option: restart from scratch
docker-compose down -v
docker-compose up -d --build
docker-compose exec backend alembic upgrade head
```

### Database Connection Issues

```bash
# Check postgres is running
docker-compose ps postgres

# Check postgres health
docker-compose exec postgres pg_isready -U user

# Test connection from backend
docker-compose exec backend python -c "
from app.database import engine
print(engine.connect())
"

# Verify DATABASE_URL
docker-compose exec backend python -c "
from app.config import settings
print(settings.database_url)
"
```

### Module Not Found

```bash
# Backend missing dependencies
docker-compose exec backend pip list
docker-compose up -d --build backend

# Frontend missing dependencies
docker-compose exec frontend npm list
docker-compose up -d --build frontend
```

### Hot Reload Not Working

```bash
# Check volumes are mounted
docker-compose config | grep volumes -A 5

# Restart with rebuild
docker-compose down
docker-compose up -d --build

# Check file permissions (macOS/Linux)
ls -la backend/
ls -la frontend/
```

### Stripe Webhooks Not Received

```bash
# Verify Stripe CLI is running
stripe listen --forward-to http://localhost:8000/subscription/webhook

# Check backend is accessible
curl http://localhost:8000/health

# Check backend logs
docker-compose logs backend | grep -i webhook

# Manually trigger test
stripe trigger customer.subscription.created
```

### Database Data Persistence

```bash
# Check volume exists
docker volume ls | grep postgres

# Inspect volume
docker volume inspect csv2mt_postgres_data

# Backup volume
docker run --rm \
  -v csv2mt_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/postgres_backup.tar.gz /data

# Restore volume
docker run --rm \
  -v csv2mt_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/postgres_backup.tar.gz -C /
```

## Performance Tips

### Speed Up Builds

```bash
# Use BuildKit (faster builds)
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

docker-compose build

# Add to ~/.bashrc or ~/.zshrc for permanent
```

### Reduce Volume Overhead

On macOS, consider:
```yaml
# In docker-compose.yml, use delegated mode
volumes:
  - ./backend:/app:delegated
  - ./frontend:/app:delegated
```

### Clean Up

```bash
# Remove unused containers/images
docker system prune

# Remove all stopped containers
docker container prune

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Free up space
docker system df  # Check usage
docker system prune -a --volumes  # Clean everything (CAUTION)
```

## Production Considerations

### Building for Production

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# No volume mounts in production
# Use built images with code baked in
```

### Example docker-compose.prod.yml

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
      # No volume mount
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=${VITE_API_URL}
    # Use nginx to serve built files
```

## Quick Reference

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Logs
docker-compose logs -f backend

# Rebuild
docker-compose up -d --build

# Shell
docker-compose exec backend bash

# Database
docker-compose exec postgres psql -U user -d micro_saas_db

# Migration
docker-compose exec backend alembic upgrade head

# Clean restart
docker-compose down -v && docker-compose up -d --build
```

## Common Tasks

### Reset Database

```bash
docker-compose down -v
docker-compose up -d
docker-compose exec backend alembic upgrade head
```

### View Real-Time Logs

```bash
# Split terminal or use tmux
docker-compose logs -f backend &
docker-compose logs -f frontend &
stripe listen --forward-to http://localhost:8000/subscription/webhook
```

### Debug Backend Issue

```bash
# Check backend is running
docker-compose ps backend

# View logs
docker-compose logs backend | less

# Access shell
docker-compose exec backend bash

# Test imports
docker-compose exec backend python -c "from app import main"

# Check database connection
docker-compose exec backend python -c "from app.database import engine; print(engine)"
```

### Test Database Connection

```bash
# From backend container
docker-compose exec backend python -c "
from sqlalchemy import create_engine
from app.config import settings
engine = create_engine(settings.database_url)
with engine.connect() as conn:
    result = conn.execute('SELECT 1')
    print('Database connection successful!')
"
```

## Resources

- Docker Compose Docs: https://docs.docker.com/compose/
- Docker Best Practices: https://docs.docker.com/develop/dev-best-practices/
- Compose File Reference: https://docs.docker.com/compose/compose-file/
