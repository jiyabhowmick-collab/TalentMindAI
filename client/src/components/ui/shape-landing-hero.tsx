"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Circle } from "lucide-react";
import { cn } from "@/lib/utils";
import { HoverButton } from "@/components/ui/hover-button";
import { useRouter } from "next/navigation";

// ── ElegantShape ─────────────────────────────────────────────────────────────
// Renders a single animated pill shape.
// `gradient`      – the base from-* class at rest  (opacity ~0.15)
// `hoverGradient` – the from-* class while hovered (opacity ~0.30)
//                   defaults to the same colour family at double opacity

function ElegantShape({
    className,
    delay = 0,
    width = 400,
    height = 100,
    rotate = 0,
    gradient = "from-white/[0.08]",
    hoverGradient,
}: {
    className?: string;
    delay?: number;
    width?: number;
    height?: number;
    rotate?: number;
    gradient?: string;
    hoverGradient?: string;
}) {
    // If no explicit hoverGradient supplied, auto-derive one by replacing
    // /[0.15] → /[0.30] in the base gradient string.
    const resolvedHoverGradient =
        hoverGradient ?? gradient.replace("/[0.15]", "/[0.30]");

    return (
        <motion.div
            initial={{ opacity: 0, y: -150, rotate: rotate - 15 }}
            animate={{ opacity: 1, y: 0, rotate }}
            transition={{
                duration: 2.4,
                delay,
                ease: [0.23, 0.86, 0.39, 0.96],
                opacity: { duration: 1.2 },
            }}
            className={cn("absolute", className)}
        >
            {/* Floating bob animation */}
            <motion.div
                animate={{ y: [0, 15, 0] }}
                transition={{
                    duration: 12,
                    repeat: Number.POSITIVE_INFINITY,
                    ease: "easeInOut",
                }}
                style={{ width, height }}
                className="relative"
            >
                {/* Hover handled via Framer Motion whileHover so opacity
                    interpolation works smoothly with arbitrary Tailwind values */}
                <motion.div
                    whileHover={{ scale: 1.06 }}
                    transition={{ duration: 0.5, ease: "easeOut" }}
                    className="relative w-full h-full group"
                >
                    {/* Rest state layer */}
                    <div
                        className={cn(
                            "absolute inset-0 rounded-full",
                            "bg-gradient-to-r to-transparent",
                            gradient,
                            "backdrop-blur-[2px] border-2 border-white/[0.15]",
                            "shadow-[0_8px_32px_0_rgba(255,255,255,0.1)]",
                            "after:absolute after:inset-0 after:rounded-full",
                            "after:bg-[radial-gradient(circle_at_50%_50%,rgba(255,255,255,0.2),transparent_70%)]",
                            "transition-opacity duration-500 opacity-100 group-hover:opacity-0"
                        )}
                    />

                    {/* Hover state layer — sits on top, fades in on hover */}
                    <div
                        className={cn(
                            "absolute inset-0 rounded-full",
                            "bg-gradient-to-r to-transparent",
                            resolvedHoverGradient,
                            "backdrop-blur-[2px] border-2 border-white/[0.25]",
                            "shadow-[0_8px_40px_0_rgba(255,255,255,0.25)]",
                            "after:absolute after:inset-0 after:rounded-full",
                            "after:bg-[radial-gradient(circle_at_50%_50%,rgba(255,255,255,0.25),transparent_70%)]",
                            "transition-opacity duration-500 opacity-0 group-hover:opacity-100"
                        )}
                    />
                </motion.div>
            </motion.div>
        </motion.div>
    );
}

// ── HeroGeometric ─────────────────────────────────────────────────────────────

