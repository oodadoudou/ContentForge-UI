# Docker Deploy Guide

## Prereqs
- Docker + Docker Compose v2

## Quick start
```bash
docker compose up --build
```
- Frontend: http://localhost:4073
- Backend API: http://localhost:8000 (health at /health)

## Images
- backend: builds from backend/Dockerfile (python:3.11-slim)
- frontend: builds from frontend/Dockerfile (node:22-alpine)

## Volumes
- Mounts ./backend/shared_assets into container read-only so settings.json can be supplied without baking into image.

## Environment
- Backend listens on 0.0.0.0:8000
- Frontend dev server via Vite on 0.0.0.0:4073; adjust `VITE_API_BASE_URL` env for remote targets.

## Production notes
- Replace frontend dev command with `npm run build` + static serve (nginx or `vite preview`).
- Add a reverse proxy (nginx/Caddy) to terminate TLS and route /api to backend and / to frontend static.
- Add persistent volume if backend gains writable state.
