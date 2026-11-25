# Reproducible evaluations

- `make evaluate` / `make real-evaluate`: fresh natural-video YOLO/ByteTrack inference on downloaded pedestrian/traffic inputs, plus actual MOT17 annotations and forecasts on measured counts. Writes real-video-results.json.
- `evaluations/real_video.py --models yolo11n.pt --assets mot04 mot09 --size 960 --output real-video-nano-960-results.json`: CPU resolution/model comparison; small variant is also recorded.
- `make physical-evaluate`: separate synchronized physical EPFL cameras through the same temporal/event/correlation engine in an isolated SQLite store. Recording-time offline experiment, not measured real-time delivery latency. Writes physical-camera-results.json.
- `scripts/verify_real_system.py --url http://127.0.0.1:8000/api/v1`: checks every configured recording, actual observations/trajectories, source playback, evidence, local Qwen and operator review. It requires all four default recording cameras enabled; use an isolated instance when an operator has intentionally stopped a source.
- `make e2e`: isolated real-video browser workflow on ports 3001/8001, including actual playback metadata and background investigation. Writes playwright-results.json and docs/screenshots/real-*.jpg.
- `make synthetic-evaluate`: historical constructed baseline comparison, explicitly synthetic and detector-bypassed. results.json is not natural-video accuracy.

Older vision-results.json/pipeline-results.json use the repeated-photograph fixture; demo-performance.json uses generated trajectories. They are retained as historical evidence, not default data or natural-motion validation. See docs/real-video-evaluation.md for current measurements and their limits.
