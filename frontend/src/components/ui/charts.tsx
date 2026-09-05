"use client";

import React, { useState } from "react";
import { LoadingState } from "@/components/ui/loading-state";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { cn } from "@/lib/utils";

export interface ChartDataPoint {
  label: string;
  value: number;
  secondaryValue?: number;
  color?: string;
}

export interface BaseChartProps {
  title?: string;
  description?: string;
  data: ChartDataPoint[];
  isLoading?: boolean;
  error?: string | null;
  onRetry?: () => void;
  emptyTitle?: string;
  emptyDescription?: string;
  height?: number;
  className?: string;
  valuePrefix?: string;
  valueSuffix?: string;
}

export function ChartWrapper({
  title,
  description,
  isLoading,
  error,
  onRetry,
  isEmpty,
  emptyTitle = "No chart data available",
  emptyDescription = "There are currently no metric points to plot on this visualization.",
  children,
  className,
}: {
  title?: string;
  description?: string;
  isLoading?: boolean;
  error?: string | null;
  onRetry?: () => void;
  isEmpty?: boolean;
  emptyTitle?: string;
  emptyDescription?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      role="region"
      aria-label={title || "Chart Visualization"}
      className={cn("rounded-xl border border-border bg-card p-6 shadow-sm", className)}
    >
      {(title || description) && (
        <div className="mb-6 space-y-1">
          {title && <h4 className="text-base font-bold text-foreground">{title}</h4>}
          {description && <p className="text-xs text-muted">{description}</p>}
        </div>
      )}

      {error ? (
        <ErrorState variant="generic" message={error} onRetry={onRetry} />
      ) : isLoading ? (
        <LoadingState variant="spinner" message="Preparing visualization data..." />
      ) : isEmpty ? (
        <EmptyState title={emptyTitle} description={emptyDescription} />
      ) : (
        children
      )}
    </div>
  );
}

