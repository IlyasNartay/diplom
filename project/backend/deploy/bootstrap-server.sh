#!/usr/bin/env bash
# First-time VPS setup for diplom monorepo deploy.
# Run on the server as root after: ssh root@YOUR_IP

set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/IlyasNartay/diplom.git}"
REPO_DIR="${REPO_DIR:-$HOME/ticketon-microservices}"
BACKEND_DIR="$REPO_DIR/project/backend"

echo "==> Installing Docker (if missing)..."
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
  systemctl enable --now docker
fi

echo "==> Cloning or updating repo..."
if [ -d "$REPO_DIR/.git" ]; then
  git -C "$REPO_DIR" fetch origin
  git -C "$REPO_DIR" checkout main
  git -C "$REPO_DIR" pull origin main
else
  git clone "$REPO_URL" "$REPO_DIR"
fi

cd "$BACKEND_DIR"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example — review it if needed."
fi

if [ ! -f .env.prod ]; then
  cp .env.prod.example .env.prod
  echo ""
  echo "IMPORTANT: edit .env.prod before production traffic:"
  echo "  nano $BACKEND_DIR/.env.prod"
  echo "Set JWT_SECRET_KEY to a long random value."
fi

echo "==> Building and starting stack..."
docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml up -d --build

echo ""
echo "Done. App should be reachable on port 80."
echo "Backend dir: $BACKEND_DIR"
echo "GitHub Actions deploy will work after secrets DO_HOST, DO_USERNAME, DO_PASSWORD are set."
