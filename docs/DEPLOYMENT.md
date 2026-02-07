# Production Deployment Guide

This guide covers deploying thWelly's AI Toolbox in a production environment using Docker containers across multiple hosts.

> **Note:** This documentation uses anonymized placeholder values. All IP addresses (e.g., `192.168.1.10`, `192.168.1.20`), container registry paths (`ghcr.io/<your-username>/`), and credentials are examples only. Replace them with your actual infrastructure values before deployment.

---

## Table of Contents

1. [Overview](#overview)
2. [Building Docker Images](#building-docker-images)
3. [Prerequisites](#prerequisites)
4. [Network Architecture](#network-architecture)
5. [Service Stacks](#service-stacks)
6. [Docker Compose Configurations](#docker-compose-configurations)
7. [Nginx Configuration](#nginx-configuration)
8. [Environment Variables](#environment-variables)
9. [Deployment Checklist](#deployment-checklist)
10. [Health Checks](#health-checks)
11. [Backup & Recovery](#backup--recovery)

---

## Overview

The production deployment consists of three service stacks distributed across two servers:

```
                         ┌─────────────────────────────────┐
                         │         NAS Server              │
                         │      (192.168.1.20)             │
                         ├─────────────────────────────────┤
                         │  PostgreSQL (5432)              │
                         │  MinIO S3 (9000/9001)           │
                         └───────────────┬─────────────────┘
                                         │
                                    LAN Network
                                         │
┌────────────────────────────────────────┴────────────────────────────────────┐
│                        Application Server (192.168.1.10)                     │
├──────────────────────────────────────────────────────────────────────────────┤
│  Docker Network: thwelly-net                                                 │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ Backend Stack                                                         │   │
│  │ - Redis (cache & broker)                                             │   │
│  │ - Celery Worker (async tasks)                                        │   │
│  │ - aiproxysrv (FastAPI on :5050)                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    ↑                                         │
│                                    │                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ Proxy Stack                                                           │   │
│  │ - Nginx (HTTPS :443, HTTP :80)                                       │   │
│  │ - Angular SPA (static files)                                         │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Service Stacks:**

| Stack | Location | Services |
|-------|----------|----------|
| **NAS Stack** | NAS Server | PostgreSQL, MinIO (S3) |
| **Backend Stack** | App Server | Redis, Celery, FastAPI |
| **Proxy Stack** | App Server | Nginx, Angular SPA |

---

## Building Docker Images

Before deploying, you need Docker images for the application components. There are two options:

### Option 1: GitHub Actions CI/CD (Recommended)

If you fork this repository, the included GitHub Actions workflow automatically builds and publishes images to GitHub Container Registry (GHCR) when you push a version tag:

```bash
# Create a release tag
git tag v1.0.0
git push origin v1.0.0

# Images will be available at:
# ghcr.io/<your-username>/aiproxysrv-app:v1.0.0
# ghcr.io/<your-username>/celery-worker-app:v1.0.0
# ghcr.io/<your-username>/aiwebui-app:v1.0.0
```

See [docs/CI_CD.md](CI_CD.md) for details on the build pipeline.

### Option 2: Build Locally

Build images directly on your deployment server:

```bash
# Backend (FastAPI + Celery)
cd aiproxysrv
docker build -t aiproxysrv-app:latest .
docker build -t celery-worker-app:latest .  # Same image, different entrypoint

# Frontend (Angular)
cd aiwebui
docker build -t aiwebui-app:latest .
```

When building locally, update the `docker-compose.yml` files to use local image names instead of GHCR paths.

---

## Prerequisites

### Hardware Requirements

| Server | Role | Minimum Specs |
|--------|------|---------------|
| **NAS Server** | Database & Storage | 4GB RAM, 100GB+ SSD |
| **App Server** | Application Runtime | 8GB RAM, 50GB SSD, GPU optional (for Ollama) |

### Software Requirements

- Docker Engine 24.0+
- Docker Compose v2.20+
- SSL/TLS certificates (Let's Encrypt or self-signed)
- (Optional) Ollama for local LLM inference

### Network Requirements

- Static IP addresses for both servers
- Ports open: 80, 443 (App Server), 5432, 9000 (NAS - internal only)
- DNS record pointing to App Server (or use IP directly)

---

## Network Architecture

### Docker Network

Create a shared Docker network on the Application Server:

```bash
docker network create thwelly-net
```

All backend services connect to this network for inter-container communication.

### Service Communication

```
┌─────────────────────────────────────────────────────────────────┐
│ App Server (Docker: thwelly-net)                                │
│                                                                 │
│   Nginx ─────► aiproxysrv ─────► Redis                         │
│    :443         :5050              :6379                        │
│                   │                  │                          │
│                   │                  ▼                          │
│                   │              Celery Worker                  │
│                   │                                             │
└───────────────────┼─────────────────────────────────────────────┘
                    │
                    ▼ (TCP over LAN)
┌─────────────────────────────────────────────────────────────────┐
│ NAS Server                                                      │
│                                                                 │
│   PostgreSQL ◄──────────────────── MinIO S3                    │
│     :5432                            :9000                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Service Stacks

### Stack 1: NAS Stack (Database & Storage)

Located on the NAS server, provides persistent data services.

**Services:**
- **PostgreSQL 17** - Primary database
- **MinIO** - S3-compatible object storage for media files

**Purpose:**
- Database persistence for all application data
- File storage for music files, cover art, and project assets

### Stack 2: Backend Stack

Located on the Application Server, handles API and async processing.

**Services:**
- **Redis** - Cache and Celery message broker
- **db-migration** - One-shot container for Alembic migrations
- **Celery Worker** - Async task processing (music generation, etc.)
- **aiproxysrv** - FastAPI backend application

**Startup Order:**
1. Redis (health check: ping)
2. db-migration (runs Alembic upgrade, exits)
3. Celery Worker (depends on Redis + migration)
4. aiproxysrv (depends on migration + Celery)

### Stack 3: Proxy Stack

Located on the Application Server, handles HTTPS termination and serves the frontend.

**Services:**
- **aiwebui-init** - One-shot container to copy Angular build to volume
- **Nginx** - Reverse proxy with SSL/TLS termination

**Features:**
- HTTPS termination with TLS 1.3
- Static file serving for Angular SPA
- Reverse proxy to backend API
- Rate limiting and security headers

---

## Docker Compose Configurations

### NAS Stack (`nas/docker-compose.yml`)

```yaml
services:
  minio:
    image: minio/minio
    container_name: minio
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    volumes:
      - /path/to/minio-data:/data
    command: server /data --console-address ":9001"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:17-alpine
    container_name: postgres
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - /path/to/postgres-data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 3
```

### Backend Stack (`aiproxysrv/docker-compose.yml`)

```yaml
networks:
  thwelly-net:
    external: true

services:
  redis:
    image: redis:alpine
    container_name: redis
    networks:
      - thwelly-net
    volumes:
      - redis-data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  db-migration:
    image: ghcr.io/<your-username>/aiproxysrv-app:<version>
    container_name: db-migration
    networks:
      - thwelly-net
    env_file:
      - .env
    command: ["alembic", "upgrade", "head"]
    working_dir: /app/src

  celery-worker:
    image: ghcr.io/<your-username>/celery-worker-app:<version>
    container_name: celery-worker
    networks:
      - thwelly-net
    env_file:
      - .env
    restart: unless-stopped
    depends_on:
      redis:
        condition: service_healthy
      db-migration:
        condition: service_completed_successfully
    healthcheck:
      test: ["CMD", "celery", "-A", "celery_app.celery_app", "inspect", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

  aiproxysrv-app:
    image: ghcr.io/<your-username>/aiproxysrv-app:<version>
    container_name: aiproxysrv-app
    networks:
      - thwelly-net
    ports:
      - "5050:5050"
    env_file:
      - .env
    restart: unless-stopped
    depends_on:
      db-migration:
        condition: service_completed_successfully
      celery-worker:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5050/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

volumes:
  redis-data:
```

### Proxy Stack (`forwardproxy/docker-compose.yml`)

```yaml
networks:
  thwelly-net:
    external: true

services:
  aiwebui-init:
    image: ghcr.io/<your-username>/aiwebui-app:<version>
    container_name: aiwebui-init
    volumes:
      - webui-content:/app/dist
    command: ["sh", "-c", "cp -r /app/browser/* /app/dist/ && echo 'UI copied'"]

  nginx:
    image: nginx:alpine
    container_name: nginx
    networks:
      - thwelly-net
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
      - webui-content:/usr/share/nginx/html/aiwebui:ro
      - ./logs:/var/log/nginx
    restart: unless-stopped
    depends_on:
      aiwebui-init:
        condition: service_completed_successfully
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/nginx_status"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s

volumes:
  webui-content:
```

---

## Nginx Configuration

### Key Security Settings

```nginx
# TLS Configuration
ssl_protocols TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
ssl_prefer_server_ciphers off;
ssl_session_timeout 1d;
ssl_session_cache shared:SSL:50m;

# Security Headers
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
```

### Rate Limiting

```nginx
# Define rate limit zones
limit_req_zone $binary_remote_addr zone=general:10m rate=5r/s;
limit_req_zone $binary_remote_addr zone=auth:10m rate=1r/s;

# Apply rate limits
location /api/v1/auth/ {
    limit_req zone=auth burst=3 nodelay;
    proxy_pass http://aiproxysrv-app:5050;
}

location /api/ {
    limit_req zone=general burst=20 nodelay;
    proxy_pass http://aiproxysrv-app:5050;
}
```

### Large File Upload Support

```nginx
# For music file uploads (up to 2GB)
client_max_body_size 2048M;

# Extended timeouts for AI endpoints
location ~ ^/api/v1/(ollama|mureka|openai)/ {
    proxy_read_timeout 600s;
    proxy_send_timeout 600s;
    proxy_pass http://aiproxysrv-app:5050;
}
```

### Angular SPA Routing

```nginx
location / {
    root /usr/share/nginx/html/aiwebui;
    try_files $uri $uri/ /index.html;

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Never cache index.html
    location = /index.html {
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }
}
```

### Example Full Configuration

```nginx
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=general:10m rate=5r/s;
    limit_req_zone $binary_remote_addr zone=auth:10m rate=1r/s;

    # Upstream definitions
    upstream backend {
        server aiproxysrv-app:5050;
    }

    # HTTP redirect to HTTPS
    server {
        listen 80;
        server_name _;
        return 301 https://$host$request_uri;
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name _;

        ssl_certificate /etc/nginx/certs/fullchain.pem;
        ssl_certificate_key /etc/nginx/certs/privkey.pem;
        ssl_protocols TLSv1.3;
        ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
        ssl_prefer_server_ciphers off;

        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;

        client_max_body_size 2048M;

        # Health check endpoint
        location /nginx_status {
            stub_status on;
            access_log off;
            allow 127.0.0.1;
            deny all;
        }

        # API proxy
        location /api/ {
            limit_req zone=general burst=20 nodelay;
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # AI endpoints with extended timeout
        location ~ ^/api/v1/(ollama|chat)/ {
            limit_req zone=general burst=20 nodelay;
            proxy_read_timeout 600s;
            proxy_send_timeout 600s;
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Angular SPA
        location / {
            root /usr/share/nginx/html/aiwebui;
            try_files $uri $uri/ /index.html;

            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
                expires 1y;
                add_header Cache-Control "public, immutable";
            }

            location = /index.html {
                add_header Cache-Control "no-cache, no-store, must-revalidate";
            }
        }
    }
}
```

---

## Environment Variables

Create a `.env` file for the backend stack:

```bash
# =============================================================================
# Server Configuration
# =============================================================================
FLASK_SERVER_HOST=0.0.0.0
FLASK_SERVER_PORT=5050

# =============================================================================
# Database (PostgreSQL on NAS)
# =============================================================================
DATABASE_URL=postgresql://user:password@<NAS_IP>:5432/aiproxysrv

# =============================================================================
# Redis
# =============================================================================
REDIS_URL=redis://redis:6379/0

# =============================================================================
# S3 Storage (MinIO on NAS)
# =============================================================================
MINIO_ENDPOINT=<NAS_IP>:9000
MINIO_ACCESS_KEY=your-access-key
MINIO_SECRET_KEY=your-secret-key
MINIO_BUCKET=your-bucket
MINIO_SECURE=false

# =============================================================================
# Security
# =============================================================================
# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET_KEY=your-jwt-secret-minimum-32-chars
JWT_EXPIRATION_HOURS=240

# Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_SECRET_KEY=your-fernet-key

# =============================================================================
# External APIs (Optional)
# =============================================================================
# OpenAI - for DALL-E image generation
OPENAI_API_KEY=sk-...

# Mureka - for music generation
MUREKA_API_KEY=...

# Anthropic - for Claude AI
CLAUDE_API_KEY=...

# =============================================================================
# Ollama (Local LLM)
# =============================================================================
OLLAMA_URL=http://<APP_SERVER_IP>:11434
OLLAMA_DEFAULT_MODEL=llama3.2:3b

# =============================================================================
# Celery
# =============================================================================
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### Security Notes

- Never commit `.env` files to version control
- Use strong, randomly generated secrets
- Rotate API keys periodically
- Consider using Docker secrets for sensitive values in production

---

## Deployment Checklist

### Initial Setup

1. **NAS Server Setup**
   ```bash
   # Create data directories
   mkdir -p /path/to/postgres-data
   mkdir -p /path/to/minio-data

   # Start NAS stack
   cd nas/
   docker compose up -d

   # Verify services
   docker compose ps
   ```

2. **Create MinIO Bucket**
   - Access MinIO Console: `http://<NAS_IP>:9001`
   - Create bucket for application data
   - Create access key for application

3. **App Server Setup**
   ```bash
   # Create Docker network
   docker network create thwelly-net

   # Install certificates
   mkdir -p forwardproxy/certs
   # Copy fullchain.pem and privkey.pem
   ```

4. **Configure Environment**
   ```bash
   cd aiproxysrv/
   cp env_template .env
   # Edit .env with production values
   ```

5. **Start Backend Stack**
   ```bash
   cd aiproxysrv/
   docker compose up -d

   # Watch migration logs
   docker logs -f db-migration

   # Verify all services
   docker compose ps
   ```

6. **Seed Database (Required for AI Features)**

   The Ollama integration uses template-driven prompts stored in the database. Seed the required data:

   ```bash
   # From project root - run against PostgreSQL on NAS
   cat scripts/db/seed_prompts.sql | docker exec -i postgres psql -U aiproxy -d aiproxysrv
   cat scripts/db/seed_lyric_parsing_rules.sql | docker exec -i postgres psql -U aiproxy -d aiproxysrv
   ```

   > **Note:** Without seeding, AI chat features (lyric improvement, title generation, etc.) will not work.

7. **Setup Ollama (Optional - for Local LLM)**

   If you want to use local AI models instead of cloud APIs:

   ```bash
   # Install Ollama on App Server
   curl -fsSL https://ollama.com/install.sh | sh

   # Pull recommended model
   ollama pull llama3.2:3b

   # Verify Ollama is running
   curl http://localhost:11434/api/tags
   ```

   Configure in `.env`:
   ```bash
   OLLAMA_URL=http://localhost:11434
   OLLAMA_DEFAULT_MODEL=llama3.2:3b
   ```

8. **Start Proxy Stack**
   ```bash
   cd forwardproxy/
   docker compose up -d

   # Verify nginx
   docker logs nginx
   ```

9. **Create First User**

   The application has an open registration endpoint. Create your first user via API or the web UI:

   ```bash
   # Via API
   curl -X POST https://your-domain/api/v1/user/create \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "email": "admin@example.com", "password": "your-secure-password"}'
   ```

   Or simply navigate to the application URL and use the registration form.

### Update Deployment

```bash
# Pull latest images
docker compose pull

# Recreate containers with new images
docker compose up -d

# Migration runs automatically via db-migration container
```

### Rollback

```bash
# Stop current version
docker compose down

# Edit docker-compose.yml to previous version tag
# Or use explicit image tag:
docker compose up -d --force-recreate aiproxysrv-app celery-worker
```

---

## Health Checks

### Service Health Endpoints

| Service | Health Check | Expected Response |
|---------|--------------|-------------------|
| **aiproxysrv** | `GET /api/v1/health` | `{"status": "healthy"}` |
| **Nginx** | `GET /nginx_status` | Stub status page |
| **PostgreSQL** | `pg_isready -U user` | Exit code 0 |
| **Redis** | `redis-cli ping` | `PONG` |
| **MinIO** | `GET /minio/health/live` | HTTP 200 |

### Monitoring Commands

```bash
# Check all container status
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Check backend health
curl -s https://your-domain/api/v1/health | jq

# Check container logs
docker logs -f aiproxysrv-app --tail 100
docker logs -f celery-worker --tail 100
docker logs -f nginx --tail 100

# Check Celery worker status
docker exec celery-worker celery -A celery_app.celery_app inspect active

# Check Redis connectivity
docker exec redis redis-cli info clients
```

### Common Issues

| Symptom | Check | Solution |
|---------|-------|----------|
| 502 Bad Gateway | Is aiproxysrv running? | `docker logs aiproxysrv-app` |
| Database connection failed | Is PostgreSQL accessible? | Check firewall, credentials |
| Slow AI responses | Is Celery worker running? | `docker logs celery-worker` |
| File upload fails | Check nginx body size | Increase `client_max_body_size` |

---

## Backup & Recovery

### Database Backup

```bash
#!/bin/bash
# backup-db.sh - Run on NAS server

BACKUP_DIR="/path/to/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_CONTAINER="postgres"

# Create backup
docker exec $DB_CONTAINER pg_dump -U aiproxy aiproxysrv | gzip > "$BACKUP_DIR/aiproxysrv_$TIMESTAMP.sql.gz"

# Keep last 7 days
find "$BACKUP_DIR" -name "aiproxysrv_*.sql.gz" -mtime +7 -delete

echo "Backup completed: aiproxysrv_$TIMESTAMP.sql.gz"
```

### Database Restore

```bash
#!/bin/bash
# restore-db.sh

BACKUP_FILE="$1"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: ./restore-db.sh <backup_file.sql.gz>"
    exit 1
fi

# Stop dependent services
docker stop aiproxysrv-app celery-worker

# Restore database
gunzip -c "$BACKUP_FILE" | docker exec -i postgres psql -U aiproxy -d aiproxysrv

# Restart services
docker start celery-worker aiproxysrv-app

echo "Restore completed"
```

### MinIO Backup

MinIO data can be backed up using:

1. **mc mirror** (MinIO Client)
   ```bash
   mc alias set local http://<NAS_IP>:9000 ACCESS_KEY SECRET_KEY
   mc mirror local/your-bucket /path/to/backup/
   ```

2. **Volume backup**
   ```bash
   # Stop MinIO temporarily
   docker stop minio

   # Backup data directory
   tar -czvf minio-backup.tar.gz /path/to/minio-data

   # Restart MinIO
   docker start minio
   ```

### Automated Backup Schedule

Add to crontab:

```cron
# Daily database backup at 2 AM
0 2 * * * /path/to/backup-db.sh >> /var/log/backup.log 2>&1

# Weekly MinIO backup on Sunday at 3 AM
0 3 * * 0 /path/to/backup-minio.sh >> /var/log/backup.log 2>&1
```

---

## Appendix

### SSL Certificate Setup (Let's Encrypt)

```bash
# Install certbot
apt install certbot

# Obtain certificate (standalone mode)
certbot certonly --standalone -d your-domain.com

# Copy to nginx certs directory
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem forwardproxy/certs/
cp /etc/letsencrypt/live/your-domain.com/privkey.pem forwardproxy/certs/

# Auto-renewal cron
0 0 1 * * certbot renew --quiet && docker exec nginx nginx -s reload
```

### Self-Signed Certificate (Development/Internal)

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout forwardproxy/certs/privkey.pem \
  -out forwardproxy/certs/fullchain.pem \
  -subj "/CN=your-hostname"
```

### Container Resource Limits

For production, consider adding resource limits:

```yaml
services:
  aiproxysrv-app:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 512M

  celery-worker:
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 1G
```