function HeroGeometric({
    badge = "Design Collective",
    title1 = "Elevate Your Digital Vision",
    title2 = "Crafting Exceptional Websites",
}: {
    badge?: string;
    title1?: string;
    title2?: string;
}) {
    const router = useRouter();
    const [isLoggedIn, setIsLoggedIn] = useState<boolean | null>(null);

    useEffect(() => {
        setIsLoggedIn(!!localStorage.getItem("token"));
    }, []);

    const fadeUpVariants = {
        hidden: { opacity: 0, y: 30 },
        visible: (i: number) => ({
            opacity: 1,
            y: 0,
            transition: {
                duration: 1,
                delay: 0.5 + i * 0.2,
                ease: [0.25, 0.4, 0.25, 1] as const,
            },
        }),
    };

    return (
        <div className="relative min-h-screen w-full flex items-center justify-center overflow-hidden bg-[#030303]">

            {/* ── Background ambient glow ── */}
            <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/[0.05] via-transparent to-rose-500/[0.05] blur-3xl" />

            {/* ── Floating shapes ── */}
            <div className="absolute inset-0 overflow-hidden">

                {/* Shape 1 */}
                <ElegantShape
                    delay={0.3}
                    width={600}
                    height={140}
                    rotate={12}
                    gradient="from-indigo-500/[0.15]"
                    className="left-[-10%] md:left-[-5%] top-[15%] md:top-[20%]"
                />

                {/* Shape 2 */}
                <ElegantShape
                    delay={0.5}
                    width={500}
                    height={120}
                    rotate={-15}
                    gradient="from-rose-500/[0.15]"
                    className="right-[-5%] md:right-[0%] top-[70%] md:top-[75%]"
                />

                {/* Shape 3 */}
                <ElegantShape
                    delay={0.4}
                    width={300}
                    height={80}
                    rotate={-8}
                    gradient="from-violet-500/[0.15]"
                    className="left-[5%] md:left-[10%] bottom-[5%] md:bottom-[10%]"
                />

                {/* Shape 4 */}
                <ElegantShape
                    delay={0.6}
                    width={200}
                    height={60}
                    rotate={20}
                    gradient="from-amber-500/[0.15]"
                    className="right-[15%] md:right-[20%] top-[10%] md:top-[15%]"
                />

                {/* Shape 5 */}
                <ElegantShape
                    delay={0.7}
                    width={150}
                    height={40}
                    rotate={-25}
                    gradient="from-cyan-500/[0.15]"
                    className="left-[20%] md:left-[25%] top-[5%] md:top-[10%]"
                />
            </div>

            {/* ── Hero content ── */}
            <div className="relative z-10 container mx-auto px-4 md:px-6">
                <div className="max-w-3xl mx-auto text-center">

                    {/* Badge */}
                    <motion.div
                        custom={0}
                        variants={fadeUpVariants}
                        initial="hidden"
                        animate="visible"
                        className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/[0.03] border border-white/[0.08] mb-8 md:mb-12"
                    >
                        <Circle className="h-2 w-2 fill-rose-500/80" />
                        <span className="text-sm text-white/60 tracking-wide">
                            {badge}
                        </span>
                    </motion.div>

                    {/* Title */}
                    <motion.div
                        custom={1}
                        variants={fadeUpVariants}
                        initial="hidden"
                        animate="visible"
                    >
                        <h1 className="text-4xl sm:text-6xl md:text-8xl font-bold mb-6 md:mb-8 tracking-tight">
                            <span className="bg-clip-text text-transparent bg-gradient-to-b from-white to-white/80">
                                {title1}
                            </span>
                            <br />
                            <span
                                className={cn(
                                    "bg-clip-text text-transparent",
                                    "bg-gradient-to-r from-indigo-300 via-white/90 to-rose-300"
                                )}
                            >
                                {title2}
                            </span>
                        </h1>
                    </motion.div>

                    {/* Subtitle */}
                    <motion.div
                        custom={2}
                        variants={fadeUpVariants}
                        initial="hidden"
                        animate="visible"
                    >
                        <p className="text-base sm:text-lg md:text-xl text-white/40 mb-8 leading-relaxed font-light tracking-wide max-w-xl mx-auto px-4">
                            Transform thousands of applications into a shortlist of qualified, job-ready candidates in minutes.
                        </p>
                    </motion.div>

                    {/* CTA buttons */}
                    <motion.div
                        custom={3}
                        variants={fadeUpVariants}
                        initial="hidden"
                        animate="visible"
                        className="flex flex-col sm:flex-row items-center justify-center gap-4"
                    >
                        <HoverButton
                            onClick={() => router.push(isLoggedIn ? '/dashboard' : '/login')}
                            className="group relative inline-flex items-center gap-2"
                        >
                            <span>{isLoggedIn === false ? "Sign up to Start Ranking" : "Start Ranking"}</span>
                            <svg
                                className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-1 inline"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                                strokeWidth={2}
                            >
                                <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                            </svg>
                        </HoverButton>
                        <a
                            href="/how-it-works"
                            className="inline-flex items-center gap-2 px-8 py-3.5 rounded-xl border border-white/10 bg-white/[0.03] text-white/70 hover:text-white hover:border-indigo-500/40 hover:bg-white/[0.06] font-medium text-sm transition-all duration-300 hover:scale-105"
                        >
                            See How It Works
                        </a>
                    </motion.div>
                </div>
            </div>

            {/* ── Top/bottom fade vignette ── */}
            <div className="absolute inset-0 bg-gradient-to-t from-[#030303] via-transparent to-[#030303]/80 pointer-events-none" />
        </div>
    );
}

export { HeroGeometric };
