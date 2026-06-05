"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  User,
  AtSign,
  Building2,
  Link2,
  Globe,
  FileText,
  Pencil,
  X,
  Save,
  Loader2,
  Check,
  LogOut,
} from "lucide-react";
import { HoverButton } from "@/components/ui/hover-button";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:4000";

interface ProfileData {
  name: string;
  email: string;
  handle: string;
  institution: string;
  githubUrl: string;
  portfolio: string;
  bio: string;
}

const FIELDS: {
  key: keyof Omit<ProfileData, "email">;
  label: string;
  icon: React.ElementType;
  placeholder: string;
  type?: string;
}[] = [
  { key: "name", label: "Full Name", icon: User, placeholder: "John Doe" },
  { key: "handle", label: "Handle", icon: AtSign, placeholder: "johndoe" },
  { key: "institution", label: "Institution", icon: Building2, placeholder: "MIT, Stanford, etc." },
  { key: "githubUrl", label: "GitHub URL", icon: Link2, placeholder: "https://github.com/johndoe", type: "url" },
  { key: "portfolio", label: "Portfolio", icon: Globe, placeholder: "https://johndoe.dev", type: "url" },
];

export function ProfileSettings() {
  const [profile, setProfile] = useState<ProfileData>({
    name: "",
    email: "",
    handle: "",
    institution: "",
    githubUrl: "",
    portfolio: "",
    bio: "",
  });
  const [editData, setEditData] = useState<ProfileData>(profile);
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<"idle" | "success" | "error">("idle");
  const [errorMsg, setErrorMsg] = useState("");

  // Fetch profile on mount
  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/api/profile`, {
        headers: { Authorization: `Bearer ${token}` },
        credentials: "include",
      });
      if (!res.ok) throw new Error("Failed to fetch profile");
      const data = await res.json();
      if (data.success) {
        setProfile(data.user);
        setEditData(data.user);
      }
    } catch {
      setErrorMsg("Could not load profile.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    setSaveStatus("idle");
    setErrorMsg("");

    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`${API}/api/profile`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        credentials: "include",
        body: JSON.stringify(editData),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Update failed");

      setProfile(data.user);
      setEditData(data.user);
      setSaveStatus("success");
      setTimeout(() => {
        setIsEditing(false);
        setSaveStatus("idle");
      }, 1200);
    } catch (err: any) {
      setSaveStatus("error");
      setErrorMsg(err.message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    setEditData(profile);
    setIsEditing(false);
    setErrorMsg("");
    setSaveStatus("idle");
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    window.location.href = "/login";
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
      </div>
    );
  }

  // Generate avatar initials
  const initials = profile.name
    ? profile.name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2)
    : "??";

  return (
    <div className="space-y-8">
      {/* Profile Header Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative rounded-2xl border border-white/[0.06] bg-white/[0.02] overflow-hidden"
      >
        {/* Banner gradient */}
        <div className="h-32 bg-gradient-to-r from-indigo-600/30 via-rose-500/20 to-violet-700/30" />

        <div className="px-6 md:px-8 pb-6 -mt-12">
          <div className="flex flex-col sm:flex-row items-start sm:items-end gap-4">
            {/* Avatar */}
            <div className="h-24 w-24 rounded-2xl bg-gradient-to-br from-indigo-500 to-rose-400 flex items-center justify-center text-2xl font-bold text-white shadow-xl shadow-indigo-600/20 ring-4 ring-[#030303]">
              {initials}
            </div>

            <div className="flex-1 min-w-0 pb-1">
              <h2 className="text-2xl font-bold text-white truncate">
                {profile.name || "Unnamed User"}
              </h2>
              <p className="text-white/40 text-sm">
                {profile.handle ? `@${profile.handle}` : profile.email}
              </p>
            </div>

            {/* Action buttons */}
            <div className="flex gap-2 sm:pb-1">
              {!isEditing ? (
                <HoverButton
                  onClick={() => setIsEditing(true)}
                  className="flex items-center gap-2 px-4 py-2 text-sm"
                >
                  <Pencil className="h-3.5 w-3.5" />
                  Edit Profile
                </HoverButton>
              ) : (
                <>
                  <button
                    onClick={handleCancel}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium
                      bg-white/[0.06] hover:bg-white/[0.1] text-white/70 hover:text-white
                      transition-all duration-300"
                  >
                    <X className="h-3.5 w-3.5" />
                    Cancel
                  </button>
                  <HoverButton onClick={handleSave} disabled={isSaving}>
                    {isSaving ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin inline" />
                        Saving...
                      </>
                    ) : (
                      <>
                        <Save className="mr-2 h-4 w-4 inline" />
                        {saveStatus === "success" ? "Saved!" : "Save Changes"}
                      </>
                    )}
                  </HoverButton>
                </>
              )}

              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium
                  bg-white/[0.04] hover:bg-red-500/20 text-white/40 hover:text-red-400
                  border border-white/[0.06] hover:border-red-500/30
                  transition-all duration-300"
              >
                <LogOut className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Error */}
      <AnimatePresence>
        {errorMsg && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3"
          >
            {errorMsg}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Profile Fields */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="rounded-2xl border border-white/[0.06] bg-white/[0.02] divide-y divide-white/[0.05]"
      >
        {/* Email (always read-only) */}
        <div className="flex items-center gap-4 px-6 md:px-8 py-5">
          <div className="h-10 w-10 rounded-xl bg-white/[0.04] flex items-center justify-center flex-shrink-0">
            <AtSign className="h-4 w-4 text-white/30" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs text-white/30 mb-1">Email Address</p>
            <p className="text-sm text-white/60 truncate">{profile.email}</p>
          </div>
          <span className="text-[10px] uppercase tracking-widest text-white/20 bg-white/[0.04] px-2 py-1 rounded-md">
            Locked
          </span>
        </div>

        {/* Editable fields */}
        {FIELDS.map((field, index) => (
          <motion.div
            key={field.key}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.05 * index }}
            className="flex items-center gap-4 px-6 md:px-8 py-5"
          >
            <div className="h-10 w-10 rounded-xl bg-white/[0.04] flex items-center justify-center flex-shrink-0">
              <field.icon className="h-4 w-4 text-white/30" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs text-white/30 mb-1">{field.label}</p>
              {isEditing ? (
                <input
                  type={field.type || "text"}
                  value={editData[field.key] || ""}
                  onChange={(e) =>
                    setEditData((prev) => ({ ...prev, [field.key]: e.target.value }))
                  }
                  placeholder={field.placeholder}
                  className="w-full bg-white/[0.04] border border-white/[0.08] rounded-lg px-3 py-2
                    text-sm text-white placeholder:text-white/20
                    focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/20
                    transition-all duration-300"
                />
              ) : (
                <p className="text-sm text-white/70 truncate">
                  {profile[field.key] || (
                    <span className="text-white/20 italic">Not set</span>
                  )}
                </p>
              )}
            </div>
          </motion.div>
        ))}

        {/* Bio */}
        <motion.div
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
          className="px-6 md:px-8 py-5"
        >
          <div className="flex items-start gap-4">
            <div className="h-10 w-10 rounded-xl bg-white/[0.04] flex items-center justify-center flex-shrink-0 mt-0.5">
              <FileText className="h-4 w-4 text-white/30" />
            </div>
            <div className="flex-1">
              <div className="flex items-center justify-between mb-1">
                <p className="text-xs text-white/30">Bio</p>
                {isEditing && (
                  <span className="text-[10px] text-white/20">
                    {(editData.bio || "").length}/500
                  </span>
                )}
              </div>
              {isEditing ? (
                <textarea
                  value={editData.bio || ""}
                  onChange={(e) =>
                    setEditData((prev) => ({ ...prev, bio: e.target.value.slice(0, 500) }))
                  }
                  placeholder="Tell us about yourself..."
                  rows={4}
                  className="w-full bg-white/[0.04] border border-white/[0.08] rounded-lg px-3 py-2
                    text-sm text-white placeholder:text-white/20 resize-none
                    focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/20
                    transition-all duration-300"
                />
              ) : (
                <p className="text-sm text-white/70 whitespace-pre-wrap">
                  {profile.bio || (
                    <span className="text-white/20 italic">No bio yet</span>
                  )}
                </p>
              )}
            </div>
          </div>
        </motion.div>
      </motion.div>

      {/* Account info footer */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
        className="text-center text-xs text-white/15 pb-4"
      >
        Account created {profile.email ? `as ${profile.email}` : ""}
      </motion.div>
    </div>
  );
}
