# Local installation

Python 3.12+, Node.js 24 LTS, `uv`, FFmpeg and (for local generative investigation) Ollama. CPU inference is supported. The default workflow is real recorded video, not synthetic simulation.

```bash
make setup
cp .env.example .env
make migrate
make browser-install
```

`make setup` creates the venv, installs CPU Torch/YOLO and application/test dependencies, installs frontend dependencies, verifies/downloads publisher video/model assets and generates browser-compatible WebM previews. All large files remain in ignored runtime/. Source hashes and permissions are recorded in configs/assets.json and datasets/README.md. Depending on connectivity, downloading models/data can take several minutes.

With `uv` caches in a restricted environment, `UV_CACHE_DIR=/tmp/trinethra-uv` can be used as an environment-specific workaround. Do not put `UV_PYTHON_INSTALL_DIR` in a temporary directory: `.venv` links to its base interpreter, so removing that directory leaves `.venv/bin/python` dangling. Keep the Python installation in uv's normal persistent location or configure a persistent directory. Frontend uses a committed npm lock and `npm ci`. The base Python install uses the recorded requirements.lock as version constraints.

If `make backend` reports that `.venv/bin/python` does not exist even though that path is present, check whether it links to a removed interpreter. Ensure `UV_PYTHON_INSTALL_DIR` is unset or points to a persistent directory, then recreate the environment and reinstall its dependencies:

```bash
uv python install 3.12
uv venv --python 3.12 --clear .venv
uv pip install --python .venv/bin/python torch torchvision --index-url https://download.pytorch.org/whl/cpu
uv pip install --python .venv/bin/python -c requirements.lock -e '.[vision,test,postgres]'
```

The actual local model download is separate from source code installation:

```bash
make llm
# Another terminal, while that service is running:
make llm-model
```

This downloads Qwen2.5 1.5B Q4_K_M (~986 MB) into runtime/models/ollama. It does not require a paid key. `make run` then starts backend, frontend and, if needed, that local model service together. Separate commands are `make backend`, `make frontend`, `make llm`. Open http://127.0.0.1:3000; API explorer http://127.0.0.1:8000/docs. Recording playback starts once, then use Replay recordings or a camera's Start button to replay with new tracking state. Starting an already-running service on its port will fail; stop the previous project process first.

Required environment variables: none for loopback real-recording operation after setup. SYNTHETIC_MODE defaults false. DEMO_MODE only permits local no-token access; false requires OPERATOR_TOKEN. Set COOKIE_SECURE=true behind HTTPS. DATABASE_URL defaults to SQLite; PostgreSQL uses `postgresql+psycopg://...`. LLM_PROVIDER defaults ollama at http://127.0.0.1:11435 with the downloaded model; none explicitly disables generation. An unavailable model produces a clearly labeled evidence-only fallback, not fake model output. MODEL_PATH/INFERENCE_SIZE/SAMPLE_FPS/TORCH_THREADS control detector execution. RUNTIME_DIR isolates media/evidence and does not independently change DATABASE_URL.

For GPU execution install an appropriate CUDA Torch build and set DEVICE=0. CUDA was not available for local verification. Webcam uses webcam:0; RTSP requires trusted camera credentials and ALLOW_NETWORK_STREAMS=true. No network stream or paid provider is contacted by default.

Verify with `make test typecheck build e2e`, `make real-evaluate` and, against the running local system, `.venv/bin/python scripts/verify_real_system.py`. The default browser suite uses real video. Explicit synthetic fixtures use a separate database and SYNTHETIC_MODE=true/E2E_SYNTHETIC=1.
