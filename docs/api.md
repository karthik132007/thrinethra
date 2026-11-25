# API

Run the backend, then inspect `/docs` or `/openapi.json` for generated schemas and input constraints. The default origin is http://127.0.0.1:8000. All data routes use `/api/v1`. Responses contain UTC Unix timestamps (seconds), normalized image coordinates and camera-local track IDs.

Authentication: set `OPERATOR_TOKEN`, then send `Authorization: Bearer <token>` or POST `{"token":"..."}` to `/auth/session` for an HttpOnly SameSite=Strict cookie. No authentication is required only when DEMO_MODE is true and no token is set. Cookies are designed for local HTTP; set COOKIE_SECURE=true behind HTTPS before network deployment. Source strings containing local paths/credentials are redacted from all camera responses. Only permitted media-root paths, webcam indices or explicitly enabled RTSP sources are accepted.

| Route | Methods | Purpose |
| --- | --- | --- |
| `/health`, `/snapshot` | GET | Process/source health; bounded live dashboard snapshot |
| `/cameras` | GET, POST | List/add sources; new source gets a default ROI |
| `/cameras/{id}` | PUT | Replace camera configuration and restart worker; resolves old source events |
| `/zones` | GET, POST | List/add normalized polygon zones |
| `/zones/{id}` | PUT | Set polygon, capacity and restricted-stop flag |
| `/connections` | GET, POST | Explicit connected-camera topology |
| `/streams/upload` | POST multipart `file` | Stream to disk, enforce 250 MiB limit and validate OpenCV decoding |
| `/streams/{id}/start`, `/stop` | POST | Source lifecycle; Start replays a finished video |
| `/streams/{id}/frame` | GET | Latest annotated JPEG (404 before first frame) |
| `/observations` | GET | Filters `camera_id`, `zone_id`, `since`, `limit`, `offset` |
| `/events` | GET | Event records, `status`, `limit`, `offset` |
| `/incidents` | GET | Joined events; `q`, `severity`, `status`, `limit`, `offset` |
| `/incidents/{id}` | GET | Timeline, retained evidence, reports and feedback |
| `/incidents/{id}/review` | PATCH | `status` under_review/verified/dismissed/resolved and `note` |
| `/evidence/{id}/frame` | GET | Authorized retained JPEG; 410 when unavailable |
| `/correlations` | GET | Latest 100 explanatory incident relationships |
| `/forecasts` | GET | Current per-zone forecasts from recent observations |
| `/investigations` | GET | Recent stored reports; `limit`, `offset` |
| `/investigations/{incident_id}` | POST | Grounded report; optional `question` |
| `/settings` | GET, PUT | Environment capability summary and validated intelligence settings |
| `/audit` | GET | Operator/system actions; `limit`, `offset` |
| `/demo/control` | POST | `paused`, `speed` (0.25–10); synthetic sources only |
| `/demo/reset` | POST | Delete synthetic generated records; retain audit and real-inference records |

Limits are bounded to 500 rows (100 for reports). The dashboard snapshot is a compact latest-state view rather than a paginated historical endpoint. JSON errors follow FastAPI `detail` conventions: 401 authentication, 404 missing resource, 409 invalid closed/demo operation, 410 expired evidence, 413 oversized upload, 422 invalid input, 429 write limit. Write throttling is 30 requests/minute per client/path and is intentionally process-local.

WebSocket `/ws/live`: browser origin must match `CORS_ORIGINS`; send `{"token":"..."}` within five seconds (or an empty token with valid cookie/local demo). Server emits `{"type":"snapshot","data":{...}}` at 1 Hz. Frontend reconnects with backoff and polls HTTP every five seconds as fallback. Configure `NEXT_PUBLIC_WS_URL` for a non-default host/port; this value must be set during frontend build.

No route dispatches emergency services or acts on individuals. Audit records deliberately exclude operator secrets, RTSP credentials and raw question text. Camera/zone names, source metadata, reference documents and operator questions are untrusted data, never executable agent instructions.


## Real recording and local-model workflow (25 November 2026)

SYNTHETIC_MODE=false is the default. DEMO_MODE controls unauthenticated local demo access and does not enable synthetic measurements. `/snapshot` filters disabled legacy synthetic sources/history out of the real workspace. Camera source_metadata reports checksum-verified publisher assets, crop/recording group and unverified geographic location; source paths/credentials remain redacted.

- POST `/recordings/replay`: begin fresh recording/track runs without deleting evidence/history. Previous active run events resolve with an explicit replay note; cooldown applies within each run.
- GET `/streams/{id}/video`: authenticated WebM playback preview of original real frames; supports ranges. `?original=true` retrieves the original container/codec. FFmpeg conversion is cached by source size/mtime and has a timeout; failure is an explicit 503, not simulated playback.
- POST `/investigations/{incident_id}/jobs`: return 202 with an ID and queue/running state immediately. Maximum four queued/running jobs and 64 retained job states; local model execution is serialized.
- GET `/investigation-jobs/{job_id}`: queued/running/complete/failed/cancelled, plus the actual report when complete. This avoids frontend proxy timeouts during CPU generation. Job state is process-local; finished reports persist in the database. On restart, rerun an interrupted job.

The original synchronous POST investigation endpoint remains available for direct clients with a sufficiently long timeout. The browser uses the short-request job API. Ollama returns structured JSON, cited reference IDs are validated against retained snapshots, and interpretations are labeled as model-generated hypotheses rather than established facts.
