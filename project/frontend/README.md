# High-Load Ticket Booking System Frontend

Frontend application for `ticketon-microservices`, built as `Vite + Vue 3 + Tailwind CSS + PWA`.

## Stack

- Vue 3
- Vue Router
- Pinia
- Tailwind CSS
- Vite PWA

## Theme

The UI is styled around the provided SDU logo:

- deep midnight and royal navy backgrounds
- warm copper accents
- formal editorial typography instead of generic startup styling

## Pages

- Home and event catalog
- Event details and seat selection
- Login and registration
- Booking history
- Saved cards

## Backend integration

By default the frontend targets:

```env
VITE_API_BASE_URL=http://localhost:8080
```

This should point to the `api_gateway` from the backend repository.

## Run

### Docker Compose

The frontend is wired into the backend compose stack.

From the backend workspace:

```bash
cd ../ticketon-microservices
docker compose up -d --build
```

After startup:

- frontend: `http://localhost:3000`
- API gateway: `http://localhost:8080`

The nginx container serves the SPA and proxies:

- `/api/*`
- `/media/*`
- `/tickets/*`

to the backend `api_gateway` inside the Docker network.

1. Install Node.js 18+.
2. Install dependencies:

```bash
npm install
```

3. Create `.env` from `.env.example`.
4. Start dev server:

```bash
npm run dev
```

5. Build production bundle:

```bash
npm run build
```

## Note

This workspace was generated in an environment where `node` and `npm` were not installed, so dependency installation and runtime verification could not be executed here yet.
