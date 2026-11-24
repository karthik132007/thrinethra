Run `.venv/bin/python evaluations/run.py` to recreate results.json from seed 42. This constructed synthetic benchmark compares per-second crowd-alert labels, four forecasting baselines and six explicit correlation pairs. It bypasses the detector and cannot measure natural video performance.

For actual inference throughput, supply runtime/media/bus.jpg as documented in datasets/README.md and run scripts/vision_smoke.py. That script writes vision-results.json and a repeated-photograph video. With the local backend running, scripts/video_api_smoke.py uploads that clip, temporarily replaces the disposable synthetic cam-04, checks observed tracks/JPEG output and restores the synthetic source; it writes pipeline-results.json. Do not run that smoke if cam-04 is a personal/operational source. These scripts do not calculate detection mAP or road/crowd event accuracy.

Playwright writes playwright-results.json. Stored values describe the actual recorded test run; timing and throughput will vary by hardware/load. See docs/evaluation.md for interpretation and limitations.

`scripts/measure_demo.py` measures synthetic threshold-to-event delay, evidence-to-event processing and WebSocket delivery separately, and writes demo-performance.json. It resets the disposable synthetic scenario. Browser paint and natural-video incident latency are not measured.

The HTTP/WebSocket smoke scripts assume the default local DEMO_MODE=true environment without an operator token. Browser and API integration tests separately verify authenticated access.
