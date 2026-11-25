# Presentation outline and technical innovation

1. **Problem:** passive CCTV supplies images but leaves operators to connect conditions across feeds.
2. **Approach:** connect short-lived local trajectories, temporal observations, graph relationships, forecasts and cited evidence. Human operators retain decisions.
3. **Architecture:** show the Mermaid diagram; explain bounded per-camera workers and a single state/persistence owner suitable for a student laptop.
4. **Technical differentiators:** temporal suppression of transient crowd spikes; multi-signal road baselines; no-identity event graph; interpretable forecast/risk components; provenance-preserving LangGraph investigation.
5. **Live demonstration:** normal → influx → congestion → connected incident → forecast → cited report → human review → normalization.
6. **Research evidence:** show the real annotated MOT17 comparisons and physical EPFL camera experiment from docs/real-video-evaluation.md. Show the measured misses and forecast errors alongside working integration. Historical synthetic tests are opt-in regression fixtures.
7. **Responsible design:** no biometrics, individual risk or enforcement; default evidence blur with known limitations; access control, audit and retention.
8. **Limitations and next experiments:** higher-recall crowd detection, independently labeled road incidents, multiple camera calibration, prediction interval calibration, stronger road models, multi-source GPU/CPU profiling, decoder isolation and named-operator roles.

The innovation is the traceable combination of aggregate observations and cross-camera hypotheses, not a claim of a new detector or a reliable accident/stampede prediction model. YOLO and ByteTrack are established pretrained/tracking components; the original project work is their integration into temporal analytics, provenance-aware incident lifecycle, regional reasoning and evidence-grounded operator workflows.
