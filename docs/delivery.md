# Delivery — real moving-video revision, 25 November 2026

Trinethra now defaults to actual pretrained model inference on downloaded moving recordings. Synthetic trajectories are opt-in regression fixtures. The application includes independent camera workers, YOLO/ByteTrack observations, temporal crowd/road rules, persisted incidents/evidence, aggregate relationships, measured-count forecasts, real local Qwen investigations and human review.

Downloaded locally: six real clips (including two distinct synchronized EPFL cameras), MOT17 annotations, calibration provenance, YOLO11 nano/small and Qwen2.5 1.5B. Source permissions and SHA-256 are preserved; no raw footage/weights enter Git. Camera layouts and crop relationships are honestly identified rather than shown as verified city surveillance locations.

Verified: 33 Python tests, three real-video browser tests (61.96 s), TypeScript and production build. Natural-video model comparison used 358 sampled frames at 640, with 105-frame higher-resolution runs for each model. The physical-camera integration processed 327 samples per camera and produced four threshold incidents, three aggregate correlations and eleven evidence snapshots. The explicit three-object test capacity is not a claim of danger. Local Qwen completed an evidence-cited operator answer on a real incident; asynchronous jobs fix long CPU-response proxy timeouts.

Real shortcomings are measured: nano/960 night-crowd recall was 0.3662 with count MAE 26.257; the model misses small/occluded people. Sparse tracking can switch IDs. Forecasting is not uniformly better than last value. Full results: real-video-evaluation.md and evaluations/*.json. No accident/stampede accuracy or guaranteed safety lead time is claimed.

## Start this installed checkout

```bash
make run
```

Open http://127.0.0.1:3000 and press Replay recordings. Inspect a camera, play the source preview, review measured counts/forecasts, investigate a retained incident, follow its evidence citations and record human verification/resolution. Source files play once; operators can stop/restart sources independently.

## Fresh setup

```bash
make setup
cp .env.example .env
make migrate
make browser-install
make llm
# Another terminal while that local service runs:
make llm-model
# Then:
make run
```

Python must live in a persistent location; environment repair guidance is in installation.md. No required paid credentials. SYNTHETIC_MODE defaults false. DEMO_MODE controls local no-token access only; OPERATOR_TOKEN is required outside that local demo mode. MODEL_PATH/INFERENCE_SIZE/SAMPLE_FPS/TORCH_THREADS configure actual inference. Default LLM_PROVIDER=ollama uses the downloaded model; none explicitly disables generation. API docs are at http://127.0.0.1:8000/docs.

Reproduce checks with `make test typecheck build e2e`, natural inference using `make evaluate`, independent-camera correlation using `make physical-evaluate`, and real HTTP/model checks using scripts/verify_real_system.py against an isolated instance with all default sources enabled. Browser tests use separate ports/database and preserve operator-controlled application state.

Docker configuration includes PostgreSQL and local Ollama, but Docker execution is blocked by the missing daemon on this host. Webcam/RTSP hardware/credentials and CUDA were unavailable. Named-user/Internet hardening, decoder sandboxing and multi-replica operation remain future operational work. No identification, biometric inference, cross-camera person matching, individual threat scoring, enforcement or autonomous dispatch exists.
