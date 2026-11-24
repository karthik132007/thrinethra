# Database

SQLAlchemy models: `apps/backend/trinethra/db.py`. Alembic initial migration: `infrastructure/migrations/versions/0001_initial.py`. Apply with `make migrate`. Startup also creates missing tables for convenient local demos; it does not alter existing columns. Future schema changes need new immutable Alembic revisions. Existing unversioned MVP schemas can be stamped with `alembic -c infrastructure/alembic.ini stamp 0001` only after confirming they match.

| Table | Key relationships / retained data |
| --- | --- |
| cameras | Source configuration, map coordinates, kind and health |
| zones | Camera FK, normalized polygon, capacity and restricted-stop flag |
| camera_connections | Explicit camera A/B foreign keys |
| observations | Camera/zone FKs; capture time, provenance, count/motion features and bounded tracks |
| track_measurements | Observation FK; aggregate count, motion and direction summary |
| events | Camera/zone FKs; type, times, severity, confidence, lifecycle, verification, factors and refs |
| incidents | Unique event FK; title and timestamped lifecycle timeline |
| incident_correlations | Two incident FKs; heuristic confidence, explanation, timestamp |
| risk_assessments | Observation FK; normalized experimental score, level and component JSON |
| forecasts | Camera FK; timestamped per-zone forecast JSON and provenance |
| evidence | Event and nullable observation FKs; relative JPEG path, snapshot factors, track summaries and source metadata |
| investigation_reports | Incident FK; complete structured grounded report and timestamp |
| operator_feedback | Incident FK; verdict, note and timestamp |
| application_configuration | Named intelligence-settings JSON; never API keys |
| audit_logs | Timestamp, action, subject and non-secret metadata |

Observation lookup has a composite camera/time index; event statuses/camera IDs, forecast/evidence/audit timestamps and relationship FKs are indexed. SQLite enforces foreign keys and WAL. PostgreSQL uses the same schema with JSON columns; no PostGIS requirement.

Evidence snapshots occur at incident onset and at most every 15 seconds while active. Configurable retention sweeps run every five minutes. Expired evidence files and refs are removed; expired observations/aggregates/risk rows and old forecasts are purged. Retained evidence loses its observation pointer when the referenced observation expires. Reports preserve historical text and can contain expired evidence IDs: operators must inspect current evidence availability. Audit, feedback and incident summaries persist until explicitly managed; their retention is not yet automated. Uploaded input media is not automatically deleted because operators may still need its source; manage that directory separately.

Use a single backend process. The writer is the main event loop; workers never open database sessions. PostgreSQL is configured and its migration SQL is checked where possible, but full PostgreSQL runtime testing requires a running database. See PROGRESS.md for verified scope.
