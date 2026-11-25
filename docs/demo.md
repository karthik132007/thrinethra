# Real-video demonstration

Run `make run`, then open http://127.0.0.1:3000. No paid key is needed. The default is SYNTHETIC_MODE=false; a green REAL VIDEO INFERENCE banner identifies the model and recorded source workflow.

1. Press Replay recordings. Source files are decoded once; cold initialization finishes before playback begins. Actual models produce boxes/classes/confidences/anonymous local IDs, counts and image-plane trajectories. Observe processed/dropped frame counts and source progress. Stop/Start a source independently.
2. Open Surveillance and inspect a camera. The annotated source frame is computed from original recording pixels. Expand source playback to see a browser-compatible WebM preview, original publisher URL, source SHA-256 and crop information. Downloaded recordings are not represented as live city cameras.
3. Review the source graph. The main MOT17 pair is explicitly two adjacent crops of one real recording; it is not falsely presented as two independent cameras. The other two clips have no invented spatial relation or GPS placement.
4. Open Intelligence: charts use real detector-derived observations. The baseline is selected from regression/last observation/exponential smoothing using recent validation, and its chosen method is displayed. Forecasts and capacity crossings are estimates, not guaranteed safety outcomes.
5. Inspect a measured sustained crowd-threshold incident. Normal footage may yield no road incident: no accident is fabricated. The configured image-space object capacity and temporal persistence explain why a condition appears.
6. Run investigation and ask a question. A bounded job queue shows generation progress while local Qwen reasons over retained structured evidence. Inspect factual snapshot citations, model-generated hypotheses, missing information and human review steps. A provider failure is explicit and retains evidence-only reporting.
7. Verify/dismiss/resolve with a note. Timeline/audit records update; no services are dispatched, no identities inferred and no enforcement occurs.

## Independent physical-camera experiment

The official EPFL laboratory sequence was downloaded from its publisher under the stated research permission. Two different synchronized camera files are processed through the same detector, temporal engine, event store and correlation graph:

```bash
.venv/bin/python evaluations/physical_cameras.py
```

This uses an isolated SQLite database under runtime/, so it does not change operator cameras/history. It uses an explicitly low 3-object threshold to exercise the mechanics with up to four laboratory participants. The outputs are actual measured counts, event evidence and aggregate correlations, not a claim that four people constitute a safety emergency. Exact results are in evaluations/physical-camera-results.json and docs/real-video-evaluation.md.

## Synthetic regression fixture

Generated trajectories are retained only for deterministic testing: launch a separate backend with SYNTHETIC_MODE=true and a separate DATABASE_URL. E2E_SYNTHETIC=1 selects its isolated browser suite. These tests cannot establish real-video accuracy and are not the default demo.
