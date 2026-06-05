"use client";

import React, { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

interface CandidateResult {
  _rank: number;
  _score: number;
  _semantic_score: number;
  _behavioral_score: number;
  _reasoning: string;
  name?: string;
  title?: string;
  [key: string]: unknown;
}

interface ResultsTableProps {
  results: CandidateResult[];
}

const TIERS = [
  { label: "Top 100", count: 100 },
  { label: "Top 50", count: 50 },
  { label: "Top 10", count: 10 },
] as const;

export function ResultsTable({ results }: ResultsTableProps) {
  const [activeTier, setActiveTier] = useState(0);
  const [expandedRow, setExpandedRow] = useState<number | null>(null);

  const tier = TIERS[activeTier];
  const visibleResults = results.slice(0, tier.count);

  const toggleRow = (rank: number) => {
    setExpandedRow((prev) => (prev === rank ? null : rank));
  };

  return (
    <div className="w-full">
      {/* Tier tabs */}
      <div className="flex items-center gap-1 mb-4 p-1 bg-white/[0.03] rounded-xl w-fit border border-white/[0.05]">
        {TIERS.map((t, i) => (
          <button
            key={t.label}
            onClick={() => {
              setActiveTier(i);
              setExpandedRow(null);
            }}
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
        <div className="grid grid-cols-[60px_1fr_160px_40px] gap-4 px-5 py-3 bg-white/[0.04] border-b border-white/[0.05] text-xs font-semibold text-white/40 uppercase tracking-wider">
          <span>Rank</span>
          <span>Candidate</span>
          <span>Score</span>
          <span />
        </div>

        {/* Rows */}
        <div className="max-h-[600px] overflow-y-auto">
          {visibleResults.map((c) => {
            const isExpanded = expandedRow === c._rank;
            const scorePct = Math.round(c._score * 100);

            return (
              <div key={c._rank}>
                <div
                  onClick={() => toggleRow(c._rank)}
                  className={`grid grid-cols-[60px_1fr_160px_40px] gap-4 px-5 py-4 items-center cursor-pointer transition-colors duration-200 ${
                    isExpanded
                      ? "bg-indigo-500/[0.06]"
                      : "hover:bg-white/[0.03]"
                  } ${c._rank > 1 ? "border-t border-white/[0.04]" : ""}`}
                >
                  {/* Rank */}
                  <span
                    className={`text-sm font-bold tabular-nums ${
                      c._rank <= 3
                        ? "text-indigo-400"
                        : c._rank <= 10
                        ? "text-white/80"
                        : "text-white/40"
                    }`}
                  >
                    #{c._rank}
                  </span>

                  {/* Name */}
                  <span className="text-sm text-white/90 truncate">
                    {c.name || c.title || `Candidate ${c._rank}`}
                  </span>

                  {/* Score bar */}
                  <div className="flex items-center gap-3">
                    <div className="flex-1 h-2 rounded-full bg-white/[0.06] overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${
                          scorePct >= 80
                            ? "bg-emerald-500"
                            : scorePct >= 60
                            ? "bg-indigo-500"
                            : scorePct >= 40
                            ? "bg-rose-500"
                            : "bg-red-500"
                        }`}
                        style={{ width: `${scorePct}%` }}
                      />
                    </div>
                    <span className="text-xs text-white/50 tabular-nums w-10 text-right">
                      {scorePct}%
                    </span>
                  </div>

                  {/* Expand */}
                  <div className="flex justify-center text-white/30">
                    {isExpanded ? (
                      <ChevronUp className="h-4 w-4" />
                    ) : (
                      <ChevronDown className="h-4 w-4" />
                    )}
                  </div>
                </div>

                {/* Expanded reasoning */}
                {isExpanded && (
                  <div className="px-5 pb-5 pt-1 bg-indigo-500/[0.04] border-t border-indigo-500/10">
                    <p className="text-sm text-white/60 leading-relaxed">
                      {c._reasoning}
                    </p>
                    <div className="mt-3 flex gap-6 text-xs text-white/30">
                      <span>
                        Semantic:{" "}
                        <span className="text-white/60">
                          {Math.round(c._semantic_score * 100)}%
                        </span>
                      </span>
                      <span>
                        Behavioral:{" "}
                        <span className="text-white/60">
                          {Math.round(c._behavioral_score * 100)}%
                        </span>
                      </span>
                    </div>
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
