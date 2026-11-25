# Downloaded research inputs and permissions

All videos, weights, annotations and browser previews live in ignored runtime/. This repository redistributes none of them. The pinned source manifest is configs/assets.json; scripts/download_assets.py verifies SHA-256 and uses resumable ranges for large files. `make setup` installs and prepares the real default sources; `make assets` verifies/retrieves them independently.

- **Supervision publisher assets:** people-walking.mp4 and vehicles.mp4 from https://supervision.roboflow.com/latest/assets/ . The publisher supplies these for demonstrations. Local testing does not imply a general redistribution license; retain the source notice.
- **MOTChallenge:** official MOT17-04-FRCNN and MOT17-09-FRCNN raw moving preview videos and MOT17Labels.zip from https://motchallenge.net/data/MOT17/ . Used locally for research/development. The preview videos have half the original annotation width/height, so evaluation normalizes boxes against the original 1920×1080 annotation dimensions. Valid pedestrian class annotations, not synthetic labels, supply counting/matching targets.
- **EPFL CVLab multi-camera laboratory:** 4p-c0.avi and 4p-c1.avi, independent synchronized physical cameras, from https://www.epfl.ch/labs/cvlab/data/data-pom-index-php/ . The publisher explicitly permits research use. Copyright remains CVLab EPFL. Cite: F. Fleuret, J. Berclaz, R. Lengagne and P. Fua, “Multi-Camera People Tracking with a Probabilistic Occupancy Map,” IEEE TPAMI 30(2):267–282, 2008, DOI 10.1109/TPAMI.2007.1174. Calibration reference is downloaded for provenance; no physical speed/density or identity association is inferred.
- **Ultralytics:** YOLO11n and YOLO11s pretrained weights, upstream AGPL-3.0/applicable enterprise terms.
- **Qwen/Ollama:** Qwen2.5 1.5B Q4_K_M, downloaded into runtime/models/ollama. Ollama digest and real generation results are in docs/real-video-evaluation.md/evaluations/real-system-results.json. No paid provider is required.

The two default MOT views are non-overlapping crops of one recording and are labeled accordingly. The separate EPFL experiment uses genuinely different physical cameras. In both cases, detections/tracks/counts come from real model execution. The isolated EPFL capacity threshold is a test setting, not a validated physical room capacity.

The old bus.jpg repeated-frame smoke and generated scenario are historical/explicit regression fixtures. Neither is used as current natural-video evidence. Synthetic test data always carries synthetic provenance and never correlates with video-inference records.

User-uploaded footage is restricted to the media directory and decoded before use. Process only media you are authorized to use; do not upload or publish these datasets or people imagery without the required permissions.
