"use client";

import React, { useState } from "react";
import { Download, Loader2 } from "lucide-react";

const API_BASE = "http://localhost:4000";

interface ExportButtonsProps {
  jobId: string;
}

const TIERS = [
  { tier: 100, label: "Top 100" },
  { tier: 50, label: "Top 50" },
  { tier: 10, label: "Top 10" },
] as const;

export function ExportButtons({ jobId }: ExportButtonsProps) {
  const [loading, setLoading] = useState<number | null>(null);

  const handleDownload = async (tier: number) => {
    setLoading(tier);
    try {
      const res = await fetch(`${API_BASE}/api/export/${jobId}/${tier}`);
      if (!res.ok) throw new Error("Download failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `talent-mind_top-${tier}_${jobId.slice(0, 8)}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Export error:", err);
      alert("Failed to download CSV. Make sure the server is running.");
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-3">
      {TIERS.map(({ tier, label }) => (
        <button
          key={tier}
          onClick={() => handleDownload(tier)}
          disabled={loading !== null}
          className={`
            group flex items-center gap-2 rounded-xl border px-5 py-2.5 text-sm font-medium
            transition-all duration-300
            ${
              loading === tier
                ? "border-indigo-500/30 bg-indigo-500/10 text-indigo-400 cursor-wait"
                : "border-white/10 bg-white/[0.03] text-white/70 hover:text-white hover:border-indigo-500/40 hover:bg-indigo-500/[0.06] hover:shadow-lg hover:shadow-indigo-500/[0.05]"
            }
            disabled:opacity-40 disabled:cursor-not-allowed
          `}
        >
          {loading === tier ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Download className="h-4 w-4 transition-transform group-hover:-translate-y-0.5" />
          )}
          {label}
        </button>
      ))}
    </div>
  );
}
