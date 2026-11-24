# Local installation

Python 3.12 and Node.js 24 LTS are the tested major versions. `uv` can install Python with `uv python install 3.12`; standard `python3.12 -m venv .venv` and `.venv/bin/pip install -e '.[test,postgres]'` also work. On Debian/Ubuntu, real OpenCV/Ultralytics inference may need `libgl1` and `libglib2.0-0`. The synthetic-only backend uses headless OpenCV.

Follow the README setup and run commands. With `uv` caches in a restricted environment, set `UV_CACHE_DIR=/tmp/trinethra-uv` and `UV_PYTHON_INSTALL_DIR=/tmp/trinethra-python`. This is an environment-specific workaround, not needed for normal installs. Frontend uses a committed npm lock and `npm ci`. The base Python install uses the recorded requirements.lock as version constraints.

No paid APIs, model weights or network map tiles are needed for the synthetic demo. `make model` explicitly downloads YOLO11n into ignored `runtime/models/`. Install the `vision` extra and CPU Torch separately before real inference. Set `DEVICE=0` only with compatible CUDA Torch installed; CPU remains the default. No GPU throughput is claimed.

Required variables: none for local synthetic operation. `DEMO_MODE=false` requires a nonempty `OPERATOR_TOKEN`. PostgreSQL requires `DATABASE_URL=postgresql+psycopg://...`. The Compose setup additionally requires `POSTGRES_PASSWORD` in `.env`. Optional LLM variables are `LLM_PROVIDER`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY`; never commit `.env`. `RUNTIME_DIR` can isolate test media/evidence; the SQLite default path is independently controlled by DATABASE_URL. Keep paths within a trusted local workspace.

Backend: `make backend`, port 8000. Frontend: `make frontend`, port 3000. Frontend production: `make build` then `npm --prefix apps/frontend start`. For another backend origin, set `BACKEND_URL` during frontend startup/build and `NEXT_PUBLIC_WS_URL` at build time. Keep CORS origins exact.

Test: `make test typecheck build evaluate`. Browser checks: `cd apps/frontend && npx playwright install chromium && npm run test:e2e`. TestClient and browser runners require local loopback/event-loop sockets; isolated sandboxes may need a host execution permission. Tests use temporary SQLite/media directories. E2E tests reset disposable synthetic state.
