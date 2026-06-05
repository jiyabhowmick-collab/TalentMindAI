"use client";

import React from "react";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { BGPattern } from "@/components/ui/bg-pattern";
import { ProfileSettings } from "@/components/ProfileSettings";

export default function ProfilePage() {
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
        <div className="max-w-3xl mx-auto space-y-8">
          {/* Header */}
          <div className="text-center mb-6">
            <h1 className="text-4xl md:text-5xl font-bold text-white tracking-tight">
              Your{" "}
              <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-rose-300">
                Profile
              </span>
            </h1>
            <p className="text-white/40 text-sm mt-3 max-w-lg mx-auto">
              Manage your account details and personal information.
            </p>
          </div>

          <ProfileSettings />
        </div>
      </div>

      <Footer />
    </main>
  );
}
