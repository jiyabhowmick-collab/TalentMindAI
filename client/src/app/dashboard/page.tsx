"use client";

import React, { useState, useCallback } from "react";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { BGPattern } from "@/components/ui/bg-pattern";
import { UploadSection } from "@/components/UploadSection";
import { JobDescriptionInput } from "@/components/JobDescriptionInput";
import { ProgressTracker, Stage } from "@/components/ProgressTracker";
import { ResultsTable } from "@/components/ResultsTable";
import { ExportButtons } from "@/components/ExportButtons";
import { Loader2, Rocket } from "lucide-react";
import { HoverButton } from "@/components/ui/hover-button";
import {
  uploadCandidates,
  pollResults,
  type CandidateResult,
  type ProgressStatus,
} from "@/services/api";

export default function DashboardPage() {
  const [file, setFile] = useState<File | null>(null);
  const [jd, setJd] = useState("");
  const [stage, setStage] = useState<Stage>("idle");
  const [jobId, setJobId] = useState<string | null>(null);
  const [results, setResults] = useState<CandidateResult[]>([]);
  const [candidateCount, setCandidateCount] = useState(0);
  const [errorMessage, setErrorMessage] = useState("");

  const canSubmit =
    file !== null &&
    jd.trim().length > 10 &&
    stage !== "uploading" &&
    stage !== "processing" &&
    stage !== "ranking";

  const handleSubmit = useCallback(async () => {
    if (!file || !jd.trim()) return;

    setStage("uploading");
    setJobId(null);
    setResults([]);
    setErrorMessage("");

    try {
      // 1. Upload file + JD
      const uploadRes = await uploadCandidates(file, jd.trim());

      setJobId(uploadRes.job_id);
      setCandidateCount(uploadRes.total_candidates || 0);

      // 2. Poll for results
      const onProgress = (status: ProgressStatus) => {
        setStage(status as Stage);
      };

      const data = await pollResults(uploadRes.job_id, onProgress);
      setResults(data.results || []);
      setCandidateCount(data.total_candidates || 0);
      setStage("done");
    } catch (err: any) {
      setStage("error");
      setErrorMessage(err.message || "Something went wrong.");
    }
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

          {/* Upload + JD */}
          <div className="space-y-6 rounded-2xl border border-white/[0.06] bg-white/[0.01] p-6 md:p-8">
            <UploadSection file={file} onFileSelect={setFile} />
            <div className="border-t border-white/[0.05]" />
            <JobDescriptionInput value={jd} onChange={setJd} />

            {/* Submit */}
            <div className="pt-2">
              <HoverButton
                onClick={handleSubmit}
                disabled={!canSubmit}
                className="w-full flex items-center justify-center gap-2"
              >
                {stage === "uploading" ||
                stage === "processing" ||
                stage === "ranking" ? (
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

          {/* Progress */}
          {stage !== "idle" && (
            <ProgressTracker
              stage={stage}
              candidateCount={candidateCount}
              errorMessage={errorMessage}
            />
          )}

          {/* Results */}
          {results.length > 0 && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold text-white">
                  Ranked Results
                </h2>
                {jobId && <ExportButtons jobId={jobId} />}
              </div>
              <ResultsTable results={results} />
            </div>
          )}
        </div>
      </div>

      <Footer />
    </main>
  );
}