// 1. Line Chart
export function LineChart({
  title,
  description,
  data,
  isLoading,
  error,
  onRetry,
  height = 240,
  valuePrefix = "",
  valueSuffix = "",
  className,
}: BaseChartProps) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  if (isLoading || error || !data || data.length === 0) {
    return (
      <ChartWrapper
        title={title}
        description={description}
        isLoading={isLoading}
        error={error}
        onRetry={onRetry}
        isEmpty={!data || data.length === 0}
        className={className}
      >
        <div />
      </ChartWrapper>
    );
  }

  const padding = 40;
  const width = 600;
  const chartWidth = width - padding * 2;
  const chartHeight = height - padding * 2;

  const maxValue = Math.max(...data.map((d) => d.value), 10);
  const minValue = 0;

  const getX = (index: number) =>
    padding + (index / (data.length - 1 || 1)) * chartWidth;
  const getY = (val: number) =>
    padding + chartHeight - ((val - minValue) / (maxValue - minValue)) * chartHeight;

  const points = data.map((d, i) => `${getX(i)},${getY(d.value)}`).join(" ");

  return (
    <ChartWrapper title={title} description={description} className={className}>
      <div className="relative w-full overflow-hidden" tabIndex={0} role="img" aria-label={`Line chart: ${title || "metrics"}`}>
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-auto overflow-visible"
          style={{ maxHeight: height }}
        >
          {/* Horizontal gridlines */}
          {[0, 0.25, 0.5, 0.75, 1].map((pct, idx) => {
            const y = padding + chartHeight * (1 - pct);
            const val = Math.round(minValue + (maxValue - minValue) * pct);
            return (
              <g key={idx} className="text-slate-200">
                <line
                  x1={padding}
                  y1={y}
                  x2={width - padding}
                  y2={y}
                  stroke="currentColor"
                  strokeDasharray="4 4"
                  strokeWidth="1"
                />
                <text
                  x={padding - 8}
                  y={y + 4}
                  textAnchor="end"
                  className="fill-slate-400 text-[10px]"
                >
                  {val}
                </text>
              </g>
            );
          })}

          {/* Line Path */}
          <polyline
            fill="none"
            stroke="#2563eb"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
            points={points}
          />

          {/* Data Points */}
          {data.map((d, i) => {
            const cx = getX(i);
            const cy = getY(d.value);
            const isHovered = hoveredIdx === i;

            return (
              <g key={i}>
                <circle
                  cx={cx}
                  cy={cy}
                  r={isHovered ? 6 : 4}
                  fill="#ffffff"
                  stroke="#2563eb"
                  strokeWidth="3"
                  className="cursor-pointer transition-all duration-150"
                  onMouseEnter={() => setHoveredIdx(i)}
                  onMouseLeave={() => setHoveredIdx(null)}
                />
                <text
                  x={cx}
                  y={height - padding + 18}
                  textAnchor="middle"
                  className="fill-slate-500 text-[11px] font-medium"
                >
                  {d.label}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Floating tooltip */}
        {hoveredIdx !== null && (
          <div
            className="absolute rounded-lg border border-border bg-slate-900 px-2.5 py-1 text-xs text-white shadow-md pointer-events-none transform -translate-x-1/2 -translate-y-8"
            style={{
              left: `${(getX(hoveredIdx) / width) * 100}%`,
              top: `${(getY(data[hoveredIdx].value) / height) * 100}%`,
            }}
          >
            <span className="font-semibold">{data[hoveredIdx].label}: </span>
            <span>{valuePrefix}{data[hoveredIdx].value}{valueSuffix}</span>
          </div>
        )}
      </div>
    </ChartWrapper>
  );
}

// 2. Bar Chart
export function BarChart({
  title,
  description,
  data,
  isLoading,
  error,
  onRetry,
  height = 240,
  valuePrefix = "",
  valueSuffix = "",
  className,
}: BaseChartProps) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  if (isLoading || error || !data || data.length === 0) {
    return (
      <ChartWrapper
        title={title}
        description={description}
        isLoading={isLoading}
        error={error}
        onRetry={onRetry}
        isEmpty={!data || data.length === 0}
        className={className}
      >
        <div />
      </ChartWrapper>
    );
  }

  const padding = 40;
  const width = 600;
  const chartWidth = width - padding * 2;
  const chartHeight = height - padding * 2;
  const maxValue = Math.max(...data.map((d) => d.value), 10);

  const barWidth = Math.max(16, Math.min(48, (chartWidth / data.length) * 0.6));
  const step = chartWidth / data.length;

  return (
    <ChartWrapper title={title} description={description} className={className}>
      <div className="relative w-full overflow-hidden" tabIndex={0} role="img" aria-label={`Bar chart: ${title || "metrics"}`}>
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-auto overflow-visible"
          style={{ maxHeight: height }}
        >
          {/* Horizontal gridlines */}
          {[0, 0.5, 1].map((pct, idx) => {
            const y = padding + chartHeight * (1 - pct);
            const val = Math.round(maxValue * pct);
            return (
              <g key={idx} className="text-slate-200">
                <line
                  x1={padding}
                  y1={y}
                  x2={width - padding}
                  y2={y}
                  stroke="currentColor"
                  strokeDasharray="4 4"
                  strokeWidth="1"
                />
                <text
                  x={padding - 8}
                  y={y + 4}
                  textAnchor="end"
                  className="fill-slate-400 text-[10px]"
                >
                  {val}
                </text>
              </g>
            );
          })}

          {/* Bars */}
          {data.map((d, i) => {
            const barHeight = (d.value / maxValue) * chartHeight;
            const x = padding + i * step + (step - barWidth) / 2;
            const y = padding + chartHeight - barHeight;
            const isHovered = hoveredIdx === i;
            const fill = d.color || "#3b82f6";

            return (
              <g key={i}>
                <rect
                  x={x}
                  y={y}
                  width={barWidth}
                  height={barHeight}
                  rx="4"
                  fill={fill}
                  className={cn(
                    "cursor-pointer transition-opacity duration-150",
                    isHovered ? "opacity-100" : "opacity-85"
                  )}
                  onMouseEnter={() => setHoveredIdx(i)}
                  onMouseLeave={() => setHoveredIdx(null)}
                />
                <text
                  x={x + barWidth / 2}
                  y={height - padding + 18}
                  textAnchor="middle"
                  className="fill-slate-500 text-[11px] font-medium"
                >
                  {d.label}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Tooltip */}
        {hoveredIdx !== null && (
          <div
            className="absolute rounded-lg border border-border bg-slate-900 px-2.5 py-1 text-xs text-white shadow-md pointer-events-none transform -translate-x-1/2 -translate-y-8"
            style={{
              left: `${((padding + hoveredIdx * step + step / 2) / width) * 100}%`,
              top: `${((padding + chartHeight - (data[hoveredIdx].value / maxValue) * chartHeight) / height) * 100}%`,
            }}
          >
            <span className="font-semibold">{data[hoveredIdx].label}: </span>
            <span>{valuePrefix}{data[hoveredIdx].value}{valueSuffix}</span>
          </div>
        )}
      </div>
    </ChartWrapper>
  );
}

// 3. Area Chart
export function AreaChart({
  title,
  description,
  data,
  isLoading,
  error,
  onRetry,
  height = 240,
  valuePrefix = "",
  valueSuffix = "",
  className,
}: BaseChartProps) {
  if (isLoading || error || !data || data.length === 0) {
    return (
      <ChartWrapper
        title={title}
        description={description}
        isLoading={isLoading}
        error={error}
        onRetry={onRetry}
        isEmpty={!data || data.length === 0}
        className={className}
      >
        <div />
      </ChartWrapper>
    );
  }

  const padding = 40;
  const width = 600;
  const chartWidth = width - padding * 2;
  const chartHeight = height - padding * 2;

  const maxValue = Math.max(...data.map((d) => d.value), 10);
  const minValue = 0;

  const getX = (index: number) =>
    padding + (index / (data.length - 1 || 1)) * chartWidth;
  const getY = (val: number) =>
    padding + chartHeight - ((val - minValue) / (maxValue - minValue)) * chartHeight;

  const linePoints = data.map((d, i) => `${getX(i)},${getY(d.value)}`).join(" ");
  const areaPoints = `${getX(0)},${padding + chartHeight} ${linePoints} ${getX(data.length - 1)},${padding + chartHeight}`;

  return (
    <ChartWrapper title={title} description={description} className={className}>
      <div className="relative w-full overflow-hidden" tabIndex={0} role="img" aria-label={`Area chart: ${title || "metrics"}`}>
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-auto overflow-visible"
          style={{ maxHeight: height }}
        >
          <defs>
            <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#2563eb" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#2563eb" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Area Fill */}
          <polygon points={areaPoints} fill="url(#areaGradient)" />

          {/* Outline Line */}
          <polyline
            fill="none"
            stroke="#2563eb"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            points={linePoints}
          />

          {/* Labels */}
          {data.map((d, i) => (
            <text
              key={i}
              x={getX(i)}
              y={height - padding + 18}
              textAnchor="middle"
              className="fill-slate-500 text-[11px] font-medium"
            >
              {d.label}
            </text>
          ))}
        </svg>
      </div>
    </ChartWrapper>
  );
}

// 4. Donut Chart
export function DonutChart({
  title,
  description,
  data,
  isLoading,
  error,
  onRetry,
  height = 240,
  className,
}: BaseChartProps) {
  if (isLoading || error || !data || data.length === 0) {
    return (
      <ChartWrapper
        title={title}
        description={description}
        isLoading={isLoading}
        error={error}
        onRetry={onRetry}
        isEmpty={!data || data.length === 0}
        className={className}
      >
        <div />
      </ChartWrapper>
    );
  }

  const defaultColors = ["#2563eb", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"];
  const total = data.reduce((acc, curr) => acc + curr.value, 0) || 1;

  let cumulativeAngle = 0;
  const radius = 65;
  const innerRadius = 45;
  const center = 100;

  const slices = data.map((d, idx) => {
    const fraction = d.value / total;
    const startAngle = cumulativeAngle;
    const endAngle = cumulativeAngle + fraction * 2 * Math.PI;
    cumulativeAngle = endAngle;

    const x1 = center + radius * Math.sin(startAngle);
    const y1 = center - radius * Math.cos(startAngle);
    const x2 = center + radius * Math.sin(endAngle);
    const y2 = center - radius * Math.cos(endAngle);

    const ix1 = center + innerRadius * Math.sin(endAngle);
    const iy1 = center - innerRadius * Math.cos(endAngle);
    const ix2 = center + innerRadius * Math.sin(startAngle);
    const iy2 = center - innerRadius * Math.cos(startAngle);

    const largeArc = fraction > 0.5 ? 1 : 0;
    const pathData = `M ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} L ${ix1} ${iy1} A ${innerRadius} ${innerRadius} 0 ${largeArc} 0 ${ix2} ${iy2} Z`;

    return {
      pathData,
      color: d.color || defaultColors[idx % defaultColors.length],
      label: d.label,
      value: d.value,
      percentage: Math.round(fraction * 100),
    };
  });

  return (
    <ChartWrapper title={title} description={description} className={className}>
      <div className="flex flex-col sm:flex-row items-center justify-center gap-6" role="img" aria-label={`Donut chart: ${title || "distribution"}`}>
        <svg viewBox="0 0 200 200" className="h-44 w-44 shrink-0">
          {slices.map((s, i) => (
            <path key={i} d={s.pathData} fill={s.color} className="transition-opacity hover:opacity-85" />
          ))}
        </svg>

        {/* Legend */}
        <div className="flex flex-col gap-2 text-xs">
          {slices.map((s, i) => (
            <div key={i} className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-full shrink-0" style={{ backgroundColor: s.color }} />
              <span className="font-medium text-slate-700">{s.label}:</span>
              <span className="text-muted font-mono">{s.value} ({s.percentage}%)</span>
            </div>
          ))}
        </div>
      </div>
    </ChartWrapper>
  );
}
