# Trinethra engineering instructions

- Local-first, Python 3.12+, Next.js/TypeScript. No deployment or remote push without authorization.
- Run `make test`, `make typecheck`, and `make build` before declaring completion.
- Keep simulation provenance on observations, events, evidence, forecasts and reports. Never present synthetic measurements as video inference.
- Never add identification, biometrics, re-identification, individual threat scoring or autonomous enforcement.
- Evidence claims must reference stored observations/evidence. Tracking IDs are camera-local and expire.
- Use per-camera workers and bounded buffers; SQLite for local operation, PostgreSQL via DATABASE_URL. Database state is never authoritative authentication state.
- Keep secrets in environment variables. Limit uploaded media, restrict source paths to the configured media directory, and redact source credentials from API output.
- Update PROGRESS.md and docs when capabilities or limitations change. Do not invent accuracy or performance figures.

- Default development/demo mode is real recorded-video inference (SYNTHETIC_MODE=false). Never reintroduce generated observations as the default.
- Downloaded assets must match configs/assets.json hashes. Large publisher files support resumable range downloads; do not silently use partial files.
- Real acceptance tests use isolated ports 3001/8001 and runtime/e2e-real.db; never reset or re-enable operator-controlled application cameras to make tests pass.
- Language model generation runs through bounded background jobs; factual observations stay tied to retained evidence even if the model fails.
