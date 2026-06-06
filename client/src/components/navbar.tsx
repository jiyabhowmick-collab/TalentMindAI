"use client";

import { Button } from "@/components/ui/button";
import { BrainCircuit, LogOut, User } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export function Navbar() {
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const router = useRouter();

    useEffect(() => {
        // Simple check for token
        const token = localStorage.getItem("token");
        setIsLoggedIn(!!token);
    }, []);

    const handleLogout = () => {
        localStorage.removeItem("token");
        setIsLoggedIn(false);
        router.push("/login");
    };

    return (
        <header className="fixed top-0 left-0 right-0 z-50 bg-[#030303]/80 backdrop-blur-md border-b border-white/[0.05]">
            <div className="max-w-6xl mx-auto px-4 md:px-6 h-16 flex items-center justify-between">
                <Link href="/" className="flex items-center gap-2 group">
                    <div className="h-8 w-8 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
                        <BrainCircuit className="h-6 w-6 text-indigo-500 drop-shadow-[0_0_10px_rgba(99,102,241,0.8)]" />
                    </div>
                    <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-300 to-rose-300">
                        Talent-Mind
                    </span>
                </Link>

                <nav className="hidden md:flex items-center gap-8 text-sm font-light text-white/60">
                    <Link href="/features" className="relative hover:text-white transition-colors group">
                        Features
                        <span className="absolute -bottom-1 left-0 w-0 h-[2px] bg-indigo-400 transition-all duration-300 group-hover:w-full"></span>
                    </Link>
                    <Link href="/features" className="relative hover:text-white transition-colors group">
                        How it Works
                        <span className="absolute -bottom-1 left-0 w-0 h-[2px] bg-indigo-400 transition-all duration-300 group-hover:w-full"></span>
                    </Link>
                    <Link href="/testimonials" className="relative hover:text-white transition-colors group">
                        Testimonials & Demo
                        <span className="absolute -bottom-1 left-0 w-0 h-[2px] bg-indigo-400 transition-all duration-300 group-hover:w-full"></span>
                    </Link>
                    <Link href="/pricing" className="relative hover:text-white transition-colors group">
                        Pricing
                        <span className="absolute -bottom-1 left-0 w-0 h-[2px] bg-indigo-400 transition-all duration-300 group-hover:w-full"></span>
                    </Link>
                    {isLoggedIn && (
                        <>
                            <Link href="/dashboard" className="relative hover:text-white transition-colors group">
                                Rank-Maker
                                <span className="absolute -bottom-1 left-0 w-0 h-[2px] bg-indigo-400 transition-all duration-300 group-hover:w-full"></span>
                            </Link>
                            <Link href="/profile" className="relative hover:text-white transition-colors group">
                                Profile
                                <span className="absolute -bottom-1 left-0 w-0 h-[2px] bg-indigo-400 transition-all duration-300 group-hover:w-full"></span>
                            </Link>
                        </>
                    )}
                </nav>

                <div className="flex items-center gap-4">
                    {!isLoggedIn ? (
                        <>
                            <Link href="/login" className="hidden sm:block">
                                <Button variant="ghost" className="text-white/80 hover:text-white hover:bg-white/[0.05] transition-all duration-300 hover:scale-105">
                                    Log in
                                </Button>
                            </Link>
                            <Link href="/login?view=register">
                                <Button className="bg-white text-black hover:bg-white/90 shadow-[0_0_20px_rgba(255,255,255,0.1)] hover:shadow-[0_0_25px_rgba(255,255,255,0.2)] transition-all duration-300 hover:scale-105">
                                    Get Started
                                </Button>
                            </Link>
                        </>
                    ) : (
                        <>
                            <Link href="/profile" className="hidden sm:flex items-center justify-center h-9 w-9 rounded-full bg-white/[0.05] border border-white/[0.1] hover:bg-white/[0.1] transition-colors">
                                <User className="h-4 w-4 text-white/70" />
                            </Link>
                            <Button 
                                onClick={handleLogout}
                                variant="ghost" 
                                className="text-white/60 hover:text-red-400 hover:bg-red-500/10 transition-all duration-300 px-3"
                            >
                                <LogOut className="h-4 w-4 mr-2" />
                                Logout
                            </Button>
                        </>
                    )}
                </div>
            </div>
        </header>
    );
}
