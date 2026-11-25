"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";
import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  Camera as CameraIcon,
  Check,
  ChevronDown,
  ChevronRight,
  Clock,
  Download,
  Expand,
  Eye,
  FileSearch,
  Focus,
  GitBranch,
  Layers,
  LayoutDashboard,
  MapPin,
  Pause,
  Play,
  Plus,
  Radio,
  RefreshCw,
  Search,
  Settings2,
  Shield,
  SlidersHorizontal,
  TrendingUp,
  Upload,
  Wifi,
  WifiOff,
  X,
  PanelLeftClose,
} from "lucide-react";
import { Button, Modal, cn } from "../components/ui";
import { ForecastChart } from "../components/forecast-chart";
import type {
  Camera,
  Zone,
  Snapshot,
  Latest,
  Incident,
  Detail,
  Report,
  Settings,
  Config,
} from "../components/types";
const OperationalMap = dynamic(() => import("../components/operational-map"), {
  ssr: false,
  loading: () => (
    <div className="empty map-loading">Loading operational map…</div>
  ),
});
type Page =
  | "Command centre"
  | "Live surveillance"
  | "Incidents"
  | "Predictive intelligence"
  | "Investigation workspace"
  | "System settings";
const pages: { name: Page; icon: typeof Activity; short: string }[] = [
  { name: "Command centre", icon: LayoutDashboard, short: "Overview" },
  { name: "Live surveillance", icon: CameraIcon, short: "Surveillance" },
  { name: "Incidents", icon: AlertTriangle, short: "Incidents" },
  { name: "Predictive intelligence", icon: TrendingUp, short: "Intelligence" },
  { name: "Investigation workspace", icon: GitBranch, short: "Investigations" },
  { name: "System settings", icon: Settings2, short: "Settings" },
];
const stamp = (n: number) =>
  new Date(n * 1000).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
const active = (i: Incident) =>
  !["resolved", "dismissed"].includes(i.event.status);
function Badge({ value }: { value: string }) {
  return (
    <span className={cn("badge", value)}>{value.replaceAll("_", " ")}</span>
  );
}
function Provenance({ value }: { value: string }) {
  return (
    <span className={cn("provenance", value === "synthetic" ? "sim" : "real")}>
      {value === "synthetic"
        ? "SYNTHETIC"
        : value === "video_inference"
          ? "VIDEO INFERENCE"
          : "WAITING FOR INFERENCE"}
    </span>
  );
}
async function api<T>(
  path: string,
  method = "GET",
  body?: unknown,
): Promise<T> {
  const response = await fetch("/api/v1" + path, {
    method,
    headers:
      body instanceof FormData ? {} : { "Content-Type": "application/json" },
    body:
      body === undefined
        ? undefined
        : body instanceof FormData
          ? body
          : JSON.stringify(body),
    credentials: "same-origin",
    cache: "no-store",
  });
  if (!response.ok) {
    let message =
      response.status === 401
        ? "Operator authentication required"
        : `Request failed (${response.status})`;
    try {
      const data = await response.json();
      message =
        typeof data.detail === "string"
          ? data.detail
          : JSON.stringify(data.detail);
    } catch {}
    throw new Error(message);
  }
  return response.json();
}
function Frame({
  camera,
  tick,
  large = false,
  observedAt,
}: {
  camera: Camera;
  tick: number;
  large?: boolean;
  observedAt?: number;
}) {
  const [failed, setFailed] = useState(false);
  useEffect(() => setFailed(false), [camera.id, camera.enabled, tick]);
  return (
    <div className={cn("video-frame", large && "large")}>
      {camera.enabled && !failed ? (
        <img
          src={`/api/v1/streams/${camera.id}/frame?t=${Math.floor(tick)}`}
          alt={`${camera.name} annotated feed`}
          onError={() => setFailed(true)}
        />
      ) : (
        <div className="empty">
          <CameraIcon size={28} />
          <span>
            {camera.enabled
              ? "Waiting for actual detector output"
              : "Stream stopped"}
          </span>
          <Button onClick={() => setFailed(false)}>Retry frame</Button>
        </div>
      )}
      <span className="video-corner tl" />
      <span className="video-corner br" />
      <div className="video-top">
        <span>
          <i className={camera.enabled ? "live-dot" : ""} />
          {camera.id.toUpperCase()}
        </span>
        <Provenance
          value={
            camera.source === "synthetic" ? "synthetic" : "video_inference"
          }
        />
      </div>
      <div className="video-bottom">
        <span>{camera.name}</span>
        <span>{observedAt ? stamp(observedAt) : "No observation"}</span>
      </div>
    </div>
  );
}
function RelationGraph({
  snapshot,
  selected,
  onSelect,
}: {
  snapshot: Snapshot;
  selected: string;
  onSelect: (id: string) => void;
}) {
  const relations = snapshot.correlations.filter(
    (c) => c.incident_a === selected || c.incident_b === selected,
  );
  const ids = [
    selected,
    ...new Set(
      relations.map((c) =>
        c.incident_a === selected ? c.incident_b : c.incident_a,
      ),
    ),
  ];
  if (!selected)
    return (
      <div className="empty">Select an incident to inspect connections.</div>
    );
  return (
    <div className="relationship">
      <svg
        viewBox="0 0 620 230"
        role="img"
        aria-label="Aggregate incident relationship graph"
      >
        {ids.slice(1, 5).map((id, index) => {
          const y = 35 + index * 52;
          return (
            <path
              key={id}
              d={`M190 115 C320 115 320 ${y} 430 ${y}`}
              fill="none"
              stroke="#596b73"
              strokeDasharray="5 5"
            />
          );
        })}
        <g
          onClick={() => onSelect(selected)}
          tabIndex={0}
          role="button"
          aria-label="Selected incident"
          onKeyDown={(e) => {
            if (e.key === "Enter") onSelect(selected);
          }}
        >
          <rect
            x="15"
            y="85"
            width="175"
            height="60"
            rx="4"
            fill="#332f28"
            stroke="#c9a36d"
          />
          <text x="30" y="110" fill="#e4d0ac" fontSize="12">
            SELECTED INCIDENT
          </text>
          <text x="30" y="130" fill="#a8b4bc" fontSize="11">
            {snapshot.incidents
              .find((i) => i.id === selected)
              ?.event.camera_id.toUpperCase()}
          </text>
        </g>
        {ids.slice(1, 5).map((id, index) => {
          const incident = snapshot.incidents.find((i) => i.id === id);
          return (
            <g
              key={id}
              onClick={() => onSelect(id)}
              tabIndex={0}
              role="button"
              aria-label={`Related incident ${incident?.event.camera_id}`}
              onKeyDown={(e) => {
                if (e.key === "Enter") onSelect(id);
              }}
              className="clickable"
            >
              <rect
                x="430"
                y={index * 52 + 12}
                width="170"
                height="44"
                rx="4"
                fill="#202c32"
                stroke="#52656e"
              />
              <text x="442" y={index * 52 + 30} fill="#c2d0d7" fontSize="12">
                {incident?.event.camera_id.toUpperCase()}
              </text>
              <text x="442" y={index * 52 + 46} fill="#90a2ac" fontSize="10">
                {incident?.title.slice(0, 25)}
              </text>
            </g>
          );
        })}
        {!relations.length && (
          <text x="280" y="120" fill="#93a1aa" fontSize="13">
            No linked events in connected zones.
          </text>
        )}
      </svg>
      <div className="relation-explanations">
        {relations.slice(0, 4).map((c) => (
          <p key={c.id}>
            <GitBranch size={13} />
            {c.explanation}{" "}
            <span>{Math.round(c.confidence * 100)}% heuristic confidence</span>
          </p>
        ))}
      </div>
    </div>
  );
}

