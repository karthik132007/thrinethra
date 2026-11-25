# Real moving-video evaluation — 25 November 2026

This report supersedes the earlier repeated-photograph and synthetic demonstrations for natural-video verification. Measurements below come from fresh pretrained-model inference on actual moving recordings. Source files, model weights and labels were downloaded locally; none are redistributed in Git.

## Inputs and reproducibility

`configs/assets.json` records publisher URLs, SHA-256 and size for four initial natural-motion videos, MOT17 training labels and YOLO11 nano/small weights. The Supervision videos are publisher-provided demo assets. MOTChallenge raw preview sequences and labels come from its official archive. Their decoded frame counts match the declared sequence lengths: MOT17-04 1,050 frames/35 s, MOT17-09 525 frames/17.5 s, pedestrian clip 341 frames/13.64 s, traffic clip 538 frames/~21.52 s. Each input changes at the pixel level; these are not repeated photographs.

```bash
make setup
make real-evaluate
# Compare higher-resolution inference:
.venv/bin/python evaluations/real_video.py --models yolo11n.pt --assets mot04 mot09 --size 960 --output real-video-nano-960-results.json
.venv/bin/python evaluations/real_video.py --models yolo11s.pt --assets mot04 mot09 --size 960 --output real-video-960-results.json
```

The default script compares two models on four videos (358 sampled frames in total across both models). The two extra resolution comparisons each process 105 frames. Sampling is approximately 2 FPS; raw videos are decoded sequentially and the detector/tracker sees real selected frames. These are development diagnostics, not a blinded benchmark or official MOTChallenge submission.

## Annotated counting/detection results

Ground truth includes MOT records with valid flag 1 and pedestrian class 1, **all visibility levels**. Official preview videos are 960×540 while annotations are 1920×1080; normalized boxes preserve alignment. Assignments use IoU≥0.5. Ignored/distractor regions are not suppressed. Preview compression and sparse sampling affect the results. Precision/recall here is per matched sampled box, not mAP. Counting error compares actual tracked detections against the annotated person count.

| Sequence | Model / size | Precision | Recall | Count MAE | Mean inference ms |
| --- | --- | ---: | ---: | ---: | ---: |
| MOT17-04 night crowd | YOLO11n / 640 | 0.9008 | 0.2152 | 34.414 | 41.881 |
| MOT17-04 night crowd | YOLO11s / 640 | 0.8696 | 0.1918 | 35.243 | 122.349 |
| MOT17-04 night crowd | YOLO11n / 960 | 0.8734 | 0.3662 | 26.257 | 98.518 |
| MOT17-04 night crowd | YOLO11s / 960 | 0.8955 | 0.3384 | 28.129 | 199.010 |
| MOT17-09 pedestrians | YOLO11n / 640 | 0.7963 | 0.4886 | 4.000 | 41.001 |
| MOT17-09 pedestrians | YOLO11s / 640 | 0.8102 | 0.4972 | 4.000 | 104.432 |
| MOT17-09 pedestrians | YOLO11n / 960 | 0.8341 | 0.4858 | 4.257 | 95.362 |
| MOT17-09 pedestrians | YOLO11s / 960 | 0.7200 | 0.5114 | 3.029 | 177.788 |

**The detector misses many small/occluded people, especially in the night crowd.** These results do not support a claim of reliable crowd counting or safety prediction. Nano/960 is the CPU default because it had lower night-crowd counting error and roughly half the compute latency of small/960 in this development comparison. Small remains downloaded and selectable via MODEL_PATH. More resolution/model size does not uniformly improve accuracy.

At two sampled frames/second, tracking IDs can switch considerably. The JSON records sampled assignment switches, not official HOTA/MOTA/IDF1. Do not interpret anonymous local ID continuity as established identity accuracy. No re-identification is used.

## Forecasting on real measured counts

