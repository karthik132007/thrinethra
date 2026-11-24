# AI models and experimental baselines

## Detection and tracking

YOLO11n uses pretrained COCO classes person, bicycle, car, motorcycle, bus and truck. Model execution is real Ultralytics inference, not class/color heuristics. ByteTrack associates detections over consecutive frames within the same camera; each worker owns a separate model/tracker. Detector confidence defaults to 0.30; inference resolution 640; sampling 2 FPS. `scripts/download_model.py` explicitly obtains weights from the upstream Ultralytics asset release, prints their SHA-256 and keeps them out of Git. Upstream model/code license: AGPL-3.0 or the applicable enterprise alternative. No demographic, face, appearance embedding or person re-identification model exists here.

Positions/boxes are normalized image coordinates. Velocity is image-plane displacement/second, never km/h. Histories are bounded to 60 positions per track and expire after 8 seconds absent. A centroid at the bottom of each box determines ROI inclusion. Perspective, occlusion, missed detections, tracker switches and sparse sampling limit all derived measurements. Dwell is bounded by the trajectory window, not a long-term identity record.

## Crowd and road intelligence

Crowd observations include object count, smoothed count over five observations, relative occupancy against configurable object capacity, growth, 4×4 spatial concentration, flow direction and conflict. Persistent high occupancy, low-motion localized bottlenecks and sustained sudden motion yield potential crowd-safety signals. No stampede or accident is confirmed. Capacity is an operator threshold in image-space objects; it is not measured people/m².

Road baselines use stationary duration, zone restrictions, count/occupancy and motion. A suspected road incident requires at least two recent abrupt trajectory decelerations within 12 seconds, elevated occupancy and reduced motion persisting over the threshold; overlapping boxes alone are never used. This cautious rule can miss real collisions and label ordinary traffic changes. A constant-image fixture cannot evaluate this hypothesis. Temporal tests include road positives and negatives, but no annotated natural accident dataset was used.

Defaults are experimental: 6 seconds signal persistence, 8 seconds stationary duration, 0.8 smoothed occupancy ratio, 30 second cooldown, 8 second event normalization. These values are configurable through Settings. Dismissal records false-positive feedback, but does not retrain the detector or automatically tune thresholds.

## Forecasting and risk

Rolling regression uses at least five and at most 60 observations to extrapolate nonnegative object counts. The horizon defaults to 60 seconds; configure 10–600 seconds. Intervals use regression residuals with a 0.5-object minimum residual and a normal 1.96 multiplier. They are approximate, not calibrated coverage claims. A linear capacity crossing is displayed only inside the forecast horizon. Extrapolation can overshoot, particularly near a phase transition.

Risk components: occupancy ≤35, persistence ≤15, growth ≤10, reduced movement ≤10, forecast pressure ≤20, nearby connected incidents ≤10. Scores sum and clamp to 0–100; high/critical cutoffs default to 50/75, elevated to 25. Confidence is separate and never called probability of danger. This score is an explanatory research heuristic, not a scientifically validated risk estimator.

## Investigation

LangGraph executes a read-only evidence retrieval/report workflow. Context includes incident metadata, related events, camera/ROI, recent stored observations, the forecast, risk components, retained evidence metadata and a configurable project-authored safety reference. Factual observation bullets are copied from a specific retained evidence snapshot and cite its exact ID. Possible explanations are hypotheses. Missing information and limits are explicit. The question field cannot grant tools or filesystem/database mutation.

`LLM_PROVIDER=none` is the default. `ollama` supports `/api/generate`; `openai` supports an OpenAI-compatible `/chat/completions` endpoint at the configured base URL. External providers see a bounded set of structured factors and the operator question, not video, source credentials or unrestricted database contents. Generated advice is labeled unverified, cannot change the deterministic facts and never triggers actions. Provider failure retains the deterministic report. External provider/CUDA behavior is not verified without a configured provider/GPU.
