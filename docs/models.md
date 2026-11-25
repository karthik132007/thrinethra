# Models and measured intelligence

## Actual detection/tracking

CPU Torch and Ultralytics run pretrained YOLO11n, with YOLO11s also downloaded for comparison. The CPU default is nano at resolution 960, target source sampling 2 FPS and two Torch threads. This choice follows the actual development comparison in real-video-evaluation.md: nano/960 was faster and had lower night-crowd counting error than small/960, while small was better on some pedestrian metrics. No claim of universal superiority is made.

Model weights come from the publisher and are pinned in configs/assets.json. A running detector records the actual weight SHA-256, model name, backend, device, input size and confidence threshold with new observations/evidence. It never returns fixed detections. Classes are people, bicycles, cars, motorcycles, buses and trucks. Each worker owns its own ByteTrack instance; there is no appearance embedding, facial recognition, protected-attribute classification or cross-camera person association.

Boxes/foot positions are normalized image coordinates. Speeds are frame-coordinate displacement/second, never km/h. Position history is bounded and absent tracks expire; dwell keeps a separate first-seen timestamp. Sparse sampling, occlusion and low resolution cause misses and ID switches. Actual annotated results (including low dense-crowd recall) are reported rather than replaced by synthetic accuracy.

## Temporal analytics and risk

Measured counts, five-observation smoothing, occupancy against operator-configured object capacity, growth, concentration and directional coherence feed crowd rules. Signals require persistence, not a single busy frame. Road rules use stopping duration, configured restrictions, occupancy/motion and recent trajectory decelerations. A suspected incident is not an accident confirmation; bounding-box overlap alone is unused.

Default thresholds are experimental: 6 s persistence, 8 s stationary duration, 0.8 relative occupancy, 30 s cooldown and 8 s normalization. The risk score sums transparent bounded occupancy/persistence/growth/movement/forecast/connected-event factors to 0–100. Confidence is derived from detections and remains separate from severity; neither is a calibrated danger probability. Capacity is an image-space object threshold, not persons/m².

Explicit graph connections correlate aggregate event type/time/available flow. The default MOT views are disclosed crops. A separate EPFL experiment verifies distinct synchronized physical cameras. No GPS position, physical proximity or matching identity is invented for downloaded footage.

## Forecasting

At least five measured observations are required. Recent counts feed regression, last observation and exponential smoothing; after a sufficient window the model with lowest recent rolling one-step MAE is selected. Short windows warm up using regression. The UI displays the actual chosen method and estimated interval/crossing. Intervals are residual-based approximations, not validated safety coverage. Real sequences show that an adaptive model can still lose to last value on held-out future counts. The forecasts concern future detections, not guaranteed emergency outcomes.

## Real local investigation

Qwen2.5 1.5B Q4_K_M is downloaded to runtime/models/ollama and served locally at port 11435. It requires no paid key. LangGraph passes read-only incident details, related events, source/ROI context, actual historical observations, forecast/risk components, retained evidence and project-authored safety guidance. Canonical factual bullets come from one exact retained snapshot; model answers and hypotheses must cite allowed evidence IDs. JSON structure and reference existence are validated; unsupported consequential recommendations are rejected. Language interpretation still requires human review.

The browser starts a bounded background job and polls its status, so CPU generation can take tens of seconds without a proxy timeout. A missing/invalid model response produces an explicit evidence-only fallback. `LLM_PROVIDER=none` requests that fallback intentionally. OpenAI-compatible external providers are optional and unverified here; no paid provider is contacted by default. The agent has no shell, arbitrary filesystem or database-mutation tool and cannot dispatch or enforce anything.

No local model was trained on the test annotations; all model evaluations are development diagnostics with explicit limits. The project is functional research software, not a certified public-safety predictor.