The first real-video pass showed that a regression extrapolation was often worse than carrying forward the last measured count. The forecasting module now compares rolling one-step errors for regression, last observation and exponential smoothing, and selects a baseline from current measurements after a sufficient window. Short windows explicitly warm up with regression.

Examples from the higher-resolution pass, predicting future **detector-derived counts**, not ground-truth danger:

| Sequence / model | Selected model MAE | Last-value MAE | Cases |
| --- | ---: | ---: | ---: |
| MOT17-04 / nano-960 | 2.398 | 2.362 | 58 |
| MOT17-09 / nano-960 | 1.542 | 1.652 | 23 |
| MOT17-04 / small-960 | 2.102 | 2.138 | 58 |
| MOT17-09 / small-960 | 1.198 | 1.478 | 23 |

Adaptive selection is not guaranteed to beat the last-value baseline, as the night-crowd result shows. There is no claim of calibrated prediction intervals or accident/stampede prediction lead time.

## End-to-end application checks

`scripts/verify_real_system.py` checks the running app through HTTP: real-profile configuration, changing counts and nonzero track movement for every source, persisted video-inference observations, annotated JPEGs, ranged source playback, actual temporal incident generation, retained evidence, a real local Qwen investigation with valid citations and human verification/resolution.

The initial completed real application pass used small/960. Per-source observed counts varied: east 4–11, pedestrian crossing 6–31, road 0–5, west 12–21. Four concurrent source workers were materially slower than isolated model measurements (mean compute roughly 0.85–1.15 s in that pass); bounded queues dropped old frames. This is why measured per-camera compute, processing counts and drops are visible. This initial small/960 pass is preserved in `evaluations/real-system-results.json`; the later browser acceptance run exercises the final nano/960 default. Do not infer multi-camera throughput from isolated inference FPS.

A downloaded Qwen2.5 1.5B Q4_K_M model (986,061,892 bytes; Ollama digest `65ec06548149b04c096a120e4a6da9d4017ea809c91734ea5631e89f96ddc57b`) produced an evidence-grounded operator answer in 22.944 seconds in the first real system pass. Model interpretation is labeled as hypothesis; exact reference IDs are validated. The UI uses bounded asynchronous investigation jobs so slow CPU generation does not depend on the frontend proxy holding one request open.

Reports and browser screenshots are actual outputs in `evaluations/real-system-results.json`, `evaluations/playwright-results.json` and `docs/screenshots/real-*.jpg`. Required unit/type/build checks and final browser status are listed in PROGRESS.md; development failures are not counted as passing verification.

## Spatial relationships and remaining verification boundaries

The main four-source interface deliberately identifies the linked MOT17 views as adjacent crops from one real recording. Their layout positions are not verified GPS. The two unrelated publisher recordings have no invented spatial connection. The cross-camera engine does not match identities. A separate experiment now processes two actual synchronized EPFL laboratory cameras (3,915 frames each at 25 FPS). It generated **4 measured threshold incidents, 3 aggregate event relationships and 11 evidence snapshots** using the unchanged application engine. Mean isolated inference was **77.689 ms**; offline processing took **61.905 s**. The experiment uses an explicit 3-object test threshold and does not claim that the laboratory scene is dangerous. It matches no identities. Image-flow directions from these uncalibrated camera coordinate systems are not compared; direction comparison requires a shared coordinate frame. Recording-time processing is not a wall-clock alert-latency measurement. Full observations and source hashes are in evaluations/physical-camera-results.json; publisher permission and citation are in datasets/README.md.

Road footage contains ordinary traffic, not labeled collisions. Road anomaly rules are implemented and unit-tested, but no accident-recognition precision/recall or real emergency outcome is established. Webcam/RTSP and CUDA require available hardware/credentials. Docker runtime remains unavailable on this host because its daemon/socket is missing; configuration checks do not imply container execution. Risk and object capacity are operator-configured experimental thresholds, not scientifically validated safety limits.
