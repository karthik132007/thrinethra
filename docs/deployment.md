# Docker deployment

The provided Compose stack contains PostgreSQL, FastAPI and Next.js. It binds published ports to host loopback. No Redis, Kubernetes or remote service is needed.

```bash
cp .env.example .env
# Set POSTGRES_PASSWORD to a strong local value in .env.
# Set OPERATOR_TOKEN for authenticated access.
mkdir -p runtime/models
# Optional real inference weights:
.venv/bin/python scripts/download_model.py
docker compose up --build
```

Open http://localhost:3000. Containers initialize schema at startup. Apply future migrations with `docker compose exec backend alembic -c infrastructure/alembic.ini upgrade head`. If an initial schema was auto-created without the Alembic version record, verify the schema and stamp the initial revision as documented in database.md.

`runtime/` is mounted for media, evidence and models; PostgreSQL has a named volume. Source secrets are environment-only. The backend build installs CPU Torch from its official CPU wheel index before the vision extra. It is a relatively large image; network access is needed during build. Local production `npm start` copies the built static assets next to the standalone server and binds loopback (override FRONTEND_HOST only intentionally). The frontend image uses Next.js standalone output with the backend HTTP origin fixed to `http://backend:8000`; WebSocket is reached by the browser on local port 8000.

This is a local demonstration deployment. Internet operation requires TLS, COOKIE_SECURE=true, identity/session management, a reverse proxy with upload/timeouts, network/RTSP egress controls, robust distributed rate limiting, operational backup/retention and independent security review. Those are not claimed as implemented. Do not use multiple backend replicas/workers: each instance owns inference and live state.

Verification status is in PROGRESS.md. A valid Compose file or successful image-independent build does not prove containers were run.
