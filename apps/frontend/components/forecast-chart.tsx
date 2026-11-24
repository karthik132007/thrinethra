"use client";
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
} from "recharts";
import type { Snapshot, Latest } from "./types";
export function ForecastChart({
  snapshot,
  latest,
  compact = false,
}: {
  snapshot: Snapshot;
  latest?: Latest;
  compact?: boolean;
}) {
  if (!latest) return <div className="empty">Waiting for observations</div>;
  const history = snapshot.history[latest.zone_id] || [];
  const zone = snapshot.zones.find((z) => z.id === latest.zone_id);
  const historical = history.map((v, index) => ({
    time: v.timestamp * 1000,
    observed: v.count,
    predicted: index === history.length - 1 ? v.count : undefined,
    band: undefined as number[] | undefined,
  }));
  const predicted = latest.forecast.points.map((v) => ({
    time: v.timestamp * 1000,
    observed: undefined,
    predicted: v.value,
    band: [v.lower, v.upper],
  }));
  return (
    <div style={{ height: compact ? 180 : 310, width: "100%" }}>
      <ResponsiveContainer>
        <ComposedChart
          data={[...historical, ...predicted]}
          margin={{ top: 15, right: 15, bottom: 5, left: -20 }}
        >
          <CartesianGrid stroke="#293238" vertical={false} />
          <XAxis
            dataKey="time"
            type="number"
            domain={["dataMin", "dataMax"]}
            tickFormatter={(v) =>
              new Date(v).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
              })
            }
            minTickGap={60}
            tick={{ fill: "#8d9ba4", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: "#8d9ba4", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            allowDecimals={false}
          />
          <Tooltip
            contentStyle={{
              background: "#182127",
              border: "1px solid #3b484f",
              borderRadius: 4,
              color: "#e5ebef",
            }}
            labelFormatter={(v) => new Date(Number(v)).toLocaleTimeString()}
          />
          {zone && (
            <ReferenceLine
              y={zone.capacity}
              stroke="#a17f47"
              strokeDasharray="4 4"
              label={{
                value: "Capacity",
                fill: "#bca579",
                fontSize: 11,
                position: "insideTopLeft",
              }}
            />
          )}
          <Area
            dataKey="band"
            stroke="none"
            fill="#c5aa73"
            fillOpacity={0.12}
            name="Approx. interval"
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="observed"
            stroke="#8cbcb0"
            dot={false}
            strokeWidth={2}
            connectNulls={false}
            isAnimationActive={false}
            name="Observed count"
          />
          <Line
            type="monotone"
            dataKey="predicted"
            stroke="#d8b16f"
            strokeDasharray="5 4"
            dot={false}
            strokeWidth={2}
            connectNulls={false}
            isAnimationActive={false}
            name="Forecast estimate"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
