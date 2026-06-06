"use client";

import React, { useEffect, useRef, useState } from "react";
import type { RankStep } from "@/services/api";

// ---------------------------------------------------------------------------
// PART 4 — Skeleton shimmer CSS
// ---------------------------------------------------------------------------

const SKEL_CSS = `
@keyframes shimmer {
  0%   { background-position: -500px 0; }
  100% { background-position:  500px 0; }
}
.skel {
  background: linear-gradient(
    90deg,
    rgba(255,255,255,0.04) 25%,
    rgba(255,255,255,0.09) 50%,
    rgba(255,255,255,0.04) 75%
  );
  background-size: 500px 100%;
  animation: shimmer 1.8s infinite linear;
  border-radius: 4px;
}
`;

// ---------------------------------------------------------------------------
// Single skeleton row — matches ResultsTable row layout
// ---------------------------------------------------------------------------

function SkeletonRow({ delay }: { delay: number }) {
  const d = `${delay}s`;
  return (
    <div
      style={{
        display:       "flex",
        alignItems:    "center",
        gap:           "16px",
        padding:       "14px 20px",
        borderBottom:  "1px solid rgba(255,255,255,0.05)",
        minHeight:     "52px",
      }}
    >
      {/* Rank */}
      <div className="skel" style={{ width: "28px", height: "14px", animationDelay: d, flexShrink: 0 }} />

      {/* Avatar */}
      <div className="skel" style={{ width: "36px", height: "36px", borderRadius: "50%", animationDelay: d, flexShrink: 0 }} />

      {/* Name + title */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "6px" }}>
        <div className="skel" style={{ width: "160px", height: "13px", animationDelay: d }} />
        <div className="skel" style={{ width: "100px", height: "11px", animationDelay: d }} />
      </div>

      {/* Score bar + pct */}
      <div style={{ display: "flex", alignItems: "center", gap: "8px", width: "190px", flexShrink: 0 }}>
        <div className="skel" style={{ flex: 1, height: "5px", borderRadius: "999px", animationDelay: d }} />
        <div className="skel" style={{ width: "34px", height: "13px", animationDelay: d }} />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Animated counter: counts up toward totalCandidates while step === 2
// ---------------------------------------------------------------------------

function useCountUp(total: number, active: boolean): number {
  const [count, setCount]  = useState(0);
  const timerRef           = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!active || total <= 0) {
      setCount(0);
      return;
    }
    const increment = Math.max(1, Math.floor(total / 60));
    timerRef.current = setInterval(() => {
      setCount((prev) => {
        const next = prev + increment;
        if (next >= total) {
          if (timerRef.current) clearInterval(timerRef.current);
          return total;
        }
        return next;
      });
    }, 1000);

    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [total, active]);

  return count;
}

// ---------------------------------------------------------------------------
// SkeletonResults
// ---------------------------------------------------------------------------

interface SkeletonResultsProps {
  totalCandidates: number;
  isDone: boolean;
}

export function SkeletonResults({ totalCandidates, isDone }: SkeletonResultsProps) {
  const count        = useCountUp(totalCandidates, !isDone && totalCandidates > 0);
  const displayCount = isDone ? totalCandidates : count;

  return (
    <>
      <style>{SKEL_CSS}</style>
      <div
        style={{
          width:        "100%",
          borderRadius: "16px",
          border:       "1px solid rgba(255,255,255,0.10)",
          overflow:     "hidden",
        }}
      >
        {/* Table header */}
        <div
          style={{
            display:      "flex",
            alignItems:   "center",
            gap:          "16px",
            padding:      "12px 20px",
            background:   "rgba(255,255,255,0.03)",
            borderBottom: "1px solid rgba(255,255,255,0.06)",
          }}
        >
          <span style={{ fontSize: "11px", fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", color: "rgba(255,255,255,0.3)", width: "28px" }}>
            Rank
          </span>
          {/* avatar spacer */}
          <div style={{ width: "36px" }} />
          <span style={{ flex: 1, fontSize: "11px", fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", color: "rgba(255,255,255,0.3)" }}>
            Candidate
          </span>
          <span style={{ width: "190px", fontSize: "11px", fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", color: "rgba(255,255,255,0.3)" }}>
            Score
          </span>
        </div>

        {/* 8 staggered skeleton rows */}
        {Array.from({ length: 8 }, (_, i) => (
          <SkeletonRow key={i} delay={i * 0.12} />
        ))}

        {/* Animated counter footer */}
        {totalCandidates > 0 && (
          <div
            style={{
              padding:           "11px 20px",
              borderTop:         "1px solid rgba(255,255,255,0.05)",
              background:        "rgba(255,255,255,0.01)",
              fontSize:          "13px",
              color:             "#eab308",  // yellow — matches Ranking step
              fontVariantNumeric:"tabular-nums",
            }}
          >
            {isDone
              ? `Ranked ${displayCount.toLocaleString()} candidates`
              : `Ranking ${displayCount.toLocaleString()} candidates...`}
          </div>
        )}
      </div>
    </>
  );
}
