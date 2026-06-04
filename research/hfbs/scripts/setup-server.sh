#!/bin/bash
# scripts/setup-server.sh
# ══════════════════════════════════════════════════════════════
# Скрипт первоначальной настройки VPS (Ubuntu 22.04 / 24.04)
# Запускать от root: bash setup-server.sh your-domain.com
# ══════════════════════════════════════════════════════════════

set -euo pipefail  # Останавливаемся при любой ошибке

DOMAIN="${1:-}"
if [ -z "$DOMAIN" ]; then
    echo "❌ Укажите домен: bash setup-server.sh your-domain.com"
    exit 1
fi

echo "🚀 Настройка сервера для HFBS (домен: $DOMAIN)"
echo "================================================"

# ── 1. Системные обновления ────────────────────────────────────
echo "📦 Обновление пакетов..."
apt-get update -qq
apt-get upgrade -y -qq

# ── 2. Базовые утилиты ─────────────────────────────────────────
apt-get install -y -qq \
    curl wget git ufw fail2ban \
    htop vim nano unzip \
    ca-certificates gnupg lsb-release

# ── 3. Docker Engine ───────────────────────────────────────────
echo "🐳 Установка Docker..."
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
    > /etc/apt/sources.list.d/docker.list

apt-get update -qq
apt-get install -y -qq \
    docker-ce docker-ce-cli containerd.io \
    docker-buildx-plugin docker-compose-plugin

# Запускаем Docker
systemctl enable --now docker
echo "✅ Docker $(docker --version)"
echo "✅ Docker Compose $(docker compose version)"

# ── 4. Создаём deploy-пользователя ────────────────────────────
echo "👤 Создание пользователя deploy..."
if ! id -u deploy &>/dev/null; then
    useradd -m -s /bin/bash deploy
    usermod -aG docker deploy
    echo "✅ Пользователь deploy создан (в группе docker)"
fi

# Настройка SSH ключа для deploy (скопируйте свой публичный ключ)
mkdir -p /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
# echo "ssh-rsa AAAA... your-key" >> /home/deploy/.ssh/authorized_keys
# chmod 600 /home/deploy/.ssh/authorized_keys
# chown -R deploy:deploy /home/deploy/.ssh

# ── 5. Firewall (UFW) ──────────────────────────────────────────
echo "🔒 Настройка firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh         # 22
ufw allow 80/tcp      # HTTP
ufw allow 443/tcp     # HTTPS
ufw --force enable
echo "✅ UFW включён (открыты: SSH, 80, 443)"

# ── 6. Fail2ban (защита от brute force) ────────────────────────
echo "🛡 Настройка fail2ban..."
systemctl enable --now fail2ban
echo "✅ Fail2ban активен"

# ── 7. Директория проекта ──────────────────────────────────────
echo "📁 Создание директории проекта..."
mkdir -p /opt/hfbs
chown deploy:deploy /opt/hfbs

# ── 8. Swap (если RAM < 4GB) ───────────────────────────────────
TOTAL_RAM=$(free -m | awk '/^Mem:/{print $2}')
if [ "$TOTAL_RAM" -lt 4096 ]; then
    echo "💾 Создание swap (RAM: ${TOTAL_RAM}MB < 4GB)..."
    if [ ! -f /swapfile ]; then
        fallocate -l 2G /swapfile
        chmod 600 /swapfile
        mkswap /swapfile
        swapon /swapfile
        echo '/swapfile none swap sw 0 0' >> /etc/fstab
        echo "✅ Swap 2GB создан"
    fi
fi

# ── 9. Настройки ядра для высокой нагрузки ─────────────────────
cat >> /etc/sysctl.conf << 'EOF'
# HFBS performance tuning
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_fin_timeout = 15
vm.swappiness = 10
EOF
sysctl -p

echo ""
echo "✅ Сервер настроен!"
echo "================================================"
echo "Следующий шаг:"
echo "  1. su - deploy"
echo "  2. cd /opt/hfbs"
echo "  3. Скопируйте проект и .env.prod"
echo "  4. bash scripts/deploy.sh $DOMAIN"
