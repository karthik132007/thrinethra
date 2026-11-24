# Trinethra engineering instructions

- Local-first, Python 3.12+, Next.js/TypeScript. No deployment or remote push without authorization.
- Run `make test`, `make typecheck`, and `make build` before declaring completion.
- Keep simulation provenance on observations, events, evidence, forecasts and reports. Never present synthetic measurements as video inference.
- Never add identification, biometrics, re-identification, individual threat scoring or autonomous enforcement.
- Evidence claims must reference stored observations/evidence. Tracking IDs are camera-local and expire.
- Use per-camera workers and bounded buffers; SQLite for local operation, PostgreSQL via DATABASE_URL. Database state is never authoritative authentication state.
- Keep secrets in environment variables. Limit uploaded media, restrict source paths to the configured media directory, and redact source credentials from API output.
- Update PROGRESS.md and docs when capabilities or limitations change. Do not invent accuracy or performance figures.
