# Troubleshooting

- **Connecting / reconnecting:** start both servers; check `http://127.0.0.1:8000/api/v1/health`. Match CORS to the browser's exact host. HTTP polling continues if WebSocket is unavailable; set NEXT_PUBLIC_WS_URL for another port/HTTPS and rebuild.
- **401:** sign in using OPERATOR_TOKEN. Cookies for `localhost` and `127.0.0.1` differ; use the same hostname throughout. The token never goes in a URL.
- **No video detections:** install the vision extra and CPU Torch, run `make model`, inspect camera health/detail. Expected cold initialization can take several seconds. Ensure the video contains one of the six supported COCO classes. Blank/invalid files return 422.
- **File ended:** files deliberately play once. Press Start to replay; they are not silently looped because that would create false temporal continuity.
- **Source path rejected:** use uploaded `media:<generated-name>` or place videos inside runtime/media. Path traversal and arbitrary files are rejected. Re-enter the exact path when editing an existing video camera because source strings are redacted on reads.
- **RTSP rejected:** enable ALLOW_NETWORK_STREAMS explicitly and restart. RTSP credentials are never returned by camera endpoints; do not expose them in names/notes.
- **No incidents:** temporal thresholds must persist for real wall-clock seconds. A busy single frame is insufficient. Set an appropriate capacity and ROI, check confidence, and distinguish crowd/road mode. Simulation at 5× still waits for real persistence.
- **Forecast empty:** at least five current observations are required. Restart/source/ROI changes clear rolling windows. In-memory windows warm up after a backend restart.
- **Unreasonable long forecast:** linear extrapolation can overshoot. Shorten the horizon and inspect the historical trend/interval. These are estimates, not validated crowd predictions.
- **LLM unavailable:** no action needed; deterministic reports still work. Check LLM_PROVIDER/BASE_URL/MODEL/API_KEY only if optional advisory generation is intended.
- **SQLite locked or duplicate scenarios:** only one backend process is supported. Stop duplicate workers/processes. Do not use Uvicorn --workers. SQLite WAL and a 30-second busy timeout are configured.
- **Permission/cache errors:** use project-local venv and writable UV_CACHE_DIR/npm cache. Sandbox socket isolation may require host permission for integration tests/servers.
- **OpenCV libGL error:** install libgl1/libglib2.0-0 for full Ultralytics OpenCV, or use the headless-only synthetic install.
- **Docker daemon not available:** local Python/Node setup remains fully supported; Docker validation limits are documented in PROGRESS.md.
- **Secrets/network exposure:** restore loopback bindings; configure a token and TLS before any remote use. This repository includes no automatic external deployment.
