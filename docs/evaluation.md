# Historical synthetic/initial smoke evaluation — 24 November 2026

**Superseded for natural-video verification by [Real moving-video evaluation](real-video-evaluation.md).** This document preserves the original measurements and does not describe the current default recording workflow.

These are recorded results from this workspace, not performance targets or real-world safety guarantees. Machine: AMD Ryzen 5 5500U, x86-64, 12 logical CPUs, approximately 14 GiB RAM. Python 3.12.11; CPU Torch/YOLO versions are recorded in requirements.lock. The host was shared with development/browser processes; no GPU was measured.

## Automated verification

- **22 Python unit/API/integration tests passed** (final behavioral run: 20.29 s). Coverage includes temporal spike suppression, crowd and road signals, recent deceleration memory, tracking expiry, forecast fitting, provenance/connectivity/proximity correlation constraints, incident creation/deduplication/resolution, evidence grounding, retained-evidence expiry, operator authentication/review, settings validation, source-path restrictions, upload rejection, independent bounded camera workers and WebSocket snapshots.
- **4 Playwright tests passed** (recorded production-server run: 21.1 s). Tests cover map/camera selection, actual JSON export, synthetic correlation → cited investigation → verification/resolution, camera inspection, forecasts, ROI controls, saved settings and 390 px mobile workflows. Earlier development failures were fixed; evaluations/playwright-results.json records the passing run.
- TypeScript checking passed; the Next.js production build passed. Final build status is also recorded in PROGRESS.md.
- SQLite Alembic migration applied successfully to an empty test database. PostgreSQL migration SQL rendered successfully (208 lines); Compose configuration validated. **PostgreSQL containers and Docker images were not run:** Docker is installed but its daemon/socket is unavailable.

Browser screenshots: docs/screenshots/command-centre.jpg, investigation.jpg and mobile-surveillance.jpg. Screenshots show clearly labeled synthetic data.

## Synthetic temporal event comparison

Reproduce: `.venv/bin/python evaluations/run.py`. Seed 42, 20 constructed 150-second episodes, 3,000 per-second samples. Episodes contain ordinary counts, isolated spikes, sustained high occupancy and recovery. Positive labels start six seconds after sustained high occupancy begins. The detector is bypassed. These are **sample-level precision/recall**, not incident-level accuracy on natural videos.

| Method | Precision | Recall | False-positive samples | False-negative samples |
| --- | ---: | ---: | ---: | ---: |
| Single-frame occupancy threshold | 0.8125 | 1.0000 | 180 | 0 |
| Smoothed temporal crowd baseline | 0.9487 | 0.9487 | 40 | 40 |

Mean detection delay from sustained high occupancy onset: **8.0 seconds**. Smoothing suppresses short spikes and adds detection delay; trailing smoothing also retains some positive samples after the constructed recovery boundary. The benchmark illustrates this tradeoff. It does not establish real-world precision or recall.

Six hand-labeled synthetic correlation pairs (two positive, four negative) yielded precision/recall 1.0/1.0. This tiny, intentionally constructed suite verifies graph, timing, type and provenance rules; it cannot establish generalization or operational correlation accuracy. Additional tests reject geographically distant connected cameras.

## Synthetic forecasting comparison

520 rolling-window forecast cases, 10-second horizon, seeded noisy trend/sinusoid data. All methods see only the preceding observations; targets are held out in time. Multiple rolling samples overlap, and the series is synthetic. Object counts are in arbitrary image-space units.

| Baseline | MAE (objects) | RMSE (objects) |
| --- | ---: | ---: |
| Last value | 2.254 | 2.792 |
| Five-sample moving average | 2.361 | 2.910 |
| Exponential smoothing, α=0.3 | 2.386 | 2.942 |
| Rolling linear regression | 1.773 | 2.130 |

Regression performed better on this particular benchmark, justifying its MVP use. No calibrated coverage, natural crowd forecast lead time or comparison with a trained deep model is claimed. Dashboard forecasts use actual current observations from the inference/simulation pipeline, not these benchmark values.

## Real image/video pipeline smoke

Reproduce using datasets/README.md, then `scripts/vision_smoke.py` and, with the local backend running, `scripts/video_api_smoke.py`. The input is an upstream real photograph encoded as a repeated-frame MJPEG video. **It has no natural scene dynamics and no ground-truth annotations.** No image/video is committed.

- 12 real YOLO frames processed; people and bus detected.
- Five ByteTrack IDs stable across all 12 repeated frames.
- First frame: **6,513.38 ms**, including cold initialization.
- Mean inference after first frame: **108.58 ms** → **9.21 inference FPS** at size 640 on CPU.
- P95 after first frame: **306.53 ms**. These are 11 warm samples, not a load test.
- Standalone inference process RSS: **437.8 MB**; process CPU during the run: **238.9%** (multi-core process accounting; 100% represents one logical core).
- HTTP upload/decoder/worker/persistence/annotated-frame smoke succeeded: five tracks, 89,135-byte annotated JPEG, first observation **8.111 s** after source configuration including cold startup.
- Selected stored observation: **77.33 ms** inference; **498.32 ms** queue-to-result time. These are individual sampled observations, not averages.
- Backend RSS during uploaded-video smoke: **489.2 MB**.

The bounded queue can drop frames during cold loading. Sampling is configured at 2 FPS; 9.21 FPS compute throughput is not a claim of 9.21 FPS source ingestion or multi-camera throughput. The default smoke checks source decoding and stable IDs, not tracking identity accuracy under motion/occlusion.

## Live synthetic alert timing

Reproduce with `scripts/measure_demo.py`; this resets disposable synthetic state. Four virtual feeds, 5× scenario playback, 15 WebSocket samples:

| Measurement | Observed |
| --- | ---: |
| Smoothed threshold crossing → incident creation | 6.139 s |
| Evidence capture → event processing | 22.77 ms |
| Incident creation → WebSocket receipt | 279.68 ms |
| Mean engine tick | 86.19 ms |
| Maximum engine tick | 116.95 ms |
| Backend RSS (after earlier model smoke) | 487.7 MB |
| Process CPU since previous health sample | 10.4% |
| System CPU at sample | 38.9% |

The six-second delay is intentional persistence, separate from processing and delivery. WebSocket receipt is measured; browser paint latency is not. CPU/system measurements are short shared-host samples and are not utilization guarantees. GPU utilization was not measured. These timings describe synthetic analytics, not end-to-end natural-video danger recognition.

## Investigation grounding

Integration tests assert every deterministic factual observation exactly matches the retained evidence snapshot's factors and cites that snapshot's ID. With no evidence, the report produces no factual observation bullets and explicitly reports missing evidence. Source labels and missing ground confirmation are preserved. This checks reference integrity, not correctness of the detector, real-world explanation validity or hallucination rates of external LLMs. Optional provider failures retain the deterministic report; live Ollama/paid providers were not tested.

## Not evaluated / next experiments

Detection mAP, natural crowd-count MAE, accident precision/recall, false alerts/hour on natural footage, genuine predictive safety lead time, interval coverage and regional event causality remain unmeasured. Next work should use permitted annotated clips, camera calibration, held-out incident labels and longer CPU/multi-source stress tests. Add decoder process isolation and deployment security validation before any operational trial. Never interpret these constructed benchmarks as evidence that the system can reliably predict accidents or stampedes.
