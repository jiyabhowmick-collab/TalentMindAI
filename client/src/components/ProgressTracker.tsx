"use client";

import React from "react";
import { Upload, Cpu, ListOrdered, CheckCircle2 } from "lucide-react";

export type Stage = "idle" | "uploading" | "processing" | "ranking" | "done" | "error";

interface ProgressTrackerProps {
  stage: Stage;
  candidateCount?: number;
  errorMessage?: string;
}

const STAGES = [
  { key: "uploading", label: "Uploading", icon: Upload },
  { key: "processing", label: "Processing", icon: Cpu },
  { key: "ranking", label: "Ranking", icon: ListOrdered },
  { key: "done", label: "Done", icon: CheckCircle2 },
] as const;

function stageIndex(stage: Stage): number {
  if (stage === "idle") return -1;
  if (stage === "error") return -1;
  return STAGES.findIndex((s) => s.key === stage);
}

export function ProgressTracker({ stage, candidateCount, errorMessage }: ProgressTrackerProps) {
  if (stage === "idle") return null;

  const currentIdx = stageIndex(stage);

  return (
    <div className="w-full rounded-2xl border border-white/10 bg-white/[0.02] p-6">
      {/* Stage indicators */}
      <div className="flex items-center justify-between mb-6">
        {STAGES.map((s, i) => {
          const Icon = s.icon;
          const isActive = stage !== "error" && i === currentIdx;
          const isComplete = stage !== "error" && i < currentIdx;
          const isFuture = stage === "error" || i > currentIdx;

          return (
            <React.Fragment key={s.key}>
              <div className="flex flex-col items-center gap-2">
                <div
                  className={`rounded-full p-3 transition-all duration-500 ${
                    isComplete
                      ? "bg-emerald-500/20 text-emerald-400"
                      : isActive
                      ? "bg-indigo-500/20 text-indigo-400 animate-pulse"
                      : "bg-white/[0.05] text-white/20"
                  }`}
                >
                  <Icon className="h-5 w-5" />
                </div>
                <span
                  className={`text-xs font-medium transition-colors duration-300 ${
                    isComplete
                      ? "text-emerald-400"
                      : isActive
                      ? "text-indigo-400"
                      : "text-white/25"
                  }`}
                >
                  {s.label}
                </span>
              </div>
              {i < STAGES.length - 1 && (
                <div className="flex-1 mx-3 h-[2px] rounded-full overflow-hidden bg-white/[0.05]">
                  <div
                    className={`h-full rounded-full transition-all duration-700 ease-out ${
                      isComplete
                        ? "w-full bg-emerald-500/60"
                        : isActive
                        ? "w-1/2 bg-indigo-500/60 animate-pulse"
                        : "w-0"
                    }`}
                  />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* Progress bar */}
      <div className="w-full h-2 rounded-full bg-white/[0.05] overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-1000 ease-out ${
            stage === "error"
              ? "bg-red-500 w-full"
              : stage === "done"
              ? "bg-gradient-to-r from-emerald-500 to-emerald-400 w-full"
              : "bg-gradient-to-r from-indigo-600 to-indigo-400"
          }`}
          style={{
            width:
              stage === "error" || stage === "done"
                ? "100%"
                : `${((currentIdx + 0.5) / STAGES.length) * 100}%`,
          }}
        />
      </div>

      {/* Status text */}
      <div className="mt-4 flex items-center justify-between">
        <p className="text-sm text-white/50">
          {stage === "error" && (
            <span className="text-red-400">{errorMessage || "An error occurred."}</span>
          )}
          {stage === "uploading" && "Uploading candidate file to server…"}
          {stage === "processing" && "Parsing candidates and preparing data…"}
          {stage === "ranking" && "Running AI ranking against job description…"}
          {stage === "done" && (
            <span className="text-emerald-400">Ranking complete!</span>
          )}
        </p>
        {candidateCount !== undefined && candidateCount > 0 && (
          <p className="text-xs text-white/30 tabular-nums">
            {candidateCount.toLocaleString()} candidates
          </p>
        )}
      </div>
    </div>
  );
}
