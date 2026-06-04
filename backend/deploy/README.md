# Environments

## Base stack

`docker-compose.yml` is now internal-only by default:

- no public ports are published from the base file
- service-to-service traffic stays inside the Docker network
- public exposure is added only by `docker-compose.dev.yml` or `docker-compose.prod.yml`

## Dev

Start local development:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

Exposed in development:

- frontend: `http://localhost:3000`
- api gateway: `http://localhost:8080`
- kafka ui: `http://localhost:8081`

## Prod

1. Create `.env.prod` from `.env.prod.example`.
2. Fill in:
   - `DOMAIN_NAME`
   - `LETSENCRYPT_EMAIL`
   - `JWT_SECRET_KEY`
   - `BACKEND_CORS_ORIGINS`
   - `PUBLIC_TICKET_BASE_URL`
3. Point your DNS `A` record to the server IP before certificate issuance.
4. Keep the frontend directory at `../frontend` relative to `backend/`.
5. Start the stack:

```powershell
docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Shortcut:

```powershell
cd deploy
.\start-prod.ps1
```

Production exposure:

- only `nginx` publishes `80/443`
- `frontend`, `api_gateway`, database, Kafka, Redis, and internal services stay private inside Docker

## HTTPS and domain

Run the initial certificate issue command after DNS is already pointing to the server:

```powershell
docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml run --rm certbot certonly --webroot -w /var/www/certbot -d your-domain.com -m you@example.com --agree-tos --no-eff-email
```

Then restart nginx:

```powershell
docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml restart nginx
```

Shortcut:

```powershell
cd deploy
.\issue-cert.ps1 -Domain your-domain.com -Email you@example.com
```

How it works:

- without certificates, nginx serves HTTP and still proxies the app
- when certificates exist, nginx automatically switches to the HTTPS template
- automatic renewal is available through the `certbot` profile/service
- uploaded posters and generated ticket/media files continue to work through nginx on the same domain
