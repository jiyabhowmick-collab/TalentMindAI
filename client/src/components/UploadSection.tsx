"use client";

import React, { useCallback, useState, useRef } from "react";
import { Upload, FileText, AlertTriangle, X, CheckCircle2 } from "lucide-react";

const MAX_SIZE = 500 * 1024 * 1024; // 500 MB

interface UploadSectionProps {
  file: File | null;
  onFileSelect: (file: File | null) => void;
}

export function UploadSection({ file, onFileSelect }: UploadSectionProps) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    (f: File) => {
      const ext = f.name.toLowerCase();
      if (!ext.endsWith(".jsonl") && !ext.endsWith(".gz")) {
        alert("Only .jsonl or .jsonl.gz files are accepted.");
        return;
      }
      onFileSelect(f);
    },
    [onFileSelect]
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const f = e.dataTransfer.files[0];
      if (f) handleFile(f);
    },
    [handleFile]
  );

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = () => setIsDragging(false);

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
  };

  const overLimit = file ? file.size > MAX_SIZE : false;

  return (
    <div className="w-full">
      <label className="block text-sm font-medium text-white/70 mb-3">
        Candidate File
      </label>

      {!file ? (
        <div
          onDrop={onDrop}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onClick={() => inputRef.current?.click()}
          className={`
            relative cursor-pointer rounded-2xl border-2 border-dashed p-12
            flex flex-col items-center justify-center gap-4 transition-all duration-300
            ${
              isDragging
                ? "border-indigo-500 bg-indigo-500/10 scale-[1.01]"
                : "border-white/10 bg-white/[0.02] hover:border-indigo-500/40 hover:bg-white/[0.04]"
            }
          `}
        >
          <div
            className={`rounded-full p-4 transition-colors duration-300 ${
              isDragging ? "bg-indigo-500/20" : "bg-white/[0.05]"
            }`}
          >
            <Upload
              className={`h-8 w-8 transition-colors duration-300 ${
                isDragging ? "text-indigo-400" : "text-white/40"
              }`}
            />
          </div>
          <div className="text-center">
            <p className="text-white/80 text-sm font-medium">
              Drag &amp; drop your candidate file here
            </p>
            <p className="text-white/30 text-xs mt-1">
              Supports .jsonl and .jsonl.gz — Max 500 MB
            </p>
          </div>
          <input
            ref={inputRef}
            type="file"
            accept=".jsonl,.gz"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) handleFile(f);
              e.target.value = "";
            }}
          />
        </div>
      ) : (
        <div
          className={`rounded-2xl border p-5 flex items-center justify-between transition-all duration-300 ${
            overLimit
              ? "border-red-500/40 bg-red-500/[0.05]"
              : "border-indigo-500/30 bg-indigo-500/[0.04]"
          }`}
        >
          <div className="flex items-center gap-4">
            <div
              className={`rounded-xl p-3 ${
                overLimit ? "bg-red-500/20" : "bg-indigo-500/20"
              }`}
            >
              <FileText
                className={`h-6 w-6 ${
                  overLimit ? "text-red-400" : "text-indigo-400"
                }`}
              />
            </div>
            <div>
              <p className="text-white text-sm font-medium flex items-center gap-2">
                {file.name}
                {!overLimit && (
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                )}
              </p>
              <p className="text-white/40 text-xs mt-0.5">
                {formatSize(file.size)}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {overLimit && (
              <div className="flex items-center gap-1.5 text-red-400 text-xs">
                <AlertTriangle className="h-4 w-4" />
                <span>Exceeds 500 MB limit</span>
              </div>
            )}
            <button
              onClick={() => onFileSelect(null)}
              className="rounded-lg p-2 hover:bg-white/10 text-white/40 hover:text-white transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
