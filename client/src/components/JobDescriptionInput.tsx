"use client";

import React, { useRef, useState, useCallback } from "react";
import { FileText, Upload, X } from "lucide-react";

interface JobDescriptionInputProps {
  value: string;
  onChange: (value: string) => void;
}

export function JobDescriptionInput({ value, onChange }: JobDescriptionInputProps) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [jdFileName, setJdFileName] = useState<string | null>(null);

  const handleJdFile = useCallback(
    async (file: File) => {
      const text = await file.text();
      onChange(text);
      setJdFileName(file.name);
    },
    [onChange]
  );

  const clearFile = () => {
    setJdFileName(null);
    onChange("");
  };

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-3">
        <label className="block text-sm font-medium text-white/70">
          Job Description
        </label>
        <span className="text-xs text-white/30 tabular-nums">
          {value.length.toLocaleString()} characters
        </span>
      </div>

      {jdFileName ? (
        <div className="rounded-2xl border border-indigo-500/30 bg-indigo-500/[0.04] p-4 flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="rounded-lg p-2 bg-indigo-500/20">
              <FileText className="h-5 w-5 text-indigo-400" />
            </div>
            <div>
              <p className="text-white text-sm font-medium">{jdFileName}</p>
              <p className="text-white/40 text-xs">JD loaded from file</p>
            </div>
          </div>
          <button
            onClick={clearFile}
            className="rounded-lg p-2 hover:bg-white/10 text-white/40 hover:text-white transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      ) : null}

      <textarea
        value={value}
        onChange={(e) => {
          onChange(e.target.value);
          if (jdFileName) setJdFileName(null);
        }}
        placeholder="Paste your job description here, or upload a file below..."
        rows={8}
        className="w-full rounded-xl border border-white/10 bg-white/[0.02] px-4 py-3 text-sm text-white placeholder:text-white/25 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all duration-300 resize-y caret-indigo-500 selection:bg-indigo-500/30 hover:bg-white/[0.04]"
      />

      <div className="mt-3 flex items-center gap-3">
        <button
          type="button"
          onClick={() => fileRef.current?.click()}
          className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2 text-xs text-white/60 hover:text-white hover:border-indigo-500/40 hover:bg-white/[0.06] transition-all duration-300"
        >
          <Upload className="h-3.5 w-3.5" />
          Upload .txt or .md
        </button>
        <span className="text-white/20 text-xs">instead of pasting</span>
        <input
          ref={fileRef}
          type="file"
          accept=".txt,.md"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) handleJdFile(f);
            e.target.value = "";
          }}
        />
      </div>
    </div>
  );
}
