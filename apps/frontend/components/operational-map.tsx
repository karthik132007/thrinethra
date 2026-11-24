"use client";
import { useEffect, useRef } from "react";
import type LType from "leaflet";
import type { Snapshot } from "./types";
const schematic = `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="850" viewBox="0 0 1200 850"><rect width="1200" height="850" fill="#1a242a"/><g fill="#202e34" stroke="#324048" stroke-width="2"><path d="M0 0H410V180H0Z"/><path d="M470 0H800V180H470Z"/><path d="M860 0H1200V180H860Z"/><path d="M0 240H180V500H0Z"/><path d="M240 240H600V500H240Z"/><path d="M660 240H890V500H660Z"/><path d="M950 240H1200V500H950Z"/><path d="M0 560H320V850H0Z"/><path d="M380 560H720V850H380Z"/><path d="M780 560H1200V850H780Z"/></g><g fill="#293b39" stroke="#3b4b43"><rect x="290" y="280" width="260" height="170" rx="5"/><rect x="840" y="610" width="210" height="150" rx="5"/><rect x="40" y="35" width="300" height="100" rx="5"/></g><g fill="none" stroke="#465158" stroke-dasharray="12 10"><path d="M0 210H1200M0 530H1200M440 0V210M830 0V210M210 210V530M630 210V530M920 210V530M350 530V850M750 530V850"/></g><g fill="#71818b" font-family="monospace" font-size="16" letter-spacing="3"><text x="300" y="370">EAST CONCOURSE</text><text x="670" y="360">TRANSIT PLAZA</text><text x="420" y="690">SOUTH ENTRANCE</text><text x="940" y="700">RIVERSIDE</text><text x="440" y="205" font-size="12">CAMPUS AVENUE</text><text x="500" y="525" font-size="12">RIVER ROAD</text><text x="45" y="90">PUBLIC GARDENS</text></g><g fill="#31473f"><circle cx="310" cy="300" r="12"/><circle cx="530" cy="410" r="12"/><circle cx="875" cy="640" r="12"/><circle cx="1000" cy="740" r="12"/></g></svg>`;
export default function OperationalMap({
  snapshot,
  selected,
  onSelect,
  street = false,
  fit = 0,
}: {
  snapshot: Snapshot;
  selected: string;
  onSelect: (id: string) => void;
  street?: boolean;
  fit?: number;
}) {
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<LType.Map | null>(null);
  const layer = useRef<LType.LayerGroup | null>(null);
  const library = useRef<typeof LType | null>(null);
  const base = useRef<LType.Layer | null>(null);
  const callback = useRef(onSelect);
  callback.current = onSelect;
  useEffect(() => {
    let cancelled = false;
    import("leaflet").then((L) => {
      if (cancelled || !container.current) return;
      library.current = L;
      const m = L.map(container.current, {
        zoomControl: false,
        attributionControl: true,
        minZoom: 14,
        maxZoom: 19,
      }).setView([16.9998, 81.8046], 17);
      map.current = m;
      layer.current = L.layerGroup().addTo(m);
      L.control.zoom({ position: "bottomright" }).addTo(m);
      const observer = new ResizeObserver(() => m.invalidateSize());
      observer.observe(container.current!);
      (m as LType.Map & { cleanup?: () => void }).cleanup = () =>
        observer.disconnect();
      m.fire("ready");
    });
    return () => {
      cancelled = true;
      if (map.current) {
        (map.current as LType.Map & { cleanup?: () => void }).cleanup?.();
        map.current.remove();
        map.current = null;
      }
    };
  }, []);
  useEffect(() => {
    const timer = setInterval(() => {
      const L = library.current,
        m = map.current;
      if (!L || !m) return;
      clearInterval(timer);
      if (base.current) m.removeLayer(base.current);
      base.current = street
        ? L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: "© OpenStreetMap contributors",
            maxZoom: 19,
          })
        : L.imageOverlay(
            "data:image/svg+xml;charset=UTF-8," + encodeURIComponent(schematic),
            [
              [16.9975, 81.8017],
              [17.002, 81.8077],
            ],
            { attribution: "Fictional demo campus · schematic geography" },
          );
      base.current.addTo(m);
    }, 100);
    return () => clearInterval(timer);
  }, [street]);
  useEffect(() => {
    const timer = setInterval(() => {
      const L = library.current,
        m = map.current,
        g = layer.current;
      if (!L || !m || !g) return;
      clearInterval(timer);
      g.clearLayers();
      for (const connection of snapshot.connections) {
        const a = snapshot.cameras.find((c) => c.id === connection.camera_a),
          b = snapshot.cameras.find((c) => c.id === connection.camera_b);
        if (a && b)
          L.polyline(
            [
              [a.lat, a.lon],
              [b.lat, b.lon],
            ],
            { color: "#70838b", weight: 1, dashArray: "5 7", opacity: 0.55 },
          ).addTo(g);
      }
      for (const camera of snapshot.cameras) {
        const latest = snapshot.latest.find((v) => v.camera_id === camera.id);
        const risk = latest?.risk.score || 0;
        const color =
          risk >= 75 ? "#f27764" : risk >= 50 ? "#e4ae59" : "#82afa4";
        if (risk >= 25)
          L.circle([camera.lat, camera.lon], {
            radius: 55 + Math.min(risk, 100),
            color,
            weight: 1,
            fillColor: color,
            fillOpacity: 0.07,
          }).addTo(g);
        const icon = L.divIcon({
          className: "map-camera-container",
          html: `<div class="map-camera ${camera.id === selected ? "chosen" : ""}" style="--pin:${color}"><svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><rect x="3" y="6" width="12" height="12" rx="2"/><path d="m15 10 6-3v10l-6-3"/></svg></div><span class="map-label">${camera.id.replace(/[^a-zA-Z0-9-]/g, "").toUpperCase()}</span>`,
          iconSize: [38, 55],
          iconAnchor: [19, 19],
        });
        L.marker([camera.lat, camera.lon], {
          icon,
          keyboard: true,
          title: camera.name,
        })
          .on("click", () => callback.current(camera.id))
          .addTo(g);
      }
    }, 100);
    return () => clearInterval(timer);
  }, [snapshot, selected]);
  useEffect(() => {
    map.current?.setView([16.9998, 81.8046], 17);
  }, [fit]);
  return (
    <div
      ref={container}
      className="operational-map"
      aria-label="Interactive camera map"
    />
  );
}
