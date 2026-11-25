# Trinethra — real-video delivery status

Updated 25 November 2026. Default application is real moving-video inference; synthetic fixtures are opt-in only. No remote push or deployment.

## Completed implementation

- Downloaded six real recordings: pedestrian/traffic publisher clips, MOT17-04/MOT17-09, and two different synchronized physical EPFL laboratory cameras. Downloaded real MOT17 annotations and EPFL calibration provenance. All source URLs, sizes, permissions and SHA-256 values are recorded in configs/assets.json; raw assets remain ignored.
- Downloaded YOLO11 nano/small pretrained weights and Qwen2.5 1.5B Q4_K_M (986 MB). CPU Torch/Ultralytics/ByteTrack are installed. Persistent project model/browser directories avoid temporary-interpreter/cache dependence.
- Default source setup uses original recordings, actual detector outputs, camera-local tracking, measured motion/counts, temporal crowd/road rules, event evidence, forecasts and audited review. No model/source failure substitutes generated data.
- Model initialization precedes playback; bounded queues drop stale frames under load; EOF drains inference and exits threads; camera errors are isolated; replay starts a fresh tracking/observation run. Dwell duration is independent of the bounded trajectory deque.
- Original-source inspection includes browser-compatible WebM playback, publisher attribution and verified hashes. Default source graph explicitly marks layout positions as unverified geography and crops as crops.
- Forecasts select among three interpretable baselines using rolling validation on measured counts. The actual method/errors/uncertainty are reported; no forced regression improvement claim.
- Local Qwen answers operator questions and produces structured, cited hypotheses/review steps through read-only LangGraph context. Facts remain exact retained snapshot factors. Bounded asynchronous jobs avoid frontend timeouts; fallback/model failures are explicit.
- Real HTTP/video/incident/model/review integration verified; source credentials stay redacted. Input source is preserved on metadata-only camera edits. Model name/hash/device/resolution/confidence are attached to new real observations/evidence.
- Existing persistence/authentication/API/camera/ROI/incident/settings/export/privacy/retention and six frontend views remain functional. Synthetic regression fixtures require SYNTHETIC_MODE=true and are separated from the default real profile.
- Installation downloads/verifies inputs and prepares playback previews; resumable ranges support large publisher files. `make run` launches the local app and optional local model. Docker includes local Ollama configuration; CI uses actual video assets. Browser tests isolate ports/database from operator-controlled sources.

## Actual verification

- 33 Python tests passed in 50.16 s, covering real ingestion, model metadata, background jobs, asset integrity and camera-coordinate boundaries.
- 3 real-video Playwright tests passed in 61.96 s, with zero unexpected/flaky cases. They verify real defaults/no simulation, actual frames, source-video metadata playback, model job completion, evidence citations, human verification and 390 px mobile controls. Test services use 3001/8001 and a separate database, preserving operator choices in the normal app.
- `make typecheck` and `make build` passed. SQLite migration tested previously; PostgreSQL SQL and Compose configuration validated.
- Initial real system integration verified all four sources and local Qwen with retained evidence citations, plus verify/resolve. Current actual report is evaluations/real-system-results.json; its first recorded model configuration is small/960, explicitly separate from the final nano/960 CPU default.
- Fresh detector comparison: 358 sampled frames across four natural clips/two models at 640; additional nano/small 960 comparisons each used 105 annotated frames. Full observations, errors and source hashes are committed as JSON, not invented summary metrics.
- MOT17-04 night crowd: nano/960 measured precision 0.8734, recall 0.3662 and count MAE 26.257. Dense/occluded people are substantially missed; this is a limitation, not a passing safety-accuracy claim.
- Independent physical-camera experiment: two publisher-synchronized EPFL cameras, 3,915 frames each, 327 inferred samples per view; the same engine produced 4 measured test-threshold incidents, 3 aggregate correlations and 11 evidence snapshots. The 3-object capacity is an explicit low mechanical test threshold, not a dangerous-room claim. Offline processing took 61.905 s; it is not wall-clock alert latency.
- Screenshots of actual recordings/reports are docs/screenshots/real-*.jpg. Earlier generated/repeated-photo results remain labeled historical and are not current natural-video evidence.

## External limits and scientific boundaries

Docker daemon/socket is unavailable, so container builds/PostgreSQL runtime could not be exercised. Physical webcam/RTSP credentials and CUDA hardware were unavailable. No labeled real collision evaluation or calibrated safety forecast exists. Counts, risk thresholds and approximate intervals remain experimental; sparse-frame tracking switches and false/missed alerts are possible. Camera GPS and physical crowd density/speed are not inferred. Model citations validate reference existence, not semantic truth. Evidence blur is upper-box based, not guaranteed anonymization. Named-user authorization, Internet hardening, decoder isolation and multi-replica operation remain outside this local research deployment. No biometrics, re-identification, individual threat scores or autonomous enforcement are implemented.
