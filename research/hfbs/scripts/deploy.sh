#!/bin/bash
# scripts/deploy.sh
# ══════════════════════════════════════════════════════════════
# Деплой HFBS на сервере.
# Запуск: bash scripts/deploy.sh your-domain.com [первый_запуск]
#
# Что делает:
#   1. Получает SSL сертификат (только при первом запуске)
#   2. Собирает/тянет Docker образы
#   3. Накатывает миграции
#   4. Запускает все контейнеры
#   5. Заполняет тестовыми данными (опционально)
# ══════════════════════════════════════════════════════════════

set -euo pipefail

DOMAIN="${1:-}"
FIRST_RUN="${2:-false}"
ENV_FILE=".env.prod"
COMPOSE_FILE="docker-compose.prod.yml"

if [ -z "$DOMAIN" ]; then
    echo "❌ Укажите домен: bash deploy.sh your-domain.com"
    exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Файл $ENV_FILE не найден!"
    echo "   cp .env.example $ENV_FILE && nano $ENV_FILE"
    exit 1
fi

echo "🚀 Деплой HFBS → $DOMAIN"
echo "================================"

# Загружаем переменные окружения
export $(grep -v '^#' $ENV_FILE | xargs)

# ── SSL сертификат (только при первом деплое) ──────────────────
if [ "$FIRST_RUN" = "first" ]; then
    echo "🔐 Получение SSL сертификата (Let's Encrypt)..."

    # Сначала запускаем Nginx только для HTTP (для challenge)
    docker compose -f $COMPOSE_FILE --env-file $ENV_FILE \
        up -d nginx postgres redis

    sleep 5  # Ждём запуска Nginx

    # Получаем сертификат
    docker compose -f $COMPOSE_FILE --env-file $ENV_FILE run --rm certbot \
        certbot certonly \
        --webroot \
        --webroot-path /var/www/certbot \
        --email admin@$DOMAIN \
        --agree-tos \
        --no-eff-email \
        -d $DOMAIN \
        -d www.$DOMAIN \
        -d api.$DOMAIN \
        -d async.$DOMAIN

    echo "✅ SSL сертификат получен"

    # Обновляем nginx.conf с реальным доменом
    sed -i "s/your-domain.com/$DOMAIN/g" nginx/conf.d/hfbs.conf
fi

# ── Pull / Build образов ───────────────────────────────────────
echo "🐳 Обновление Docker образов..."
docker compose -f $COMPOSE_FILE --env-file $ENV_FILE pull --ignore-pull-failures 2>/dev/null || true
docker compose -f $COMPOSE_FILE --env-file $ENV_FILE build --no-cache

# ── Запуск инфраструктуры ─────────────────────────────────────
echo "🏗  Запуск баз данных и брокеров..."
docker compose -f $COMPOSE_FILE --env-file $ENV_FILE \
    up -d postgres redis zookeeper kafka

echo "⏳ Ожидание готовности PostgreSQL..."
until docker compose -f $COMPOSE_FILE --env-file $ENV_FILE \
    exec postgres pg_isready -U $POSTGRES_USER -q; do
    sleep 2
done
echo "✅ PostgreSQL готов"

# ── Миграции Django ────────────────────────────────────────────
echo "🔄 Применение Django миграций..."
docker compose -f $COMPOSE_FILE --env-file $ENV_FILE \
    run --rm django python manage.py migrate --noinput

# ── Создание таблиц FastAPI ────────────────────────────────────
echo "🔄 Создание таблиц FastAPI..."
docker compose -f $COMPOSE_FILE --env-file $ENV_FILE \
    run --rm fastapi python alembic_init.py

# ── Тестовые данные (только при первом запуске) ────────────────
if [ "$FIRST_RUN" = "first" ]; then
    echo "🌱 Загрузка тестовых данных..."
    docker compose -f $COMPOSE_FILE --env-file $ENV_FILE \
        run --rm django python manage.py shell < seed.py
fi

# ── Запуск всех сервисов ───────────────────────────────────────
echo "🚀 Запуск всех сервисов..."
docker compose -f $COMPOSE_FILE --env-file $ENV_FILE up -d

# ── Проверка здоровья ──────────────────────────────────────────
echo "⏳ Проверка сервисов..."
sleep 15

check_service() {
    local name=$1
    local url=$2
    if curl -sf "$url" > /dev/null 2>&1; then
        echo "  ✅ $name"
    else
        echo "  ⚠️  $name — не отвечает (проверьте: docker logs hfbs_$name)"
    fi
}

check_service "Django"  "http://localhost:8000/api/v1/events/"
check_service "FastAPI" "http://localhost:8001/health"
check_service "Nginx"   "http://localhost/health" 2>/dev/null || echo "  ℹ️  Nginx — проверьте через браузер"

echo ""
echo "✅ Деплой завершён!"
echo "================================"
echo "🌐 Сайт:         https://$DOMAIN"
echo "📚 Django API:   https://api.$DOMAIN/api/docs/"
echo "⚡ FastAPI docs: https://async.$DOMAIN/docs"
echo "🔧 Django Admin: https://api.$DOMAIN/admin/"
echo ""
echo "Статус контейнеров:"
docker compose -f $COMPOSE_FILE --env-file $ENV_FILE ps
