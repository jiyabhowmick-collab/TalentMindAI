"use client";

import React from "react";
import { Upload, Cpu, ListOrdered, CheckCircle2 } from "lucide-react";
import type { RankStep } from "@/services/api";

// Keep Stage exported for any code that still imports it
export type Stage = "idle" | "uploading" | "processing" | "ranking" | "done" | "error";

interface ProgressTrackerProps {
  step: RankStep;          // 0=uploading 1=processing 2=ranking 3=done
  totalCandidates?: number;
}

// ---------------------------------------------------------------------------
// Step metadata
// ---------------------------------------------------------------------------

const STEPS = [
  { label: "Uploading",  icon: Upload      },
  { label: "Processing", icon: Cpu         },
  { label: "Ranking",    icon: ListOrdered },
  { label: "Done",       icon: CheckCircle2},
] as const;

// Progress bar target % per step
const STEP_PROGRESS: Record<RankStep, number> = { 0: 15, 1: 40, 2: 75, 3: 100 };

// Bar colour per step
const STEP_BAR_COLOR: Record<RankStep, string> = {
  0: "#ef4444",  // red    — uploading
  1: "#f59e0b",  // amber  — processing
  2: "#eab308",  // yellow — ranking
  3: "#22c55e",  // green  — done
};

// Status line per step
const STATUS_TEXT: Record<RankStep, string> = {
  0: "Uploading file...",
  1: "Parsing candidates...",
  2: "Ranking in progress...",
  3: "Ranking complete!",
};

// ---------------------------------------------------------------------------
// Colours
// ---------------------------------------------------------------------------
const C_DONE    = "#22c55e";
const C_ACTIVE  = "#eab308";
const C_PENDING = "rgba(255,255,255,0.25)";

const BG_DONE    = "rgba(34,197,94,0.15)";
const BG_ACTIVE  = "rgba(234,179,8,0.15)";
const BG_PENDING = "transparent";

const BORDER_DONE    = `1.5px solid ${C_DONE}`;
const BORDER_ACTIVE  = `1.5px solid ${C_ACTIVE}`;
const BORDER_PENDING = "1.5px solid rgba(255,255,255,0.12)";

// ---------------------------------------------------------------------------
// CSS injected once
// ---------------------------------------------------------------------------

const TRACKER_CSS = `
@keyframes activePulse {
  0%,100% { box-shadow: 0 0 0 0 rgba(234,179,8,0.35); }
  50%      { box-shadow: 0 0 0 8px rgba(234,179,8,0); }
}
@keyframes flowRight {
  0%   { background-position: 100% 0; }
  100% { background-position: -100% 0; }
}
`;

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function ProgressTracker({ step, totalCandidates }: ProgressTrackerProps) {
  const progressPct = STEP_PROGRESS[step];
  const barColor    = STEP_BAR_COLOR[step];
  const statusColor = barColor;                    // status text matches bar
  const isDone      = step === 3;

  return (
    <div
      style={{
        width:        "100%",
        borderRadius: "16px",
        border:       "1px solid rgba(255,255,255,0.10)",
        background:   "rgba(255,255,255,0.02)",
        padding:      "24px",
      }}
    >
      <style>{TRACKER_CSS}</style>

      {/* ── Step icons + connectors ──────────────────────────────────── */}
      <div style={{ display: "flex", alignItems: "center", marginBottom: "24px" }}>
        {STEPS.map((s, i) => {
          const Icon     = s.icon;
          const isPast   = i < step;
          const isActive = i === step;
          // Done label gets indigo/purple
          const isLast   = i === 3;

          const bg     = isPast ? BG_DONE : isActive ? BG_ACTIVE : BG_PENDING;
          const border = isPast ? BORDER_DONE : isActive ? BORDER_ACTIVE : BORDER_PENDING;
          const color  = isPast ? C_DONE : isActive ? C_ACTIVE : C_PENDING;
          const anim   = isActive ? "activePulse 2s ease infinite" : "none";

          const labelColor = isLast && isPast
            ? "#818cf8"
            : isLast && isActive
            ? "#818cf8"
            : isPast
            ? C_DONE
            : isActive
            ? C_ACTIVE
            : "rgba(255,255,255,0.28)";

          return (
            <React.Fragment key={s.label}>
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "8px" }}>
                {/* Icon circle */}
                <div
                  style={{
                    display:        "flex",
                    alignItems:     "center",
                    justifyContent: "center",
                    width:          "44px",
                    height:         "44px",
                    borderRadius:   "50%",
                    background:     bg,
                    border,
                    color,
                    animation:      anim,
                    transition:     "background 0.4s, border-color 0.4s, color 0.4s",
                    flexShrink:     0,
                  }}
                >
                  <Icon size={18} />
                </div>

                {/* Label */}
                <span
                  style={{
                    fontSize:   "12px",
                    fontWeight: 500,
                    color:      labelColor,
                    transition: "color 0.4s",
                    whiteSpace: "nowrap",
                  }}
                >
                  {s.label}
                </span>
              </div>

              {/* Connector line */}
              {i < STEPS.length - 1 && (
                <div
                  style={{
                    flex:         1,
                    height:       isPast ? "2px" : "1px",
                    margin:       "0 6px",
                    marginBottom: "20px",  // align with icon midpoints
                    borderRadius: "1px",
                    overflow:     "hidden",
                    background:   "rgba(255,255,255,0.10)",
                    position:     "relative",
                    transition:   "height 0.3s",
                  }}
                >
                  {/* Filled / animated fill */}
                  {isPast && (
                    <div style={{ position: "absolute", inset: 0, background: C_DONE }} />
                  )}
                  {isActive && (
                    <div
                      style={{
                        position:           "absolute",
                        inset:              0,
                        background:         `linear-gradient(90deg, ${C_DONE} 0%, ${C_ACTIVE} 50%, rgba(255,255,255,0.1) 100%)`,
                        backgroundSize:     "200% 100%",
                        animation:          "flowRight 1.5s linear infinite",
                      }}
                    />
                  )}
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* ── Progress bar ─────────────────────────────────────────────── */}
      <div
        style={{
          width:        "100%",
          height:       "6px",
          borderRadius: "3px",
          background:   "rgba(255,255,255,0.08)",
          overflow:     "hidden",
        }}
      >
        <div
          style={{
            width:           `${progressPct}%`,
            height:          "100%",
            borderRadius:    "3px",
            background:      barColor,
            transition:      "width 0.9s cubic-bezier(0.4,0,0.2,1), background-color 0.6s ease",
          }}
        />
      </div>

      {/* ── Status text ──────────────────────────────────────────────── */}
      <div
        style={{
          marginTop:      "16px",
          display:        "flex",
          alignItems:     "center",
          justifyContent: "space-between",
        }}
      >
        <span style={{ fontSize: "14px", color: statusColor, transition: "color 0.4s" }}>
          {STATUS_TEXT[step]}
        </span>

        {/* Candidate count — only on Done step */}
        {isDone && totalCandidates !== undefined && totalCandidates > 0 && (
          <span
            style={{
              fontSize:          "12px",
              color:             "rgba(255,255,255,0.3)",
              fontVariantNumeric:"tabular-nums",
            }}
          >
            {totalCandidates.toLocaleString()} candidates
          </span>
        )}
      </div>
    </div>
  );
}
