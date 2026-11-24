export type Track = {
  id: number;
  class: string;
  confidence: number;
  bbox: number[];
  center: number[];
  speed: number;
  velocity: number[];
  dwell: number;
  trajectory: number[][];
};
export type Camera = {
  id: string;
  name: string;
  lat: number;
  lon: number;
  source: string;
  kind: string;
  enabled: boolean;
  health: string;
  detail: string;
  dropped_frames?: number;
};
export type Zone = {
  id: string;
  camera_id: string;
  name: string;
  capacity: number;
  polygon: number[][];
  restricted: boolean;
};
export type Event = {
  id: string;
  camera_id: string;
  zone_id: string;
  type: string;
  started_at: number;
  updated_at: number;
  severity: string;
  confidence: number;
  status: string;
  verification: string;
  provenance: string;
  factors: string[];
  tracks: number[];
  evidence_refs: string[];
};
export type Incident = {
  id: string;
  event_id: string;
  title: string;
  timeline: { timestamp: number; status: string; note: string }[];
  event: Event;
};
export type ForecastPoint = {
  timestamp: number;
  value: number;
  lower: number;
  upper: number;
};
export type Forecast = {
  ready: boolean;
  reason?: string;
  points: ForecastPoint[];
  horizon: number;
  peak_ratio: number;
  threshold_crossing_seconds?: number | null;
  method?: string;
  uncertainty?: string;
  factors?: string[];
  provenance: string;
  residual_rmse?: number;
};
export type Risk = {
  score: number;
  level: string;
  confidence: number;
  components: Record<string, number>;
  explanation: string;
};
export type Metrics = {
  count: number;
  people: number;
  vehicles: number;
  occupancy: number;
  smoothed_count: number;
  mean_speed: number;
  growth_rate: number;
  direction: number;
  conflicting_flow: number;
  concentration: number;
  confidence: number;
  tracks: Track[];
};
export type Latest = {
  camera_id: string;
  zone_id: string;
  timestamp: number;
  provenance: string;
  metrics: Metrics;
  risk: Risk;
  forecast: Forecast;
  inference_ms: number;
  inference_fps: number | null;
  pipeline_latency_ms: number;
  queue_latency_ms: number;
  media_time: number;
};
export type Correlation = {
  id: string;
  incident_a: string;
  incident_b: string;
  confidence: number;
  explanation: string;
  timestamp: number;
};
export type Snapshot = {
  timestamp: number;
  cameras: Camera[];
  zones: Zone[];
  incidents: Incident[];
  correlations: Correlation[];
  connections: { id: string; camera_a: string; camera_b: string }[];
  latest: Latest[];
  history: Record<
    string,
    { timestamp: number; count: number; provenance: string }[]
  >;
  demo: {
    enabled: boolean;
    time: number;
    duration: number;
    speed: number;
    paused: boolean;
    phase: string;
  };
  health: { engine_error: string; tick_ms: number; uptime_seconds: number };
};
export type Evidence = {
  id: string;
  timestamp: number;
  provenance: string;
  url: string;
  data: {
    factors: string[];
    count: number;
    media_time: number;
    event_latency_ms: number;
    privacy: string;
    risk: Risk;
  };
};
export type Report = {
  id: string;
  timestamp: number;
  data: {
    summary: string;
    observations: { claim: string; evidence_references: string[] }[];
    related_events: Correlation[];
    possible_explanations: {
      text: string;
      evidence_references: string[];
      kind: string;
    }[];
    risk_factors: string[];
    missing_information: string[];
    recommended_actions: string[];
    evidence_references: string[];
    limitations: string[];
    mode: string;
    provenance: string;
    operator_answer: string;
    question: string;
    risk?: Risk;
    tool_trace: string[];
    optional_llm_advisory?: { text: string; label: string };
  };
};
export type Detail = Incident & {
  evidence: Evidence[];
  reports: Report[];
  feedback: { timestamp: number; verdict: string; note: string }[];
};
export type Config = {
  persistence_seconds: number;
  occupancy_threshold: number;
  stationary_seconds: number;
  forecast_horizon: number;
  risk_high: number;
  risk_critical: number;
  cooldown_seconds: number;
  confidence_threshold: number;
};
export type Settings = {
  intelligence: Config;
  llm: { provider: string; model: string; configured_by: string };
  privacy: {
    blur_evidence: boolean;
    evidence_retention_days: number;
    observation_retention_days: number;
  };
  device: string;
};
