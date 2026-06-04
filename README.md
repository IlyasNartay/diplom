# Diplom

Main repository for the diploma project. The previously separated backend and frontend work is now collected in one `main` branch.

## Project

- `backend/` - FastAPI microservices, PostgreSQL, Kafka, Redis, migrations, Docker Compose, deployment configs, and tests.
- `frontend/` - Vue 3 + Vite + Tailwind CSS + PWA client for the ticket booking system.

## Research

- [IlyasNartayGp/hfbs](https://github.com/IlyasNartayGp/hfbs)
- [IlyasNartayGp/hfbs-v2](https://github.com/IlyasNartayGp/hfbs-v2)

## Run

Backend development stack:

```bash
cd backend
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

Frontend development server:

```bash
cd frontend
npm install
npm run dev
```
