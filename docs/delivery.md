# Final delivery report

Trinethra is a working local research MVP: a Next.js/TypeScript command centre connected to a FastAPI/SQLAlchemy modular monolith, independent YOLO/ByteTrack video workers, temporal crowd/road baselines, an aggregate incident graph, regression forecasts, transparent risk and read-only LangGraph investigations. SQLite is the local default; PostgreSQL/Compose configuration is provided. Redis is unnecessary for the single-process MVP.

Implemented operator workflows: configure/upload/start/stop cameras; inspect anonymous tracks and ROIs; monitor camera health/map/zone measurements; search/filter incidents; inspect retained blurred evidence, relationships and risk factors; generate cited deterministic investigations; verify/dismiss/resolve with notes/audit; view historical forecasts; edit intelligence/zone settings; export actual data; run/reset an explicitly synthetic four-camera scenario. Core functionality needs no paid API key.

Verification: 22 Python tests, 4 Playwright tests, TypeScript and production build passed. SQLite migration applied; PostgreSQL SQL/Compose config validated. CPU detector smoke processed 12 real image frames with five stable track IDs; average warm inference was 108.58 ms (9.21 compute FPS), 437.8 MB RSS. HTTP upload/inference/persistence/frame integration produced five tracks and a first observation in 8.111 seconds including cold startup. A four-feed synthetic run measured 6.139 seconds persistence-to-event and 279.68 ms event-to-WebSocket delivery. Full results and scope: docs/evaluation.md.

Constructed synthetic benchmark: temporal event precision/recall 0.9487/0.9487 versus single-frame 0.8125/1.0 across 3,000 per-second samples. False-positive samples 40 versus 180. Regression forecast MAE/RMSE 1.773/2.130 versus last-value 2.254/2.792 across 520 synthetic forecast cases. Six labeled synthetic correlation pairs passed. These are not real-world accuracy claims.

## Installation

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -c requirements.lock -e '.[test,postgres]'
npm --prefix apps/frontend ci
cp .env.example .env
make migrate
```

For real inference, install CPU Torch and vision dependencies, then download the weights:

```bash
uv pip install --python .venv/bin/python torch torchvision --index-url https://download.pytorch.org/whl/cpu
uv pip install --python .venv/bin/python -e '.[vision]'
make model
```

## Startup and demo

```bash
make backend
# Separate terminal:
make frontend
```

Open http://127.0.0.1:3000; API docs http://127.0.0.1:8000/docs. Press Reset demo, use 2× or 5× playback, watch normal → influx → congestion, open the connected crowd incident, investigate, follow an evidence reference and record human verification/resolution. The simulation is conspicuously labeled and stops at 150 scenario seconds. For real inference, upload a permitted video in Surveillance; no natural CCTV footage is bundled. No deployment or remote push was performed.

Required environment: none for local synthetic demo. OPERATOR_TOKEN is required for DEMO_MODE=false and recommended for operator access. DATABASE_URL selects persistence; MODEL_PATH/DEVICE/SAMPLE_FPS/INFERENCE_SIZE configure vision. COOKIE_SECURE is available for HTTPS. Optional LLM_PROVIDER/BASE_URL/MODEL/API_KEY configure advisory-only output. Retention, evidence blur, trusted RTSP opt-in and exact CORS origins are documented in .env.example and docs/installation.md. Compose additionally requires POSTGRES_PASSWORD.

## Partial/blocked and optional work

Docker/PostgreSQL container execution is blocked by the unavailable Docker daemon; configuration/SQL checks passed. Webcam/RTSP hardware/credentials, CUDA and external LLM adapters were not exercised. Natural-video annotation-based detection/count/event accuracy and safety forecast lead time remain unmeasured; the real pipeline smoke uses repeated photographic imagery, not natural motion. No biometrics, person re-identification or enforcement exists. This is a single-process local research application with heuristic thresholds, approximate intervals, limited blur and a shared operator token. Named roles, hardened deployment, decoder isolation, natural footage evaluation, calibration and multi-source load testing are optional next steps.
