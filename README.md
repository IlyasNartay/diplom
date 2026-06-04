# Diplom

Main repository for the diploma project. The previously separated project and research work is now collected in one `main` branch.

## Project

- `project/backend/` - FastAPI microservices, PostgreSQL, Kafka, Redis, migrations, Docker Compose, deployment configs, and tests.
- `project/frontend/` - Vue 3 + Vite + Tailwind CSS + PWA client for the ticket booking system.

## Research

- `research/hfbs/` - imported from [IlyasNartayGp/hfbs](https://github.com/IlyasNartayGp/hfbs).
- `research/hfbs-v2/` - imported from [IlyasNartayGp/hfbs-v2](https://github.com/IlyasNartayGp/hfbs-v2).

## Run

Backend development stack:

```bash
cd project/backend
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

Frontend development server:

```bash
cd project/frontend
npm install
npm run dev
```