export default function Home() {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null),
    [page, setPage] = useState<Page>("Command centre"),
    [connection, setConnection] = useState("connecting"),
    [error, setError] = useState(""),
    [toast, setToast] = useState(""),
    [selected, setSelected] = useState(""),
    [selectedIncident, setSelectedIncident] = useState(""),
    [detail, setDetail] = useState<Detail | null>(null),
    [busy, setBusy] = useState(false),
    [street, setStreet] = useState(false),
    [fit, setFit] = useState(0),
    [timeRange, setTimeRange] = useState(3600),
    [search, setSearch] = useState(""),
    [severity, setSeverity] = useState("all"),
    [statusFilter, setStatusFilter] = useState("all"),
    [inspect, setInspect] = useState<Camera | null>(null),
    [cameraModal, setCameraModal] = useState(false),
    [editCamera, setEditCamera] = useState<Camera | null>(null),
    [settings, setSettings] = useState<Settings | null>(null),
    [config, setConfig] = useState<Config | null>(null),
    [health, setHealth] = useState<Record<string, unknown> | null>(null),
    [question, setQuestion] = useState(""),
    [note, setNote] = useState(""),
    [token, setToken] = useState(""),
    [needsAuth, setNeedsAuth] = useState(false),
    [loginVersion, setLoginVersion] = useState(0),
    [grid, setGrid] = useState(2),
    [sidebar, setSidebar] = useState(true),
    [zoneModal, setZoneModal] = useState<Zone | null>(null);
  const alive = useRef(true);
  const notify = (message: string) => {
    setToast(message);
    setTimeout(() => setToast(""), 5000);
  };
  const run = async (action: () => Promise<unknown>, message?: string) => {
    setBusy(true);
    setError("");
    try {
      await action();
      if (message) notify(message);
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  const refresh = useCallback(async () => {
    try {
      const data = await api<Snapshot>("/snapshot");
      setSnapshot(data);
      setNeedsAuth(false);
      setError((previous) =>
        previous.includes("Failed to fetch") ||
        previous === "Operator authentication required"
          ? ""
          : previous,
      );
    } catch (e) {
      const message = (e as Error).message;
      setError(message);
      if (message.includes("authentication")) setNeedsAuth(true);
    }
  }, []);
  useEffect(() => {
    alive.current = true;
    refresh();
    let ws: WebSocket | undefined;
    let timer: ReturnType<typeof setTimeout>;
    let retries = 0;
    const connect = () => {
      if (!alive.current) return;
      const url =
        process.env.NEXT_PUBLIC_WS_URL ||
        `${location.protocol === "https:" ? "wss" : "ws"}://${location.hostname}:8000/ws/live`;
      ws = new WebSocket(url);
      ws.onopen = () => {
        ws?.send(JSON.stringify({ token: "" }));
        retries = 0;
      };
      ws.onmessage = (message) => {
        try {
          const value = JSON.parse(message.data);
          if (value.type === "snapshot") {
            setSnapshot(value.data);
            setConnection("live");
            setNeedsAuth(false);
          }
        } catch {
          setConnection("error");
        }
      };
      ws.onerror = () => setConnection("disconnected");
      ws.onclose = () => {
        if (alive.current) {
          setConnection("polling");
          timer = setTimeout(connect, Math.min(15000, 1000 * 2 ** retries++));
        }
      };
    };
    connect();
    const poll = setInterval(refresh, 5000);
    return () => {
      alive.current = false;
      clearTimeout(timer);
      clearInterval(poll);
      ws?.close();
    };
  }, [refresh, loginVersion]);
  useEffect(() => {
    if (snapshot && !snapshot.cameras.some((c) => c.id === selected))
      setSelected(snapshot.cameras[0]?.id || "");
  }, [snapshot?.cameras.map((c) => c.id).join(","), selected]);
  useEffect(() => {
    if (!selectedIncident) return;
    api<Detail>(`/incidents/${selectedIncident}`)
      .then(setDetail)
      .catch((e) => setError(e.message));
  }, [
    selectedIncident,
    snapshot?.incidents.find((i) => i.id === selectedIncident)?.event.status,
  ]);
  useEffect(() => {
    if (page === "System settings") {
      api<Settings>("/settings")
        .then((data) => {
          setSettings(data);
          setConfig(data.intelligence);
        })
        .catch((e) => setError(e.message));
      api<Record<string, unknown>>("/health")
        .then(setHealth)
        .catch((e) => setError(e.message));
    }
  }, [page]);
  const openIncident = (id: string, workspace = false) => {
    if (id !== selectedIncident) setDetail(null);
    setSelectedIncident(id);
    setPage(workspace ? "Investigation workspace" : "Incidents");
  };
  const investigate = () =>
    run(async () => {
      const job = await api<{ id: string }>(
        `/investigations/${selectedIncident}/jobs`,
        "POST",
        { question },
      );
      let report: Report | undefined;
      const deadline = Date.now() + 240000;
      while (Date.now() < deadline) {
        const state = await api<{
          state: string;
          report?: Report;
          error?: string;
        }>(`/investigation-jobs/${job.id}`);
        if (state.state === "complete" && state.report) {
          report = state.report;
          break;
        }
        if (["failed", "cancelled"].includes(state.state))
          throw new Error(state.error || "Investigation failed");
        await new Promise((resolve) => setTimeout(resolve, 1000));
      }
      if (!report)
        throw new Error(
          "Investigation is still running; reopen the incident to check retained reports.",
        );
      setDetail((old) =>
        old ? { ...old, reports: [report, ...old.reports] } : old,
      );
      setPage("Investigation workspace");
    }, "Evidence-grounded investigation completed");
  const review = (status: string) =>
    run(
      async () => {
        const data = await api<Detail>(
          `/incidents/${selectedIncident}/review`,
          "PATCH",
          { status, note },
        );
        setDetail(data);
        setNote("");
      },
      `Incident ${status.replaceAll("_", " ")}`,
    );
  const exportData = () => {
    const blob = new Blob(
      [
        JSON.stringify(
          { exported_at: new Date().toISOString(), snapshot, incident: detail },
          null,
          2,
        ),
      ],
      { type: "application/json" },
    );
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "trinethra-observations.json";
    link.click();
    URL.revokeObjectURL(url);
    notify("Operational data exported");
  };
  const camera = snapshot?.cameras.find((c) => c.id === selected);
  const latest = snapshot?.latest.find((v) => v.camera_id === selected);
  const filtered =
    snapshot?.incidents.filter(
      (i) =>
        snapshot.timestamp - i.event.started_at <= timeRange &&
        (severity === "all" || i.event.severity === severity) &&
        (statusFilter === "all" ||
          (statusFilter === "active"
            ? active(i)
            : i.event.status === statusFilter)) &&
        `${i.title} ${i.event.camera_id}`
          .toLowerCase()
          .includes(search.toLowerCase()),
    ) || [];
  const activeIncidents = snapshot?.incidents.filter(active) || [];
  const maxRisk = Math.max(
    0,
    ...(snapshot?.latest.map((v) => v.risk.score) || []),
  );
  const people =
    snapshot?.latest.reduce((sum, v) => sum + v.metrics.people, 0) || 0;
  const vehicles =
    snapshot?.latest.reduce((sum, v) => sum + v.metrics.vehicles, 0) || 0;
  const report = detail?.reports[0]?.data;
  if (needsAuth)
    return (
      <main className="login">
        <div className="login-box">
          <div className="brand-symbol">
            <Eye size={32} />
          </div>
          <h1>Trinethra</h1>
          <p>Operator access · Command centre</p>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              run(async () => {
                await api("/auth/session", "POST", { token });
                setNeedsAuth(false);
                setLoginVersion((v) => v + 1);
              });
            }}
          >
            <label>
              Operator token
              <input
                type="password"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                required
                autoFocus
              />
            </label>
            <Button type="submit" className="primary">
              Sign in
            </Button>
          </form>
          {error && <p className="error-text">{error}</p>}
        </div>
      </main>
    );
  return (
    <div className={cn("app-shell", !sidebar && "sidebar-collapsed")}>
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-symbol">
            <Eye size={25} />
          </div>
          <div>
            <strong>TRINETHRA</strong>
            <span>THE THIRD EYE</span>
          </div>
        </div>
        <div className="workspace-label">OPERATIONS WORKSPACE</div>
        <nav>
          {pages.map((item, index) => (
            <button
              key={item.name}
              onClick={() => setPage(item.name)}
              className={cn("nav-item", page === item.name && "selected")}
              title={item.name}
              aria-label={item.short}
            >
              <item.icon size={18} />
              <span>{item.short}</span>
              {item.name === "Incidents" && activeIncidents.length > 0 ? (
                <b>{activeIncidents.length}</b>
              ) : item.name === "Command centre" ? (
                <span className="nav-key">01</span>
              ) : null}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="system-chip">
            <span
              className={cn(
                "connection-dot",
                connection === "live" && "online",
              )}
            />
            <span>
              {connection === "live"
                ? "Live system connection"
                : "HTTP polling fallback"}
            </span>
          </div>
          <div className="privacy-note">
            <Shield size={15} />
            <span>
              Anonymous by design.
              <br />
              Human judgment, informed.
            </span>
          </div>
          <div className="operator">
            <div className="avatar">OP</div>
            <div>
              <strong>Local operator</strong>
              <span>Command centre access</span>
            </div>
            <button
              aria-label="Collapse sidebar"
              onClick={() => setSidebar(false)}
            >
              <PanelLeftClose size={15} />
            </button>
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumb">
            {!sidebar && (
              <Button
                onClick={() => setSidebar(true)}
                aria-label="Show sidebar"
              >
                <LayoutDashboard size={16} />
              </Button>
            )}
            <span>Operations</span>
            <ChevronRight size={13} />
            <strong>{page}</strong>
          </div>
          <div className="top-actions">
            <span className="local-label">
              <MapPin size={13} />{" "}
              {snapshot?.demo.enabled
                ? "SYNTHETIC TEST ENVIRONMENT"
                : "RECORDED VIDEO INFERENCE"}
            </span>
            <span className="top-separator" />
            <span className="clock">
              {snapshot ? stamp(snapshot.timestamp) : "—"}
            </span>
            <span
              className={cn("live-label", connection === "live" && "online")}
            >
              {connection === "live" ? (
                <Wifi size={13} />
              ) : (
                <WifiOff size={13} />
              )}{" "}
              {connection === "live" ? "LIVE" : "RECONNECTING"}
            </span>
          </div>
        </header>
        <main className="main-content">
          <div className="page-heading">
            <div>
              <div className="eyebrow">SITUATIONAL INTELLIGENCE PLATFORM</div>
              <h1>{page}</h1>
              <p>
                {page === "Command centre"
                  ? "A connected view. An informed response."
                  : page === "Live surveillance"
                    ? "Camera-local detection, tracking and spatial observations."
                    : page === "Incidents"
                      ? "Evidence-led triage with a human in control."
                      : page === "Predictive intelligence"
                        ? "Understand current trends. Anticipate possible pressure."
                        : page === "Investigation workspace"
                          ? "Trace every observation back to its evidence."
                          : "Configure the environment and experimental intelligence baselines."}
              </p>
            </div>
            <div className="heading-actions">
              <label className="select-icon">
                <Clock size={14} />
                <select
                  aria-label="Time range"
                  value={timeRange}
                  onChange={(e) => setTimeRange(Number(e.target.value))}
                >
                  <option value={900}>Last 15 minutes</option>
                  <option value={3600}>Last hour</option>
                  <option value={86400}>Last 24 hours</option>
                  <option value={31536000}>All retained data</option>
                </select>
                <ChevronDown size={13} />
              </label>
              <Button onClick={exportData} disabled={!snapshot}>
                <Download size={15} />
                Export data
              </Button>
            </div>
          </div>
          {error && (
            <div role="alert" className="error-banner">
              <AlertTriangle size={16} />
              <span>{error}</span>
              <Button onClick={() => refresh()}>Retry</Button>
              <button aria-label="Dismiss error" onClick={() => setError("")}>
                <X size={15} />
              </button>
            </div>
          )}
          {!snapshot ? (
            <div className="loading-state">
              <Radio size={30} />
              <h2>Connecting to operations</h2>
              <p>
                Start the backend at 127.0.0.1:8000 to receive observations.
              </p>
              <Button onClick={refresh}>
                <RefreshCw size={15} />
                Reconnect
              </Button>
            </div>
          ) : (
            <>
              {!snapshot.demo.enabled && (
                <div className="recording-bar">
                  <div>
                    <span className="real-tag">REAL VIDEO INFERENCE</span>
                    <strong>
                      {snapshot.recordings?.model || "Local detector"}
                    </strong>
                    <p>
                      Measured from downloaded recordings · geographic locations
                      unverified · no generated detections
                    </p>
                  </div>
                  <Button
                    disabled={busy}
                    onClick={() =>
                      run(
                        () => api("/recordings/replay", "POST", {}),
                        "Recordings restarted with fresh tracking",
                      )
                    }
                  >
                    <RefreshCw size={14} />
                    Replay recordings
                  </Button>
                </div>
              )}
              {snapshot.demo.enabled && (
                <div className="demo-bar">
                  <div className="demo-description">
                    <span className="demo-tag">SIMULATION</span>
                    <span>
                      <strong>{snapshot.demo.phase}</strong>
                      <span className="demo-detail">
                        Synthetic trajectories · no real video inference
                      </span>
                    </span>
                  </div>
                  <div className="demo-controls">
                    <span className="mono muted">
                      {Math.floor(snapshot.demo.time)} /{" "}
                      {snapshot.demo.duration}s
                    </span>
                    <div className="demo-progress">
                      <div
                        style={{
                          width: `${(snapshot.demo.time / snapshot.demo.duration) * 100}%`,
                        }}
                      />
                    </div>
                    <Button
                      aria-label={
                        snapshot.demo.paused ? "Resume demo" : "Pause demo"
                      }
                      onClick={() =>
                        run(() =>
                          api("/demo/control", "POST", {
                            paused: !snapshot.demo.paused,
                          }),
                        )
                      }
                      disabled={busy}
                    >
                      {snapshot.demo.paused ? (
                        <Play size={14} />
                      ) : (
                        <Pause size={14} />
                      )}
                    </Button>
                    <select
                      aria-label="Demo playback speed"
                      value={snapshot.demo.speed}
                      onChange={(e) =>
                        run(() =>
                          api("/demo/control", "POST", {
                            speed: Number(e.target.value),
                          }),
                        )
                      }
                    >
                      <option value={0.5}>0.5×</option>
                      <option value={1}>1×</option>
                      <option value={2}>2×</option>
                      <option value={5}>5×</option>
                      <option value={10}>10×</option>
                    </select>
                    <Button
                      onClick={() =>
                        run(async () => {
                          await api("/demo/reset", "POST", {});
                          setSelectedIncident("");
                          setDetail(null);
                        }, "Synthetic scenario reset")
                      }
                      disabled={busy}
                    >
                      <RefreshCw size={13} />
                      Reset demo
                    </Button>
                  </div>
                </div>
              )}
              {snapshot.health.engine_error && (
                <div className="error-banner">
                  Intelligence engine degraded: {snapshot.health.engine_error}.
                  See backend logs.
                </div>
              )}
              {(page === "Command centre" || page === "Live surveillance") && (
                <div className="stat-grid">
                  <Stat
                    label="CAMERA NETWORK"
                    value={`${snapshot.cameras.filter((c) => c.enabled && ["online", "synthetic"].includes(c.health)).length}`}
                    suffix={`/ ${snapshot.cameras.length}`}
                    sub="Sources reporting"
                    icon={CameraIcon}
                    tone="green"
                  />
                  <Stat
                    label="ACTIVE INCIDENTS"
                    value={String(activeIncidents.length).padStart(2, "0")}
                    sub={`${activeIncidents.filter((i) => i.event.severity === "critical").length} critical · operator review required`}
                    icon={AlertTriangle}
                    tone="amber"
                  />
                  <Stat
                    label="OBSERVED OCCUPANCY"
                    value={snapshot.latest.length ? String(people) : "—"}
                    suffix="people"
                    sub={`${vehicles} vehicle detections · ${snapshot.demo.enabled ? "synthetic measurements" : "measured per-source counts, not unique people across cameras"}`}
                    icon={Activity}
                  />
                  <Stat
                    label="HIGHEST ZONE SCORE"
                    value={
                      snapshot.latest.length ? String(Math.round(maxRisk)) : "—"
                    }
                    suffix="/ 100"
                    sub="Highest zone score · experimental"
                    icon={Shield}
                    tone={
                      maxRisk >= 75 ? "red" : maxRisk >= 50 ? "amber" : "green"
                    }
                  />
                </div>
              )}
              {page === "Command centre" && (
                <>
                  <div className="overview-grid">
                    <section className="panel map-panel">
                      <PanelHead
                        title="Operational overview"
                        subtitle={`${snapshot.cameras.length} SOURCES · ${snapshot.zones.length} ZONES`}
                      >
                        <Button
                          onClick={() => {
                            if (snapshot.demo.enabled) setStreet((v) => !v);
                            else setFit((v) => v + 1);
                          }}
                          className={street ? "active-button" : ""}
                        >
                          <Layers size={14} />
                          {street
                            ? "Street map"
                            : snapshot.demo.enabled
                              ? "Schematic"
                              : "Source graph"}
                        </Button>
                        <Button
                          aria-label="Fit map"
                          onClick={() => setFit((v) => v + 1)}
                        >
                          <Focus size={15} />
                        </Button>
                      </PanelHead>
                      <div className="map-wrap">
                        <OperationalMap
                          snapshot={snapshot}
                          selected={selected}
                          onSelect={setSelected}
                          street={street}
                          fit={fit}
                        />
                        <div className="map-floating-label">
                          <span className="live-dot" /> OPERATIONAL NETWORK{" "}
                          <span className="muted">
                            /{" "}
                            {snapshot.demo.enabled
                              ? street
                                ? "OSM"
                                : "SIMULATION LAYOUT"
                              : "SOURCE TOPOLOGY"}
                          </span>
                        </div>
                        <div className="map-legend">
                          <span>
                            <i style={{ background: "#82afa4" }} />
                            Normal
                          </span>
                          <span>
                            <i style={{ background: "#e4ae59" }} />
                            High risk
                          </span>
                          <span>
                            <i style={{ background: "#f27764" }} />
                            Critical
                          </span>
                          <span className="line-legend">Connected zones</span>
                        </div>
                      </div>
                      <div className="map-footer">
                        <Radio size={13} />
                        <span>
                          Aggregate signals only · no cross-camera identity
                          matching
                        </span>
                        <span className="muted">
                          Updated {stamp(snapshot.timestamp)}
                        </span>
                      </div>
                    </section>
                    <section className="panel incident-feed">
                      <PanelHead
                        title="Incident feed"
                        subtitle={`${activeIncidents.length} OPEN`}
                      >
                        <Button
                          aria-label="Open incidents"
                          onClick={() => setPage("Incidents")}
                        >
                          <ArrowUpRight size={16} />
                        </Button>
                      </PanelHead>
                      <div className="feed-scroll">
                        {filtered.slice(0, 8).map((i) => (
                          <button
                            className={cn("feed-item", i.event.severity)}
                            key={i.id}
                            onClick={() => openIncident(i.id)}
                          >
                            <div className="feed-line">
                              <span className="incident-dot" />
                              <span className="mono">
                                {i.id.slice(0, 8).toUpperCase()}
                              </span>
                              <span>{stamp(i.event.started_at)}</span>
                            </div>
                            <strong>{i.title}</strong>
                            <div className="feed-location">
                              <MapPin size={12} />
                              {
                                snapshot.cameras.find(
                                  (c) => c.id === i.event.camera_id,
                                )?.name
                              }
                              <ChevronRight size={13} />
                            </div>
                            <div className="feed-bottom">
                              <Badge value={i.event.severity} />
                              <span>{i.event.status.replaceAll("_", " ")}</span>
                              <Provenance value={i.event.provenance} />
                            </div>
                          </button>
                        ))}
                        {!filtered.length && (
                          <div className="empty">
                            <Shield size={28} />
                            <strong>No incidents in this window</strong>
                            <p>
                              Temporal conditions must persist before an alert
                              opens. Replay the recordings or add a video
                              source; normal footage may produce no incidents.
                            </p>
                          </div>
                        )}
                      </div>
                      <button
                        className="panel-footer-button"
                        onClick={() => setPage("Incidents")}
                      >
                        View all incidents <ChevronRight size={14} />
                      </button>
                    </section>
                  </div>
                  <div className="lower-grid">
                    <section className="panel">
                      <PanelHead
                        title="Camera in focus"
                        subtitle={camera?.id.toUpperCase()}
                      >
                        <select
                          aria-label="Select camera"
                          value={selected}
                          onChange={(e) => setSelected(e.target.value)}
                        >
                          {snapshot.cameras.map((c) => (
                            <option key={c.id} value={c.id}>
                              {c.name}
                            </option>
                          ))}
                        </select>
                        <Button
                          aria-label="Inspect camera"
                          onClick={() => camera && setInspect(camera)}
                        >
                          <Expand size={14} />
                        </Button>
                      </PanelHead>
                      {camera && (
                        <Frame
                          camera={camera}
                          tick={snapshot.timestamp}
                          observedAt={latest?.timestamp}
                        />
                      )}
                      <div className="camera-metrics">
                        <span>
                          <b>{latest?.metrics.count ?? "—"}</b> zone objects
                        </span>
                        <span>
                          <b>
                            {latest
                              ? Math.round(latest.metrics.occupancy * 100) + "%"
                              : "—"}
                          </b>{" "}
                          occupancy
                        </span>
                        <span>
                          <b>
                            {latest?.inference_fps
                              ? latest.inference_fps.toFixed(1) + " FPS"
                              : latest?.provenance === "synthetic"
                                ? "SIM"
                                : "—"}
                          </b>{" "}
                          {latest?.inference_fps ? "inference" : "source"}
                        </span>
                      </div>
                    </section>
                    <section className="panel forecast-preview">
                      <PanelHead
                        title="Occupancy outlook"
                        subtitle="OBSERVATION-SELECTED BASELINE"
                      >
                        <Button
                          onClick={() => setPage("Predictive intelligence")}
                        >
                          Explore
                          <ChevronRight size={13} />
                        </Button>
                      </PanelHead>
                      <div className="forecast-preview-heading">
                        <div>
                          <b>
                            {latest?.forecast.points.at(-1)?.value.toFixed(0) ??
                              "—"}
                          </b>
                          <span>
                            estimated objects at +
                            {latest?.forecast.horizon ?? 60}s
                          </span>
                        </div>
                        <Provenance
                          value={latest?.provenance || "unavailable"}
                        />
                      </div>
                      <ForecastChart
                        snapshot={snapshot}
                        latest={latest}
                        compact
                      />
                      <div className="chart-legend">
                        <span>
                          <i className="observed-line" />
                          Observed
                        </span>
                        <span>
                          <i className="forecast-line" />
                          Forecast
                        </span>
                        <span>
                          Shaded: approximate interval · estimates only
                        </span>
                      </div>
                    </section>
                    <section className="panel posture">
                      <PanelHead
                        title="Intelligence posture"
                        subtitle="EXPLAINABLE BY DESIGN"
                      />
                      <div className="posture-main">
                        <Shield size={27} />
                        <h3>
                          {maxRisk >= 75
                            ? "Review recommended"
                            : maxRisk >= 50
                              ? "Elevated attention"
                              : "Monitoring conditions"}
                        </h3>
                        <p>
                          Experimental aggregate risk. Assess the evidence
                          before taking action.
                        </p>
                      </div>
                      <div className="posture-row">
                        <span>Linked incident pairs</span>
                        <b>{snapshot.correlations.length}</b>
                      </div>
                      <div className="posture-row">
                        <span>Human verification</span>
                        <b>Required</b>
                      </div>
                      <div className="posture-row">
                        <span>Identity recognition</span>
                        <b>Disabled</b>
                      </div>
                      <Button
                        className="posture-button"
                        onClick={() => {
                          if (activeIncidents[0])
                            openIncident(activeIncidents[0].id, true);
                          else {
                            setPage("Investigation workspace");
                          }
                        }}
                      >
                        <FileSearch size={15} />
                        Open investigation workspace
                      </Button>
                    </section>
                  </div>
                </>
              )}
              {page === "Live surveillance" && (
                <>
                  <div className="section-toolbar">
                    <div>
                      <h2>
                        Camera network{" "}
                        <span className="muted">
                          / {snapshot.cameras.length} sources
                        </span>
                      </h2>
                      <p>
                        Bounding boxes and temporary track IDs remain local to
                        each camera.
                      </p>
                    </div>
                    <div className="toolbar-actions">
                      <select
                        aria-label="Camera grid columns"
                        value={grid}
                        onChange={(e) => setGrid(Number(e.target.value))}
                      >
                        <option value={2}>2 columns</option>
                        <option value={1}>1 column</option>
                        <option value={3}>3 columns</option>
                      </select>
                      <Button
                        onClick={() => {
                          setEditCamera(null);
                          setCameraModal(true);
                        }}
                      >
                        <Plus size={15} />
                        Add camera
                      </Button>
                    </div>
                  </div>
                  <div
                    className="surveillance-grid"
                    style={{
                      gridTemplateColumns: `repeat(${grid},minmax(0,1fr))`,
                    }}
                  >
                    {snapshot.cameras.map((c) => {
                      const l = snapshot.latest.find(
                        (v) => v.camera_id === c.id,
                      );
                      return (
                        <section className="panel" key={c.id}>
                          <PanelHead
                            title={c.name}
                            subtitle={c.id.toUpperCase()}
                          >
                            <Badge value={c.health} />
                            <Button
                              aria-label={`Inspect ${c.name}`}
                              onClick={() => setInspect(c)}
                            >
                              <Expand size={14} />
                            </Button>
                          </PanelHead>
                          <Frame
                            camera={c}
                            tick={snapshot.timestamp}
                            observedAt={l?.timestamp}
                          />
                          <div className="camera-metrics">
                            <span>
                              <b>{l?.metrics.people ?? "—"}</b> people
                            </span>
                            <span>
                              <b>{l?.metrics.vehicles ?? "—"}</b> vehicles
                            </span>
                            <span>
                              <b>{l?.inference_fps?.toFixed(1) ?? "—"}</b>{" "}
                              inference FPS
                            </span>
                            <span>
                              <b>{l?.inference_ms.toFixed(0) ?? "—"}ms</b>{" "}
                              compute
                            </span>
                          </div>
                          {c.source !== "synthetic" && (
                            <div className="recording-timeline">
                              Recording {Math.floor(c.media_time || 0)} /{" "}
                              {Math.ceil(c.media_duration || 0)}s ·{" "}
                              {c.processed_frames || 0} frames inferred
                              {c.health === "ended"
                                ? " · playback complete"
                                : ""}
                            </div>
                          )}
                          {c.detail && (
                            <p className="camera-error">{c.detail}</p>
                          )}
                          <div className="camera-actions">
                            <Button
                              onClick={() =>
                                run(
                                  () =>
                                    api(
                                      `/streams/${c.id}/${c.enabled && c.health !== "ended" ? "stop" : "start"}`,
                                      "POST",
                                      {},
                                    ),
                                  `${c.name} ${c.enabled && c.health !== "ended" ? "stopped" : "started"}`,
                                )
                              }
                            >
                              {c.enabled && c.health !== "ended" ? (
                                <Pause size={13} />
                              ) : (
                                <Play size={13} />
                              )}{" "}
                              {c.enabled && c.health !== "ended"
                                ? "Stop"
                                : "Start"}
                            </Button>
                            <Button
                              onClick={() => {
                                setEditCamera(c);
                                setCameraModal(true);
                              }}
                            >
                              <Settings2 size={13} />
                              Configure
                            </Button>
                            <span className="muted">
                              Processed: {c.processed_frames ?? 0} · dropped:{" "}
                              {c.dropped_frames ?? 0}
                            </span>
                          </div>
                        </section>
                      );
                    })}
                  </div>
                </>
              )}
              {(page === "Incidents" || page === "Investigation workspace") && (
                <>
                  <div className="incident-layout">
                    <section className="panel incident-list">
                      <PanelHead
                        title="Incident register"
                        subtitle={`${filtered.length} RECORDS`}
                      />
                      <div className="filters">
                        <label className="search-field">
                          <Search size={14} />
                          <input
                            placeholder="Search incidents or cameras"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                          />
                        </label>
                        <div>
                          <select
                            aria-label="Severity filter"
                            value={severity}
                            onChange={(e) => setSeverity(e.target.value)}
                          >
                            <option value="all">All severities</option>
                            {["normal", "elevated", "high", "critical"].map(
                              (s) => (
                                <option key={s}>{s}</option>
                              ),
                            )}
                          </select>
                          <select
                            aria-label="Status filter"
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                          >
                            <option value="all">All statuses</option>
                            {[
                              "active",
                              "under_review",
                              "verified",
                              "dismissed",
                              "resolved",
                            ].map((s) => (
                              <option key={s}>{s}</option>
                            ))}
                          </select>
                        </div>
                      </div>
                      <div className="register-scroll">
                        {filtered.map((i) => (
                          <button
                            key={i.id}
                            className={cn(
                              "register-item",
                              selectedIncident === i.id && "chosen",
                            )}
                            onClick={() => {
                              if (i.id !== selectedIncident) setDetail(null);
                              setSelectedIncident(i.id);
                            }}
                          >
                            <div>
                              <span className="mono">
                                {i.id.slice(0, 8).toUpperCase()}
                              </span>
                              <Badge value={i.event.severity} />
                            </div>
                            <strong>{i.title}</strong>
                            <p>
                              {i.event.camera_id.toUpperCase()} ·{" "}
                              {stamp(i.event.started_at)}
                            </p>
                            <div>
                              <Provenance value={i.event.provenance} />
                              <Badge value={i.event.status} />
                            </div>
                          </button>
                        ))}
                        {!filtered.length && (
                          <div className="empty">
                            No incidents match these filters.
                          </div>
                        )}
                      </div>
                    </section>
                    <div className="incident-detail">
                      {!detail ? (
                        <div className="panel empty detail-empty">
                          <FileSearch size={35} />
                          <h2>
                            {selectedIncident
                              ? "Loading retained evidence…"
                              : "Select an incident"}
                          </h2>
                          <p>
                            Inspect temporal observations, connected events and
                            evidence references.
                          </p>
                        </div>
                      ) : (
                        <>
                          <section className="panel detail-header">
                            <div className="detail-top">
                              <span className="mono">
                                INCIDENT / {detail.id.slice(0, 8).toUpperCase()}
                              </span>
                              <div>
                                <Provenance value={detail.event.provenance} />
                                <Badge value={detail.event.severity} />
                                <Badge value={detail.event.status} />
                              </div>
                            </div>
                            <h2>{detail.title}</h2>
                            <p>
                              <MapPin size={14} />
                              {
                                snapshot.cameras.find(
                                  (c) => c.id === detail.event.camera_id,
                                )?.name
                              }{" "}
                              <span>·</span>Opened{" "}
                              {stamp(detail.event.started_at)}
                              <span>·</span>
                              {Math.round(detail.event.confidence * 100)}%
                              signal confidence
                            </p>
                            <div className="warning-inline">
                              <Shield size={15} />
                              Suspected condition · human verification required.
                              Risk severity is separate from confidence.
                            </div>
                          </section>
                          <section className="panel">
                            <PanelHead
                              title="Observed evidence"
                              subtitle={`${detail.evidence.length} RETAINED REFERENCES`}
                            />
                            <div className="evidence-grid">
                              {detail.evidence.map((e) => (
                                <a
                                  href={`#evidence-${e.id}`}
                                  key={e.id}
                                  className="evidence-card"
                                >
                                  <img
                                    src={e.url}
                                    alt={`Evidence ${e.id} at ${stamp(e.timestamp)}`}
                                  />
                                  <div>
                                    <span>{stamp(e.timestamp)}</span>
                                    <Provenance value={e.provenance} />
                                  </div>
                                  <p id={`evidence-${e.id}`} className="mono">
                                    REF {e.id.slice(0, 12)}
                                  </p>
                                  <p>
                                    {e.data.count} zone objects · alert latency{" "}
                                    {e.data.event_latency_ms.toFixed(0)}ms
                                  </p>
                                </a>
                              ))}
                              {!detail.evidence.length && (
                                <div className="empty">
                                  Evidence expired or unavailable; factual
                                  claims cannot be independently checked.
                                </div>
                              )}
                            </div>
                            <div className="factor-list">
                              {detail.event.factors.map((factor, index) => (
                                <div key={index}>
                                  <Check size={13} />
                                  <span>{factor}</span>
                                </div>
                              ))}
                            </div>
                          </section>
                          <section className="panel">
                            <PanelHead
                              title="Incident relationships"
                              subtitle="AGGREGATE CORRELATION"
                            />
                            <RelationGraph
                              snapshot={snapshot}
                              selected={detail.id}
                              onSelect={(id) => {
                                if (id !== selectedIncident) setDetail(null);
                                setSelectedIncident(id);
                              }}
                            />
                          </section>
                          <section className="panel investigation-report">
                            <PanelHead
                              title="Evidence-grounded investigation"
                              subtitle={
                                report?.mode || "READ-ONLY LANGGRAPH WORKFLOW"
                              }
                            >
                              <Button
                                className="primary"
                                disabled={busy || !detail.evidence.length}
                                onClick={investigate}
                              >
                                <FileSearch size={14} />
                                {busy
                                  ? "Investigating…"
                                  : report
                                    ? "Re-run investigation"
                                    : "Investigate incident"}
                              </Button>
                            </PanelHead>
                            <div className="question-box">
                              <label>
                                Operator question
                                <input
                                  value={question}
                                  onChange={(e) => setQuestion(e.target.value)}
                                  placeholder="What supports this alert, and what remains uncertain?"
                                  maxLength={500}
                                />
                              </label>
                            </div>
                            {report ? (
                              <div className="report-body">
                                <p className="report-summary">
                                  {report.summary}
                                </p>
                                {report.operator_answer && (
                                  <p className="muted">
                                    {report.operator_answer}
                                  </p>
                                )}
                                <h3>Grounded observations</h3>
                                {report.observations.map((o, index) => (
                                  <div className="grounded-claim" key={index}>
                                    <span>{o.claim}</span>
                                    <div>
                                      {o.evidence_references.map((ref) => (
                                        <a href={`#evidence-${ref}`} key={ref}>
                                          [REF {ref.slice(0, 8)}]
                                        </a>
                                      ))}
                                    </div>
                                  </div>
                                ))}
                                <div className="report-columns">
                                  <div>
                                    <h3>Possible explanations</h3>
                                    {report.possible_explanations.map(
                                      (p, index) => (
                                        <p key={index}>
                                          {p.text}
                                          <small>
                                            Hypothesis ·{" "}
                                            {p.evidence_references
                                              .map((v) => v.slice(0, 8))
                                              .join(", ")}
                                          </small>
                                        </p>
                                      ),
                                    )}
                                    <h3>Missing information</h3>
                                    <ul>
                                      {report.missing_information.map((v) => (
                                        <li key={v}>{v}</li>
                                      ))}
                                    </ul>
                                  </div>
                                  <div>
                                    <h3>Human review steps</h3>
                                    <ol>
                                      {report.recommended_actions.map((v) => (
                                        <li key={v}>{v}</li>
                                      ))}
                                    </ol>
                                  </div>
                                </div>
                                {report.risk && (
                                  <>
                                    <h3>
                                      Experimental risk breakdown ·{" "}
                                      {report.risk.score}/100
                                    </h3>
                                    <div className="risk-bars">
                                      {Object.entries(
                                        report.risk.components,
                                      ).map(([key, value]) => (
                                        <div key={key}>
                                          <span>
                                            {key.replaceAll("_", " ")}
                                          </span>
                                          <div>
                                            <i
                                              style={{
                                                width: `${(value / 35) * 100}%`,
                                              }}
                                            />
                                          </div>
                                          <b>{value.toFixed(1)}</b>
                                        </div>
                                      ))}
                                    </div>
                                  </>
                                )}
                                <div className="limitations">
                                  <h3>Uncertainty & limitations</h3>
                                  {report.limitations.map((v) => (
                                    <p key={v}>{v}</p>
                                  ))}
                                </div>
                                {report.optional_llm_advisory && (
                                  <p className="warning-inline">
                                    {report.optional_llm_advisory.label}:{" "}
                                    {report.optional_llm_advisory.text}
                                  </p>
                                )}
                                <details>
                                  <summary>
                                    Read-only tool trace & retained evidence
                                    references
                                  </summary>
                                  <p>{report.tool_trace.join(" → ")}</p>
                                  <p className="mono">
                                    {report.evidence_references.join(", ")}
                                  </p>
                                </details>
                              </div>
                            ) : (
                              <div className="empty">
                                <FileSearch size={26} />
                                <p>
                                  Run an investigation to retrieve incident
                                  details, correlated events, historical
                                  observations, forecasts and retained evidence.
                                  No API key required.
                                </p>
                              </div>
                            )}
                          </section>
                          <div className="review-grid">
                            <section className="panel">
                              <PanelHead
                                title="Operator review"
                                subtitle="AUDITED ACTIONS"
                              />
                              <div className="review-form">
                                <label>
                                  Review note
                                  <textarea
                                    value={note}
                                    onChange={(e) => setNote(e.target.value)}
                                    placeholder="Record your assessment and any missing context…"
                                    maxLength={2000}
                                  />
                                </label>
                                <div className="review-buttons">
                                  <Button
                                    disabled={
                                      busy ||
                                      ["resolved", "dismissed"].includes(
                                        detail.event.status,
                                      )
                                    }
                                    onClick={() => review("under_review")}
                                  >
                                    <Eye size={14} />
                                    Review
                                  </Button>
                                  <Button
                                    disabled={busy}
                                    onClick={() => review("verified")}
                                  >
                                    <Check size={14} />
                                    Verify
                                  </Button>
                                  <Button
                                    disabled={busy}
                                    onClick={() => review("dismissed")}
                                  >
                                    <X size={14} />
                                    Dismiss
                                  </Button>
                                  <Button
                                    disabled={busy}
                                    onClick={() => review("resolved")}
                                  >
                                    Resolve
                                  </Button>
                                </div>
                                <p className="muted">
                                  Verification records an operator assessment.
                                  No response or enforcement action is
                                  dispatched.
                                </p>
                              </div>
                            </section>
                            <section className="panel">
                              <PanelHead title="Lifecycle timeline" />
                              <div className="timeline">
                                {detail.timeline.map((v, index) => (
                                  <div key={index}>
                                    <i />
                                    <span className="mono">
                                      {stamp(v.timestamp)}
                                    </span>
                                    <strong>
                                      {v.status.replaceAll("_", " ")}
                                    </strong>
                                    <p>{v.note}</p>
                                  </div>
                                ))}
                              </div>
                            </section>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                </>
              )}
              {page === "Predictive intelligence" && (
                <>
                  <div className="section-toolbar">
                    <div>
                      <h2>Zone occupancy forecast</h2>
                      <p>
                        Counts are objects within configured image polygons. No
                        physical crowd density is inferred.
                      </p>
                    </div>
                    <select
                      aria-label="Forecast camera"
                      value={selected}
                      onChange={(e) => setSelected(e.target.value)}
                    >
                      {snapshot.cameras.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="prediction-layout">
                    <section className="panel">
                      <PanelHead
                        title={camera?.name || "Selected zone"}
                        subtitle="MEASURED HISTORY + ESTIMATE"
                      >
                        <Provenance
                          value={latest?.provenance || "unavailable"}
                        />
                      </PanelHead>
                      <ForecastChart snapshot={snapshot} latest={latest} />
                      <div className="chart-legend">
                        <span>
                          <i className="observed-line" />
                          Observed
                        </span>
                        <span>
                          <i className="forecast-line" />
                          Forecast estimate
                        </span>
                        <span>Approximate 95% residual interval</span>
                      </div>
                      <div className="forecast-footnote">
                        {latest?.forecast.ready
                          ? latest.forecast.uncertainty
                          : latest?.forecast.reason ||
                            "Waiting for recent observations."}{" "}
                        Forecasts are estimates, not guarantees.
                      </div>
                    </section>
                    <section className="panel prediction-summary">
                      <PanelHead
                        title="Model context"
                        subtitle="INTERPRETABLE BASELINE"
                      />
                      <dl>
                        <dt>Method</dt>
                        <dd>
                          {latest?.forecast.method ||
                            "Waiting for measured history"}
                        </dd>
                        <dt>Forecast horizon</dt>
                        <dd>{latest?.forecast.horizon ?? "—"} seconds</dd>
                        <dt>Capacity crossing estimate</dt>
                        <dd>
                          {latest?.forecast.threshold_crossing_seconds != null
                            ? `In ${latest.forecast.threshold_crossing_seconds}s`
                            : latest?.forecast.ready
                              ? "No crossing in horizon"
                              : "Insufficient measurements"}
                        </dd>
                        <dt>Recent prediction residual RMSE</dt>
                        <dd>{latest?.forecast.residual_rmse ?? "—"} objects</dd>
                        <dt>Input provenance</dt>
                        <dd>
                          {latest?.provenance === "synthetic"
                            ? "Synthetic trajectories"
                            : "Video inference"}
                        </dd>
                      </dl>
                      <p>
                        Capacity and risk thresholds are experimental operator
                        settings. Residual error is estimated from recent
                        observations and is not a real-world safety accuracy
                        score.
                      </p>
                      <Button onClick={() => setPage("System settings")}>
                        <SlidersHorizontal size={14} />
                        Configure forecast
                      </Button>
                    </section>
                  </div>
                  <section className="panel">
                    <PanelHead
                      title="Zone risk comparison"
                      subtitle="CURRENT OBSERVATIONS"
                    />
                    <div className="table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th>Zone / camera</th>
                            <th>Objects</th>
                            <th>Capacity</th>
                            <th>Occupancy</th>
                            <th>Growth / s</th>
                            <th>Risk / 100</th>
                            <th>Provenance</th>
                          </tr>
                        </thead>
                        <tbody>
                          {snapshot.zones.map((z) => {
                            const l = snapshot.latest.find(
                              (v) => v.zone_id === z.id,
                            );
                            return (
                              <tr
                                key={z.id}
                                onClick={() => setSelected(z.camera_id)}
                                className="clickable"
                              >
                                <td>
                                  {z.name}
                                  <small>{z.camera_id.toUpperCase()}</small>
                                </td>
                                <td>{l?.metrics.count ?? "—"}</td>
                                <td>{z.capacity}</td>
                                <td>
                                  {l
                                    ? Math.round(l.metrics.occupancy * 100) +
                                      "%"
                                    : "—"}
                                </td>
                                <td>{l?.metrics.growth_rate ?? "—"}</td>
                                <td>
                                  <Badge value={l?.risk.level || "normal"} />{" "}
                                  <b>{l?.risk.score ?? "—"}</b>
                                </td>
                                <td>
                                  <Provenance
                                    value={l?.provenance || "unavailable"}
                                  />
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </section>
                </>
              )}
              {page === "System settings" && (
                <>
                  <div className="settings-grid">
                    <section className="panel">
                      <PanelHead
                        title="Camera configuration"
                        subtitle="LOCAL & NETWORK SOURCES"
                      >
                        <Button
                          onClick={() => {
                            setEditCamera(null);
                            setCameraModal(true);
                          }}
                        >
                          <Plus size={14} />
                          Add camera
                        </Button>
                      </PanelHead>
                      <div className="table-wrap">
                        <table>
                          <thead>
                            <tr>
                              <th>Camera</th>
                              <th>Source</th>
                              <th>Status</th>
                              <th>Actions</th>
                            </tr>
                          </thead>
                          <tbody>
                            {snapshot.cameras.map((c) => (
                              <tr key={c.id}>
                                <td>
                                  {c.name}
                                  <small>{c.id}</small>
                                </td>
                                <td>{c.source}</td>
                                <td>
                                  <Badge value={c.health} />
                                </td>
                                <td>
                                  <Button
                                    onClick={() => {
                                      setEditCamera(c);
                                      setCameraModal(true);
                                    }}
                                  >
                                    Edit
                                  </Button>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      <div className="settings-note">
                        Sources: uploaded/local video, webcam and opt-in RTSP.
                        Configure local file sources by placing videos in
                        runtime/media.
                      </div>
                    </section>
                    <section className="panel">
                      <PanelHead
                        title="Zones & regions of interest"
                        subtitle="NORMALIZED IMAGE COORDINATES"
                      />
                      <div className="zone-list">
                        {snapshot.zones.map((z) => (
                          <div key={z.id}>
                            <MapPin size={16} />
                            <span>
                              <strong>{z.name}</strong>
                              <small>
                                {z.capacity} object capacity ·{" "}
                                {z.polygon.length} polygon vertices
                                {z.restricted ? " · restricted" : ""}
                              </small>
                            </span>
                            <Button onClick={() => setZoneModal(z)}>
                              Configure
                            </Button>
                          </div>
                        ))}
                      </div>
                    </section>
                    <section className="panel">
                      <PanelHead
                        title="Detection, risk & forecasting"
                        subtitle="EXPERIMENTAL THRESHOLDS"
                      />
                      {config && (
                        <form
                          className="settings-form"
                          onSubmit={(e) => {
                            e.preventDefault();
                            run(async () => {
                              const saved = await api<Settings>(
                                "/settings",
                                "PUT",
                                config,
                              );
                              setSettings(saved);
                            }, "Intelligence settings saved");
                          }}
                        >
                          <div className="form-grid">
                            {Object.entries(config).map(([key, value]) => (
                              <label key={key}>
                                {key.replaceAll("_", " ")}
                                <input
                                  type="number"
                                  step={key.includes("threshold") ? 0.05 : 1}
                                  value={value}
                                  onChange={(e) =>
                                    setConfig({
                                      ...config,
                                      [key]: Number(e.target.value),
                                    })
                                  }
                                  required
                                />
                              </label>
                            ))}
                          </div>
                          <p>
                            Persistence suppresses single-frame alerts.
                            Thresholds have no scientifically validated safety
                            interpretation.
                          </p>
                          <Button
                            type="submit"
                            className="primary"
                            disabled={busy}
                          >
                            Save intelligence settings
                          </Button>
                        </form>
                      )}
                    </section>
                    <section className="panel">
                      <PanelHead
                        title="System health & privacy"
                        subtitle="LOCAL-FIRST RUNTIME"
                      />
                      <div className="health-body">
                        <dl>
                          <dt>LLM provider</dt>
                          <dd>
                            {settings?.llm.provider || "none"} · deterministic
                            fallback always available
                          </dd>
                          <dt>Configure optional LLM</dt>
                          <dd>
                            LLM_PROVIDER, LLM_BASE_URL, LLM_MODEL, LLM_API_KEY
                            in .env, then restart backend.
                          </dd>
                          <dt>Evidence privacy</dt>
                          <dd>
                            {settings?.privacy.blur_evidence
                              ? "Upper-person-box blurring enabled"
                              : "Blurring disabled"}
                          </dd>
                          <dt>Retention</dt>
                          <dd>
                            {settings?.privacy.evidence_retention_days} days
                            evidence ·{" "}
                            {settings?.privacy.observation_retention_days} days
                            observations
                          </dd>
                          <dt>Database / model</dt>
                          <dd>
                            {String(health?.database || "checking")} /{" "}
                            {health?.model_available
                              ? "available"
                              : "not downloaded"}
                          </dd>
                          <dt>Memory / compute device</dt>
                          <dd>
                            {String(health?.memory_mb ?? "—")} MB /{" "}
                            {settings?.device || "cpu"}
                          </dd>
                          <dt>Engine tick</dt>
                          <dd>{snapshot.health.tick_ms.toFixed(1)} ms</dd>
                          <dt>Authentication</dt>
                          <dd>
                            {String(health?.authentication || "checking")}
                          </dd>
                        </dl>
                        <Button
                          onClick={() =>
                            run(
                              async () =>
                                setHealth(
                                  await api<Record<string, unknown>>("/health"),
                                ),
                              "System health refreshed",
                            )
                          }
                        >
                          <RefreshCw size={14} />
                          Refresh health
                        </Button>
                      </div>
                    </section>
                  </div>
                </>
              )}
              <footer className="workspace-footer">
                <span>
                  <Shield size={12} />
                  PRIVACY-PRESERVING INTELLIGENCE
                </span>
                <span>
                  Experimental research MVP · human verification required
                </span>
                <span>TRINETHRA v0.1</span>
              </footer>
            </>
          )}
        </main>
      </div>
      {toast && (
        <div className="toast" role="status">
          <Check size={16} />
          {toast}
          <button
            onClick={() => setToast("")}
            aria-label="Dismiss notification"
          >
            <X size={14} />
          </button>
        </div>
      )}
      <Modal
        open={!!inspect}
        onOpenChange={(v) => {
          if (!v) setInspect(null);
        }}
        title={
          inspect
            ? `${inspect.name} · ${inspect.id.toUpperCase()}`
            : "Camera inspection"
        }
        wide
      >
        {inspect && snapshot && (
          <>
            <Frame
              camera={
                snapshot.cameras.find((c) => c.id === inspect.id) || inspect
              }
              tick={snapshot.timestamp}
              observedAt={
                snapshot.latest.find((v) => v.camera_id === inspect.id)
                  ?.timestamp
              }
              large
            />
            {inspect.source !== "synthetic" && (
              <details className="recording-original">
                <summary>Play source recording and inspect metadata</summary>
                <video
                  controls
                  preload="metadata"
                  src={`/api/v1/streams/${inspect.id}/video`}
                  aria-label="Original recorded footage"
                />
                <p>
                  Browser-compatible preview of the original recording.
                  Detections above are computed independently from the original
                  frames.
                </p>
                <p>
                  {inspect.source_metadata?.context ||
                    "Operator-supplied source. Validate context before interpreting alerts."}
                </p>
                {inspect.source_metadata?.crop && (
                  <p>
                    Analysis crop:{" "}
                    {JSON.stringify(inspect.source_metadata.crop)} of this
                    original frame.
                  </p>
                )}
                {inspect.source_metadata?.publisher_url && (
                  <a
                    href={inspect.source_metadata.publisher_url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Publisher source
                  </a>
                )}
                <p className="mono">
                  Asset SHA-256:{" "}
                  {inspect.source_metadata?.sha256 ||
                    "Not a downloaded manifest asset"}
                </p>
              </details>
            )}
            <div className="inspection-info">
              {snapshot.latest
                .filter((v) => v.camera_id === inspect.id)
                .map((l) => (
                  <div key={l.zone_id}>
                    <p>
                      Zone:{" "}
                      {snapshot.zones.find((z) => z.id === l.zone_id)?.name}
                    </p>
                    <p>
                      {l.metrics.count} objects ·{" "}
                      {Math.round(l.metrics.occupancy * 100)}% configured
                      occupancy · {l.risk.score}/100 experimental risk
                    </p>
                    <p>
                      Image-plane mean speed {l.metrics.mean_speed}/s · pipeline
                      latency {l.pipeline_latency_ms.toFixed(0)}ms
                    </p>
                    <p>
                      Inference{" "}
                      {l.inference_fps?.toFixed(1) ??
                        (l.provenance === "synthetic"
                          ? "not applicable (simulation)"
                          : "not available")}{" "}
                      FPS · temporary tracks {l.metrics.tracks.length}
                    </p>
                    <Provenance value={l.provenance} />
                  </div>
                ))}
            </div>
          </>
        )}
      </Modal>
      <Modal
        open={cameraModal}
        onOpenChange={setCameraModal}
        title={editCamera ? "Configure camera" : "Add camera"}
      >
        <CameraForm
          initial={editCamera}
          onSave={(data) =>
            run(async () => {
              await api(
                editCamera ? `/cameras/${editCamera.id}` : "/cameras",
                editCamera ? "PUT" : "POST",
                data,
              );
              setCameraModal(false);
            }, "Camera configuration saved")
          }
          busy={busy}
        />
      </Modal>
      <Modal
        open={!!zoneModal}
        onOpenChange={(v) => {
          if (!v) setZoneModal(null);
        }}
        title="Configure zone & region of interest"
      >
        {zoneModal && (
          <ZoneForm
            zone={zoneModal}
            onSave={(data) =>
              run(async () => {
                await api(`/zones/${zoneModal.id}`, "PUT", data);
                setZoneModal(null);
              }, "Region of interest saved")
            }
            busy={busy}
          />
        )}
      </Modal>
    </div>
  );
}
function PanelHead({
  title,
  subtitle,
  children,
}: {
  title?: string;
  subtitle?: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="panel-head">
      <div>
        <h2>{title}</h2>
        {subtitle && <span>{subtitle}</span>}
      </div>
      <div className="panel-tools">{children}</div>
    </div>
  );
}
function Stat({
  label,
  value,
  suffix,
  sub,
  icon: Icon,
  tone = "neutral",
}: {
  label: string;
  value: string;
  suffix?: string;
  sub: string;
  icon: typeof Activity;
  tone?: string;
}) {
  return (
    <section className={cn("stat", tone)}>
      <div className="stat-label">
        {label}
        <Icon size={16} />
      </div>
      <div className="stat-value">
        {value}
        <span>{suffix}</span>
      </div>
      <p>{sub}</p>
    </section>
  );
}
function CameraForm({
  initial,
  onSave,
  busy,
}: {
  initial: Camera | null;
  onSave: (data: unknown) => void;
  busy: boolean;
}) {
  const [form, setForm] = useState({
    name: initial?.name || "",
    lat: initial?.lat || 17.0001,
    lon: initial?.lon || 81.804,
    kind: initial?.kind || "crowd",
    source: initial?.source === "synthetic" ? "synthetic" : "",
    enabled: initial?.enabled ?? true,
  });
  const [uploading, setUploading] = useState(false),
    [error, setError] = useState("");
  useEffect(
    () =>
      setForm({
        name: initial?.name || "",
        lat: initial?.lat || 17.0001,
        lon: initial?.lon || 81.804,
        kind: initial?.kind || "crowd",
        source: initial?.source === "synthetic" ? "synthetic" : "",
        enabled: initial?.enabled ?? true,
      }),
    [initial],
  );
  return (
    <form
      className="settings-form"
      onSubmit={(e) => {
        e.preventDefault();
        onSave(form);
      }}
    >
      <label>
        Camera name
        <input
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          required
          maxLength={100}
        />
      </label>
      <div className="form-grid">
        <label>
          Latitude
          <input
            type="number"
            step=".000001"
            min="-90"
            max="90"
            value={form.lat}
            onChange={(e) => setForm({ ...form, lat: Number(e.target.value) })}
            required
          />
        </label>
        <label>
          Longitude
          <input
            type="number"
            step=".000001"
            min="-180"
            max="180"
            value={form.lon}
            onChange={(e) => setForm({ ...form, lon: Number(e.target.value) })}
            required
          />
        </label>
      </div>
      <label>
        Analytics mode
        <select
          value={form.kind}
          onChange={(e) => setForm({ ...form, kind: e.target.value })}
        >
          <option value="crowd">Crowd intelligence</option>
          <option value="road">Road safety</option>
        </select>
      </label>
      <label>
        Source
        <input
          value={form.source}
          onChange={(e) => setForm({ ...form, source: e.target.value })}
          placeholder={
            initial
              ? "Leave blank to keep current source"
              : "media:filename.mp4, webcam:0 or rtsp://…"
          }
          required={!initial}
        />
      </label>
      <p className="muted">
        Leave the source blank to preserve an existing recording, or upload a
        replacement. Credentials are never returned by the API.
      </p>
      <label className="upload-field">
        <Upload size={17} />
        {uploading ? "Validating video…" : "Upload video (max 250 MiB)"}
        <input
          type="file"
          accept="video/*"
          disabled={uploading}
          onChange={async (e) => {
            if (!e.target.files?.[0]) return;
            setUploading(true);
            setError("");
            try {
              const data = new FormData();
              data.append("file", e.target.files[0]);
              const result = await api<{ source: string }>(
                "/streams/upload",
                "POST",
                data,
              );
              setForm({ ...form, source: result.source });
            } catch (e) {
              setError((e as Error).message);
            } finally {
              setUploading(false);
            }
          }}
        />
      </label>
      <label className="checkbox-label">
        <input
          type="checkbox"
          checked={form.enabled}
          onChange={(e) => setForm({ ...form, enabled: e.target.checked })}
        />
        Enable source
      </label>
      {error && <p className="error-text">{error}</p>}
      <Button className="primary" type="submit" disabled={busy || uploading}>
        {busy ? "Saving…" : "Save camera"}
      </Button>
    </form>
  );
}
function ZoneForm({
  zone,
  onSave,
  busy,
}: {
  zone: Zone;
  onSave: (data: unknown) => void;
  busy: boolean;
}) {
  const [name, setName] = useState(zone.name),
    [capacity, setCapacity] = useState(zone.capacity),
    [polygon, setPolygon] = useState(JSON.stringify(zone.polygon)),
    [restricted, setRestricted] = useState(zone.restricted),
    [error, setError] = useState("");
  return (
    <form
      className="settings-form"
      onSubmit={(e) => {
        e.preventDefault();
        try {
          onSave({
            camera_id: zone.camera_id,
            name,
            capacity,
            polygon: JSON.parse(polygon),
            restricted,
          });
        } catch {
          setError("Enter valid JSON coordinates.");
        }
      }}
    >
      <label>
        Zone name
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
      </label>
      <label>
        Capacity (counted objects, not physical density)
        <input
          type="number"
          min="1"
          max="100000"
          value={capacity}
          onChange={(e) => setCapacity(Number(e.target.value))}
          required
        />
      </label>
      <label>
        ROI polygon · normalized [x,y] coordinates
        <textarea
          value={polygon}
          onChange={(e) => setPolygon(e.target.value)}
          required
          rows={4}
        />
      </label>
      <p>
        Each point must lie in [0,1] × [0,1]. Use a nonzero-area polygon with at
        least three vertices. Camera preview draws the saved region.
      </p>
      <label className="checkbox-label">
        <input
          type="checkbox"
          checked={restricted}
          onChange={(e) => setRestricted(e.target.checked)}
        />
        Restricted stopping zone (road mode)
      </label>
      {error && <p className="error-text">{error}</p>}
      <Button type="submit" className="primary" disabled={busy}>
        Save zone
      </Button>
    </form>
  );
}
