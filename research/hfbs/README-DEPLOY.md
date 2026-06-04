# 🖥️ Развёртывание HFBS на сервере

Три способа, от простого к профессиональному:

---

## Способ 1 — VPS вручную (самый простой, для диплома)

### Минимальные требования сервера
| Параметр | Минимум | Рекомендуется |
|----------|---------|---------------|
| CPU | 2 ядра | 4 ядра |
| RAM | 2 GB | 4 GB |
| Диск | 20 GB SSD | 40 GB SSD |
| OS | Ubuntu 22.04 | Ubuntu 24.04 |
| Провайдер | Timeweb, Selectel, Hetzner, DigitalOcean |

---

### Шаг 1 — Арендуйте VPS и настройте DNS

Купите VPS у любого провайдера. В DNS-панели добавьте A-записи:

```
your-domain.com      A → IP_вашего_сервера
www.your-domain.com  A → IP_вашего_сервера
api.your-domain.com  A → IP_вашего_сервера
async.your-domain.com A → IP_вашего_сервера
```

> Для диплома можно использовать **бесплатные домены**: freenom.com (.tk, .ml) или студенческий GitHub Education Pack (namecheap).

---

### Шаг 2 — Настройте сервер

```bash
# Подключитесь по SSH
ssh root@IP_ВАШЕГО_СЕРВЕРА

# Запустите скрипт настройки (устанавливает Docker, UFW, fail2ban)
curl -O https://raw.githubusercontent.com/YOUR_REPO/main/scripts/setup-server.sh
bash setup-server.sh your-domain.com
```

Или вручную:

```bash
# Обновление
apt-get update && apt-get upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com | sh
systemctl enable --now docker

# Firewall
ufw allow ssh
ufw allow 80
ufw allow 443
ufw enable
```

---

### Шаг 3 — Загрузите проект на сервер

```bash
# Вариант A: Git (рекомендуется)
cd /opt
git clone https://github.com/YOUR_USER/hfbs.git
cd hfbs

# Вариант B: scp (загрузить zip локально)
# Локально:
scp hfbs-diploma-project.zip root@IP:/opt/
# На сервере:
cd /opt && unzip hfbs-diploma-project.zip && cd hfbs
```

---

### Шаг 4 — Создайте .env.prod

```bash
cp .env.example .env.prod
nano .env.prod
```

Заполните все значения:

```env
DOMAIN=your-domain.com
REGISTRY=local                    # если собираете на сервере

POSTGRES_USER=hfbs_prod
POSTGRES_PASSWORD=СГЕНЕРИРУЙТЕ_СИЛЬНЫЙ_ПАРОЛЬ
POSTGRES_DB=hfbs_db

REDIS_PASSWORD=СГЕНЕРИРУЙТЕ_ПАРОЛЬ

# Генерация Django SECRET_KEY:
# python3 -c "import secrets; print(secrets.token_urlsafe(50))"
DJANGO_SECRET_KEY=...50_символов...

# Генерация FastAPI JWT:
# openssl rand -hex 32
FASTAPI_JWT_SECRET=...64_символа...
```

---

### Шаг 5 — Первый запуск (с SSL)

```bash
chmod +x scripts/deploy.sh scripts/setup-server.sh

# Первый запуск — получает SSL, создаёт БД, загружает тестовые данные
bash scripts/deploy.sh your-domain.com first
```

**Что произойдёт:**
1. Запустятся PostgreSQL и Redis
2. Let's Encrypt выдаст SSL сертификат
3. Накатятся Django миграции
4. Создадутся таблицы FastAPI
5. Запустятся все контейнеры + Nginx

---

### Шаг 6 — Проверка

```bash
# Статус контейнеров
docker ps

# Логи конкретного сервиса
docker logs hfbs_django -f
docker logs hfbs_fastapi -f
docker logs hfbs_nginx -f

# Проверка API
curl https://your-domain.com/api/v1/events/
curl https://async.your-domain.com/health
```

Откройте в браузере:
- **https://your-domain.com** — Frontend
- **https://api.your-domain.com/api/docs/** — Django Swagger
- **https://async.your-domain.com/docs** — FastAPI Swagger
- **https://api.your-domain.com/admin/** — Django Admin

