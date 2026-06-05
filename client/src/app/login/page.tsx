import { AuthSplitScreen } from "@/components/auth/auth-split-screen";
import { BGPattern } from "@/components/ui/bg-pattern";
import { Navbar } from "@/components/navbar";
import { Suspense } from "react";

export default function LoginPage() {
  return (
    <main className="bg-[#030303] min-h-screen relative overflow-hidden flex flex-col">
      {/* Boxy Design Background */}
      <BGPattern 
        variant="checkerboard" 
        mask="fade-edges" 
        fill="rgba(99, 102, 241, 0.06)" 
        size={40} 
        className="absolute inset-0 z-0 opacity-60" 
      />

      <div className="relative z-10 w-full">
        {/* We can hide navbar on mobile for login screen to save space, but let's keep it consistent */}
        <div className="absolute top-0 left-0 w-full z-50">
            <Navbar />
        </div>

        {/* Adjusting padding top so it doesn't overlap with the navbar */}
        <div className="pt-16">
            <Suspense fallback={<div className="min-h-screen" />}>
                <AuthSplitScreen 
                logo={
                    <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-300 to-rose-300">
                        Talent-Mind
                    </span>
                }
                imageSrc="https://images.unsplash.com/photo-1522071820081-009f0129c71c?ixlib=rb-4.1.0&auto=format&fit=crop&q=80&w=2000"
                imageAlt="Team collaborating"
                />
            </Suspense>
        </div>
      </div>
    </main>
  );
}
