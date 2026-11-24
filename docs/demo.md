# Hackathon demonstration

No paid keys or CCTV access required. Start both services, open http://127.0.0.1:3000 and press Reset demo. The amber SIMULATION bar and source badges explicitly identify synthetic measurements. Four virtual camera coordinates and connectivity edges are seeded from configs/cameras.yaml; the map is a fictional campus near the demo city coordinates.

1. **Normal monitoring (scenario 0–15 s):** inspect camera health and camera-local IDs. Point out object capacity is an image-space threshold, not people/m².
2. **Increasing influx (15–42 s):** watch East concourse and Transit plaza counts rise with a configured delay. Historical points feed the actual forecasting module; no chart series are hand-authored.
3. **Congestion (42–95 s):** temporal persistence opens potential crowd-safety incidents; road actors stop in a restricted region. Highlight candidate waiting, risk factors and separate confidence.
4. **Cross-camera reasoning:** open a crowd incident and inspect its linked incident graph. Explain connectivity, compatible event types and onset proximity. No people are matched across cameras.
5. **Prediction:** open Intelligence. Show actual recent synthetic observations, rolling regression, interval and possible capacity crossing; emphasize uncertainty.
6. **Investigation:** select an incident and press Investigate incident. The read-only LangGraph workflow produces grounded observations with exact evidence references, hypotheses, missing information and human review steps. No LLM key required.
7. **Human oversight:** enter a note and mark Under Review, Verified, Dismissed or Resolved. Inspect the lifecycle timeline. No real response is dispatched.
8. **Recovery (95–150 s):** watch occupancy fall; at completion virtual feeds become empty and persistent conditions automatically resolve after normalization. Closed records remain inspectable.

2× is a readable default; 5× produces a compact ~30-second scenario plus real-time persistence. Pause freezes synthetic observations; real video sources keep processing. Reset clears only synthetic generated records and preserves audit history/video-derived records. Scenario time restarts on backend launch; persisted records survive until reset.

For real inference, use Surveillance → Add camera → Upload video, with footage you are authorized to process. Set an appropriate ROI/capacity. The source badge changes to VIDEO INFERENCE. No natural surveillance footage is bundled. The optional smoke fixture encodes a repeated real photograph solely to verify decoding/inference/tracking; do not present it as real crowd movement or accident validation.