---

### Обновление после изменений в коде

```bash
# На сервере
cd /opt/hfbs
git pull

# Пересобрать и перезапустить
bash scripts/deploy.sh your-domain.com
```

---

## Способ 2 — Автоматический деплой через GitHub Actions (CI/CD)

### Настройка

1. Форкните репозиторий на GitHub
2. Добавьте секреты в **Settings → Secrets → Actions**:

| Секрет | Значение |
|--------|----------|
| `SERVER_HOST` | IP вашего VPS |
| `SERVER_USER` | `deploy` |
| `SERVER_SSH_KEY` | Приватный SSH ключ |
| `SERVER_PORT` | `22` |
| `DOMAIN` | `your-domain.com` |
| `PROD_ENV` | Содержимое вашего `.env.prod` |

3. Добавьте файл `.github/workflows/deploy.yml` (уже есть в архиве)

### Как это работает

```
Вы пишете код
    ↓
git push origin main
    ↓
GitHub Actions:
  1. Запускает тесты Django + FastAPI
  2. Собирает 3 Docker образа
  3. Пушит в ghcr.io (GitHub Container Registry)
  4. SSH на сервер → docker pull → docker compose up -d
    ↓
Сайт обновлён автоматически!
```

---

## Способ 3 — Облачные платформы (без своего сервера)

### Railway.app (самый простой бесплатный вариант)

```bash
npm install -g @railway/cli
railway login
railway init
railway up
```

Railway автоматически обнаружит `docker-compose.yml` и задеплоит всё.

---

### Render.com

1. Подключите GitHub репозиторий
2. Создайте **Web Service** для Django (Dockerfile)
3. Создайте **Web Service** для FastAPI
4. Создайте **Static Site** для Frontend
5. Добавьте **PostgreSQL** и **Redis** как managed services

---

### Timeweb Cloud / Selectel (российские провайдеры)

Оба поддерживают Docker и имеют управляемые PostgreSQL и Redis.
Подходят если нужна локация в России.

```bash
# Установка Docker на Timeweb / Selectel VPS (Ubuntu)
curl -fsSL https://get.docker.com | sh
# Дальше — тот же процесс что в Способе 1
```

---

## Полезные команды для обслуживания

```bash
# Просмотр логов в реальном времени
docker compose -f docker-compose.prod.yml logs -f

# Перезапуск одного сервиса
docker compose -f docker-compose.prod.yml restart django

# Остановить всё (данные сохранятся в volumes)
docker compose -f docker-compose.prod.yml down

# Остановить и удалить все данные (!)
docker compose -f docker-compose.prod.yml down -v

# Бэкап PostgreSQL
docker exec hfbs_postgres pg_dump -U hfbs_prod hfbs_db > backup_$(date +%Y%m%d).sql

# Восстановление из бэкапа
docker exec -i hfbs_postgres psql -U hfbs_prod hfbs_db < backup_20250315.sql

# Обновление SSL сертификата вручную
docker exec hfbs_certbot certbot renew

# Мониторинг ресурсов
docker stats

# Очистка неиспользуемых образов (экономим место)
docker system prune -f
```

---

## Архитектура в продакшне

```
Internet (HTTPS)
      │
      ▼
┌─────────────────────────────────────────┐
│           Nginx :443                    │
│   SSL termination + reverse proxy       │
└──────┬─────────┬──────────┬─────────────┘
       │         │          │
  /api/v1/   /async/   / (frontend)
       │         │          │
  ┌────▼───┐ ┌───▼────┐ ┌───▼──────┐
  │ Django │ │FastAPI │ │ React    │
  │  :8000 │ │  :8001 │ │ (Nginx)  │
  │Gunicorn│ │Gunicorn│ │  :80     │
  │4 worker│ │+Uvicorn│ └──────────┘
  └────┬───┘ └───┬────┘
       │         │
  ┌────▼─────────▼─────┐
  │    PostgreSQL       │
  │    Redis           │
  │    Kafka           │
  └────────────────────┘
```
