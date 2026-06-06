"use client";

import React, { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import type { CandidateResult } from "@/services/api";

interface ResultsTableProps {
  results: CandidateResult[];
}

// ---------------------------------------------------------------------------
// PART 3 — ScoreBar: red → amber → yellow → lime → green by score tier
// ---------------------------------------------------------------------------

function getScoreColor(pct: number): string {
  if (pct >= 75) return "#22c55e"; // green  — strong match
  if (pct >= 55) return "#84cc16"; // lime   — good match
  if (pct >= 40) return "#eab308"; // yellow — moderate
  if (pct >= 25) return "#f59e0b"; // amber  — weak
  return "#ef4444";                 // red    — poor match
}

function ScoreBar({ score }: { score: number }) {
  const pct   = Math.round(score * 100);
  const color = getScoreColor(pct);

  return (
    <div style={{ display: "flex", alignItems: "center", gap: "10px", minWidth: "180px", width: "100%" }}>
      <div
        style={{
          flex:         1,
          height:       "5px",
          borderRadius: "999px",
          background:   "rgba(255,255,255,0.08)",
          overflow:     "hidden",
        }}
      >
        <div
          style={{
            width:        `${pct}%`,
            height:       "100%",
            borderRadius: "999px",
            background:   color,
            transition:   "width 0.7s cubic-bezier(0.4, 0, 0.2, 1)",
          }}
        />
      </div>
      <span
        style={{
          fontSize:          "13px",
          fontWeight:        500,
          color,
          minWidth:          "38px",
          textAlign:         "right",
          fontVariantNumeric:"tabular-nums",
        }}
      >
        {pct}%
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// ScoreBreakdown — shown in expanded row panel
// ---------------------------------------------------------------------------

function ScoreBreakdown({
  semanticScore,
  behavioralScore,
}: {
  semanticScore: number;
  behavioralScore: number;
}) {
  return (
    <div style={{ display: "flex", gap: "16px", marginTop: "8px" }}>
      <span style={{ fontSize: "12px", color: "#a78bfa" }}>
        Semantic: {Math.round(semanticScore * 100)}%
      </span>
      <span style={{ fontSize: "12px", color: "#60a5fa" }}>
        Behavioral: {Math.round(behavioralScore * 100)}%
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tier tabs
// ---------------------------------------------------------------------------

const TIERS = [
  { label: "Top 100", count: 100 },
  { label: "Top 50",  count: 50  },
  { label: "Top 10",  count: 10  },
] as const;

// ---------------------------------------------------------------------------
// ResultsTable
// ---------------------------------------------------------------------------

export function ResultsTable({ results }: ResultsTableProps) {
  const [activeTier,  setActiveTier]  = useState(0);
  const [expandedRow, setExpandedRow] = useState<number | null>(null);

  const visibleResults = results.slice(0, TIERS[activeTier].count);
  const toggleRow = (rank: number) =>
    setExpandedRow((prev) => (prev === rank ? null : rank));

  return (
    <div className="w-full">
      {/* Tier tabs */}
      <div className="flex items-center gap-1 mb-4 p-1 bg-white/[0.03] rounded-xl w-fit border border-white/[0.05]">
        {TIERS.map((t, i) => (
          <button
            key={t.label}
            onClick={() => { setActiveTier(i); setExpandedRow(null); }}
            className={`px-4 py-2 rounded-lg text-xs font-medium transition-all duration-300 ${
              i === activeTier
                ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/20"
                : "text-white/40 hover:text-white/70 hover:bg-white/[0.05]"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="rounded-2xl border border-white/10 overflow-hidden">
        {/* Header */}
        <div className="grid grid-cols-[60px_1fr_200px_40px] gap-4 px-5 py-3 bg-white/[0.04] border-b border-white/[0.05] text-xs font-semibold text-white/40 uppercase tracking-wider">
          <span>Rank</span>
          <span>Candidate</span>
          <span>Score</span>
          <span />
        </div>

        {/* Rows */}
        <div className="max-h-[600px] overflow-y-auto">
          {visibleResults.map((c) => {
            const isExpanded = expandedRow === c._rank;

            return (
              <div key={c._rank}>
                <div
                  onClick={() => toggleRow(c._rank)}
                  className={`grid grid-cols-[60px_1fr_200px_40px] gap-4 px-5 py-4 items-center cursor-pointer transition-colors duration-200 ${
                    isExpanded ? "bg-indigo-500/[0.06]" : "hover:bg-white/[0.03]"
                  } ${c._rank > 1 ? "border-t border-white/[0.04]" : ""}`}
                >
                  {/* Rank badge */}
                  <span
                    className={`text-sm font-bold tabular-nums ${
                      c._rank <= 3 ? "text-indigo-400" : c._rank <= 10 ? "text-white/80" : "text-white/40"
                    }`}
                  >
                    #{c._rank}
                  </span>

                  {/* Name + title */}
                  <div className="min-w-0">
                    <p className="text-sm text-white/90 truncate">
                      {c.name || c.candidate_id || `Candidate ${c._rank}`}
                    </p>
                    {c.current_title && (
                      <p className="text-xs text-white/30 truncate mt-0.5">
                        {c.current_title}
                      </p>
                    )}
                  </div>

                  {/* Score bar */}
                  <ScoreBar score={c._score} />

                  {/* Expand toggle */}
                  <div className="flex justify-center text-white/30">
                    {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  </div>
                </div>

                {/* Expanded panel */}
                {isExpanded && (
                  <div className="px-5 pb-5 pt-3 bg-indigo-500/[0.04] border-t border-indigo-500/10">
                    <p className="text-sm text-white/60 leading-relaxed">{c._reasoning}</p>
                    <ScoreBreakdown
                      semanticScore={c._semantic_score}
                      behavioralScore={c._behavioral_score}
                    />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      <p className="text-xs text-white/20 mt-3 text-right">
        Showing {visibleResults.length} of {results.length} candidates
      </p>
    </div>
  );
}
