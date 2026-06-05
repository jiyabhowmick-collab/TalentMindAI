"use client";

import React, { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { BrainCircuit, Eye, EyeOff, Loader2, CheckCircle2, XCircle } from "lucide-react";
import Link from "next/link";
import { BGPattern } from "@/components/ui/bg-pattern";
import { HoverButton } from "@/components/ui/hover-button";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:4000";

export default function ResetPasswordPage() {
  const { token } = useParams<{ token: string }>();
  const router = useRouter();

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState<"idle" | "success" | "error">("idle");
  const [errorMsg, setErrorMsg] = useState("");

  const strength = getStrength(password);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");

    if (password.length < 6) {
      setErrorMsg("Password must be at least 6 characters.");
      return;
    }
    if (password !== confirmPassword) {
      setErrorMsg("Passwords do not match.");
      return;
    }

    setIsLoading(true);
    try {
      const res = await fetch(`${API}/api/auth/resetpassword/${token}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Reset failed.");

      // Save token and auto-login
      if (data.token) localStorage.setItem("token", data.token);
      setStatus("success");

      // Redirect to dashboard after 2s
      setTimeout(() => router.push("/dashboard"), 2000);
    } catch (err: any) {
      setErrorMsg(err.message);
      setStatus("error");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#030303] flex items-center justify-center px-4 relative overflow-hidden">
      <BGPattern
        variant="checkerboard"
        mask="fade-edges"
        fill="rgba(234, 88, 12, 0.04)"
        size={40}
        className="absolute inset-0 z-0 opacity-50"
      />

      {/* Glow */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-indigo-600/10 rounded-full blur-[120px] pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative z-10 w-full max-w-md"
      >
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 justify-center mb-10 group">
          <div className="h-9 w-9 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform">
            <BrainCircuit className="h-7 w-7 text-indigo-500 drop-shadow-[0_0_12px_rgba(99,102,241,0.8)]" />
          </div>
          <span className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-300 to-rose-300">
            Talent-Mind
          </span>
        </Link>

        <div className="rounded-2xl border border-white/[0.07] bg-white/[0.02] backdrop-blur-md p-8 shadow-2xl shadow-black/40">
          <AnimatePresence mode="wait">
            {/* ── Success state ── */}
            {status === "success" && (
              <motion.div
                key="success"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="text-center space-y-4 py-4"
              >
                <div className="flex justify-center">
                  <div className="h-16 w-16 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                    <CheckCircle2 className="h-8 w-8 text-emerald-400" />
                  </div>
                </div>
                <h2 className="text-2xl font-bold text-white">Password Reset!</h2>
                <p className="text-white/50 text-sm">
                  Your password has been updated. Redirecting to your dashboard…
                </p>
                <div className="flex justify-center">
                  <Loader2 className="h-4 w-4 animate-spin text-indigo-500" />
                </div>
              </motion.div>
            )}

            {/* ── Form state ── */}
            {status !== "success" && (
              <motion.div
                key="form"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="space-y-6"
              >
                <div>
                  <h1 className="text-3xl font-bold tracking-tight text-white mb-1">
                    New Password
                  </h1>
                  <p className="text-sm text-white/40">
                    Choose a strong password for your account.
                  </p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-5">
                  {/* Password */}
                  <div className="space-y-2">
                    <label className="text-sm text-white/70">New Password</label>
                    <div className="relative">
                      <input
                        type={showPassword ? "text" : "password"}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="••••••••••••"
                        required
                        disabled={isLoading}
                        className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-4 py-3 pr-11
                          text-sm text-white placeholder:text-white/20
                          focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/20
                          disabled:opacity-50 transition-all"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword((v) => !v)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60 transition-colors"
                      >
                        {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>

                    {/* Strength bar */}
                    {password && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        className="space-y-1"
                      >
                        <div className="flex gap-1">
                          {[1, 2, 3, 4].map((level) => (
                            <div
                              key={level}
                              className={`h-1 flex-1 rounded-full transition-all duration-300 ${
                                strength >= level
                                  ? level <= 1
                                    ? "bg-red-500"
                                    : level <= 2
                                    ? "bg-indigo-400"
                                    : level <= 3
                                    ? "bg-rose-400"
                                    : "bg-emerald-500"
                                  : "bg-white/[0.08]"
                              }`}
                            />
                          ))}
                        </div>
                        <p className="text-xs text-white/30">
                          {["", "Weak", "Fair", "Good", "Strong"][strength]} password
                        </p>
                      </motion.div>
                    )}
                  </div>

                  {/* Confirm Password */}
                  <div className="space-y-2">
                    <label className="text-sm text-white/70">Confirm Password</label>
                    <div className="relative">
                      <input
                        type={showConfirm ? "text" : "password"}
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        placeholder="••••••••••••"
                        required
                        disabled={isLoading}
                        className={`w-full bg-white/[0.04] border rounded-xl px-4 py-3 pr-11
                          text-sm text-white placeholder:text-white/20
                          focus:outline-none focus:ring-1 disabled:opacity-50 transition-all
                          ${
                            confirmPassword && password !== confirmPassword
                              ? "border-red-500/50 focus:border-red-500/50 focus:ring-red-500/20"
                              : confirmPassword && password === confirmPassword
                              ? "border-emerald-500/50 focus:border-emerald-500/50 focus:ring-emerald-500/20"
                              : "border-white/[0.08] focus:border-indigo-500/50 focus:ring-indigo-500/20"
                          }`}
                      />
                      <button
                        type="button"
                        onClick={() => setShowConfirm((v) => !v)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60 transition-colors"
                      >
                        {showConfirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                    {confirmPassword && password !== confirmPassword && (
                      <p className="text-xs text-red-400 flex items-center gap-1">
                        <XCircle className="h-3 w-3" /> Passwords don't match
                      </p>
                    )}
                  </div>

                  {/* Error */}
                  <AnimatePresence>
                    {errorMsg && (
                      <motion.p
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3"
                      >
                        {errorMsg}
                      </motion.p>
                    )}
                  </AnimatePresence>

                  <HoverButton
                    type="submit"
                    disabled={isLoading || password !== confirmPassword || password.length < 6}
                    className="w-full"
                  >
                    {isLoading ? (
                      <span className="flex items-center justify-center gap-2">
                        <Loader2 className="h-4 w-4 animate-spin inline" />
                        Resetting…
                      </span>
                    ) : (
                      "Reset Password"
                    )}
                  </HoverButton>
                </form>

                <p className="text-center text-sm text-white/30">
                  <Link href="/login" className="text-indigo-400 hover:text-indigo-300 transition-colors">
                    Back to Sign in
                  </Link>
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>
    </main>
  );
}

// ── Password strength calculator ───────────────────────────────────────
function getStrength(password: string): number {
  let score = 0;
  if (password.length >= 6) score++;
  if (password.length >= 10) score++;
  if (/[A-Z]/.test(password) && /[a-z]/.test(password)) score++;
  if (/[0-9]/.test(password) && /[^A-Za-z0-9]/.test(password)) score++;
  return score;
}
