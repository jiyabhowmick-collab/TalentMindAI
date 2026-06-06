"use client";

import React, { useState, useCallback } from "react";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { BGPattern } from "@/components/ui/bg-pattern";
import { UploadSection } from "@/components/UploadSection";
import { JobDescriptionInput } from "@/components/JobDescriptionInput";
import { ProgressTracker } from "@/components/ProgressTracker";
import { ResultsTable } from "@/components/ResultsTable";
import { ExportButtons } from "@/components/ExportButtons";
import { SkeletonResults } from "@/components/SkeletonResults";
import { Loader2, Rocket } from "lucide-react";
import { HoverButton } from "@/components/ui/hover-button";
import {
  uploadAndRank,
  type CandidateResult,
  type RankStep,
} from "@/services/api";

export default function DashboardPage() {
  const [file,            setFile]           = useState<File | null>(null);
  const [jd,              setJd]             = useState("");
  const [step,            setStep]           = useState<RankStep | -1>(-1);
  const [jobId,           setJobId]          = useState<string | null>(null);
  const [results,         setResults]        = useState<CandidateResult[]>([]);
  const [totalCandidates, setTotalCandidates]= useState(0);
  const [errorMessage,    setErrorMessage]   = useState("");

  const isRunning = step === 0 || step === 1 || step === 2;
  const isDone    = step === 3;
  const isIdle    = step === -1;

  const canSubmit =
    file !== null && jd.trim().length > 10 && !isRunning;

  const handleSubmit = useCallback(async () => {
    if (!file || !jd.trim()) return;

    // Reset state
    setStep(-1);
    setJobId(null);
    setResults([]);
    setErrorMessage("");
    setTotalCandidates(0);

    // Small tick so React flushes the reset before starting
    await new Promise<void>((r) => setTimeout(r, 0));

    await uploadAndRank(file, jd.trim(), {
      onStepChange:      (s) => setStep(s),
      onTotalCandidates: (n) => setTotalCandidates(n),
      onComplete:        (res, total, id) => {
        setResults(res);
        setTotalCandidates(total);
        setJobId(id);
      },
      onError: (msg) => {
        setErrorMessage(msg);
        setStep(-1);          // back to idle so error message shows
      },
    });
  }, [file, jd]);

  return (
    <main className="bg-[#030303] min-h-screen flex flex-col relative overflow-hidden">
      <BGPattern
        variant="checkerboard"
        mask="fade-edges"
        fill="rgba(99, 102, 241, 0.04)"
        size={40}
        className="absolute inset-0 z-0 opacity-50"
      />
      <Navbar />

      <div className="relative z-10 flex-grow pt-24 pb-16 px-4 md:px-6">
        <div className="max-w-4xl mx-auto space-y-8">

          {/* Header */}
          <div className="text-center mb-10">
            <h1 className="text-4xl md:text-5xl font-bold text-white tracking-tight">
              Candidate{" "}
              <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-rose-300">
                Ranking
              </span>
            </h1>
            <p className="text-white/40 text-sm mt-3 max-w-lg mx-auto">
              Upload your candidate file and job description — our AI will
              semantically rank every candidate and return the best matches.
            </p>
          </div>

          {/* Upload + JD card */}
          <div className="space-y-6 rounded-2xl border border-white/[0.06] bg-white/[0.01] p-6 md:p-8">
            <UploadSection file={file} onFileSelect={setFile} />
            <div className="border-t border-white/[0.05]" />
            <JobDescriptionInput value={jd} onChange={setJd} />

            <div className="pt-2">
              <HoverButton
                onClick={handleSubmit}
                disabled={!canSubmit}
                className="w-full flex items-center justify-center gap-2"
              >
                {isRunning ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin inline" />
                    Processing…
                  </>
                ) : (
                  <>
                    <Rocket className="h-4 w-4 inline" />
                    Start Ranking
                  </>
                )}
              </HoverButton>
            </div>
          </div>

          {/* Error banner */}
          {errorMessage && isIdle && (
            <div className="rounded-2xl border border-red-500/30 bg-red-500/10 px-5 py-4">
              <p className="text-sm text-red-400">{errorMessage}</p>
            </div>
          )}

          {/* Progress stepper */}
          {step !== -1 && (
            <ProgressTracker
              step={step as RankStep}
              totalCandidates={totalCandidates}
            />
          )}

          {/* Skeleton / results area */}
          {step !== -1 && (
            <div style={{ position: "relative" }}>

              {/* Skeleton — visible while step < 3, fades out when done */}
              {!isDone && (
                <SkeletonResults
                  totalCandidates={totalCandidates}
                  isDone={false}
                />
              )}

              {/* Real results — fade in when done */}
              {isDone && results.length > 0 && (
                <div
                  style={{
                    animation: "fadeIn 0.5s ease forwards",
                  }}
                >
                  <style>{`@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }`}</style>
                  <div className="space-y-6">
                    <div className="flex items-center justify-between">
                      <h2 className="text-xl font-bold text-white">Ranked Results</h2>
                      {jobId && <ExportButtons jobId={jobId} />}
                    </div>
                    <ResultsTable results={results} />
                  </div>
                </div>
              )}
            </div>
          )}

        </div>
      </div>

      <Footer />
    </main>
  );
}
