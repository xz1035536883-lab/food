#!/bin/bash
# Deploy script for food-calorie backend to Alibaba Cloud Thailand server
# Usage: ./deploy.sh <server-ip> [ssh-user]

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: $0 <server-ip> [ssh-user]"
    echo "  server-ip  : Alibaba Cloud server IP address"
    echo "  ssh-user   : SSH user (default: root)"
    exit 1
fi

SERVER_IP="$1"
SSH_USER="${2:-root}"
REMOTE_DIR="/root/food-backend"
LOCAL_BACKEND_DIR="$(cd "$(dirname "$0")/../backend" && pwd)"
DEPLOY_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Deploying to ${SSH_USER}@${SERVER_IP} ==="
echo "Remote dir: ${REMOTE_DIR}"

# Step 1: Sync backend code to server
echo ""
echo "--- Step 1: Syncing backend code ---"
rsync -avz \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    --exclude='runtime/' \
    --exclude='uploads/*' \
    --exclude='.env' \
    --exclude='food_calorie.db' \
    "${LOCAL_BACKEND_DIR}/" \
    "${SSH_USER}@${SERVER_IP}:${REMOTE_DIR}/"

# Step 1b: Copy nginx config to server (for first-time setup)
echo ""
echo "--- Copying nginx config ---"
scp "${DEPLOY_DIR}/nginx.conf" "${SSH_USER}@${SERVER_IP}:${REMOTE_DIR}/nginx.conf"

# Step 2: Build and start Docker containers
echo ""
echo "--- Step 2: Building and starting containers ---"
ssh "${SSH_USER}@${SERVER_IP}" << 'ENDSSH'
set -e

cd /root/food-backend

# Pull latest base image
docker pull python:3.11-slim || true

# Build and start
docker compose up -d --build

# Wait for container to be healthy
sleep 3

# Show status
echo ""
echo "--- Container Status ---"
docker compose ps

echo ""
echo "--- Recent Logs ---"
docker compose logs --tail=30
ENDSSH

# Step 3: Configure Nginx (first-time setup)
echo ""
echo "--- Step 3: Nginx configuration (checking...) ---"
ssh "${SSH_USER}@${SERVER_IP}" "test -f /etc/nginx/sites-enabled/food-api" 2>/dev/null && {
    echo "Nginx config already exists, skipping."
} || {
    echo ""
    echo "Nginx not yet configured. Run the following commands on the server:"
    echo ""
    echo "  # 1. Install nginx and certbot (if not already installed)"
    echo "  apt install -y nginx certbot python3-certbot-nginx"
    echo ""
    echo "  # 2. Copy and configure nginx (replace YOUR_DOMAIN with your actual domain)"
    echo "  cp /root/food-backend/nginx.conf /etc/nginx/sites-available/food-api"
    echo "  sed -i 's/your-domain.com/YOUR_DOMAIN/g' /etc/nginx/sites-available/food-api"
    echo "  ln -s /etc/nginx/sites-available/food-api /etc/nginx/sites-enabled/food-api"
    echo ""
    echo "  # 3. Test and reload nginx"
    echo "  nginx -t && systemctl reload nginx"
    echo ""
    echo "  # 4. Obtain SSL certificate (after DNS is pointed to this server)"
    echo "  certbot --nginx -d YOUR_DOMAIN"
}

echo ""
echo "=== Backend deployed ==="
echo ""
echo "Remaining manual steps:"
echo "  1. Set up .env on server at ${REMOTE_DIR}/.env"
echo "  2. Configure DNS A record to point your domain to ${SERVER_IP}"
echo "  3. Run the nginx setup commands above (first deploy only)"
echo "  4. Verify: curl http://${SERVER_IP}:8000/api/health"
echo "  5. After SSL:  curl https://YOUR_DOMAIN/api/health"
echo "  6. Update miniapp/app.js apiBase to your domain"
echo "  7. Add your domain to WeChat mini-program server domain whitelist"
