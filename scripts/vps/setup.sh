#!/bin/bash
# =============================================================
# VPS Initial Setup Script for chmusicpro
# Target: Hetzner CAX31 (ARM64), Ubuntu 24.04
# =============================================================
set -e

DOMAIN="mymusicproduction.thwelly.ch"
DEPLOY_DIR="/opt/chmusicpro"

echo "=== chmusicpro VPS Setup ==="

# ----------------------------------------------------------
# 1. System updates
# ----------------------------------------------------------
echo "[1/6] System update..."
apt-get update && apt-get upgrade -y

# ----------------------------------------------------------
# 2. Install Docker
# ----------------------------------------------------------
echo "[2/6] Installing Docker..."
if ! command -v docker &> /dev/null; then
  curl -fsSL https://get.docker.com | sh
  echo "Docker installed."
else
  echo "Docker already installed."
fi

# ----------------------------------------------------------
# 3. Install Certbot (Let's Encrypt)
# ----------------------------------------------------------
echo "[3/6] Installing Certbot..."
apt-get install -y certbot

# ----------------------------------------------------------
# 4. Create directory structure
# ----------------------------------------------------------
echo "[4/6] Creating directory structure..."
mkdir -p ${DEPLOY_DIR}/{infrastructure,chmusicprosrv,forwardproxy/nginx,forwardproxy/logs}

# ----------------------------------------------------------
# 5. Create Docker network
# ----------------------------------------------------------
echo "[5/6] Creating Docker network..."
docker network create chmusicpro-net 2>/dev/null || echo "Network already exists."

# ----------------------------------------------------------
# 6. Obtain SSL certificate
# ----------------------------------------------------------
echo "[6/6] Obtaining Let's Encrypt certificate..."
if [ ! -d "/etc/letsencrypt/live/${DOMAIN}" ]; then
  certbot certonly --standalone -d ${DOMAIN} --agree-tos --non-interactive --email admin@thwelly.ch
  # Create Docker volume for Let's Encrypt certs
  docker volume create letsencrypt-data
  # Copy certs into Docker volume via temp container
  docker run --rm -v letsencrypt-data:/certs -v /etc/letsencrypt:/host-certs:ro alpine sh -c \
    "cp -rL /host-certs/* /certs/"
  echo "SSL certificate obtained."
else
  echo "SSL certificate already exists."
fi

# ----------------------------------------------------------
# Setup certbot auto-renewal cron
# ----------------------------------------------------------
cat > /etc/cron.d/certbot-renew << 'CRON'
# Renew Let's Encrypt certs and copy to Docker volume
0 3 * * 1 root certbot renew --quiet && docker run --rm -v letsencrypt-data:/certs -v /etc/letsencrypt:/host-certs:ro alpine sh -c "cp -rL /host-certs/* /certs/" && docker restart forward-proxy
CRON

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "  1. Copy docker-compose files to ${DEPLOY_DIR}/"
echo "  2. Copy .env to ${DEPLOY_DIR}/.env (based on env_template)"
echo "  3. Copy alembic.ini to ${DEPLOY_DIR}/chmusicprosrv/"
echo "  4. Copy nginx.conf to ${DEPLOY_DIR}/forwardproxy/nginx/"
echo "  5. Start services:"
echo "     cd ${DEPLOY_DIR}/infrastructure && docker compose up -d"
echo "     cd ${DEPLOY_DIR}/chmusicprosrv && docker compose up -d"
echo "     cd ${DEPLOY_DIR}/forwardproxy && docker compose up -d"
echo "  6. Seed database:"
echo "     docker exec -i postgres psql -U aiproxy -d aiproxysrv < seed_prompts.sql"
