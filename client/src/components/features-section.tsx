import { motion } from "framer-motion";
import { BrainCircuit, Search, Zap, UserCheck } from "lucide-react";
import { cn } from "@/lib/utils";
import { BGPattern } from "@/components/ui/bg-pattern";

const features = [
    {
        title: "Semantic Matching",
        description: "Go beyond simple keywords. Our AI understands the context and true meaning behind job descriptions and candidate resumes.",
        icon: BrainCircuit,
    },
    {
        title: "Hidden Gems",
        description: "Discover high-potential candidates whose true capabilities might be lost in the noise of traditional filters.",
        icon: Search,
    },
    {
        title: "Behavioral Signals",
        description: "Integrate activity signals and behavioral data to ensure a perfect cultural and operational fit.",
        icon: UserCheck,
    },
    {
        title: "Fast Shortlists",
        description: "Deliver highly accurate, ranked candidate shortlists in seconds, dramatically reducing time-to-hire.",
        icon: Zap,
    },
];

export function FeaturesSection() {
    return (
        <section id="features" className="relative w-full bg-[#030303] py-24 px-4 md:px-6 overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-b from-[#030303] via-indigo-900/[0.02] to-[#030303] pointer-events-none z-10" />
            
            <BGPattern 
                variant="checkerboard" 
                mask="fade-edges" 
                fill="rgba(99, 102, 241, 0.04)" 
                size={40} 
                className="absolute inset-0 opacity-60" 
            />
            
            <div className="relative z-10 max-w-6xl mx-auto">
                <div className="text-center mb-16 md:mb-24">
                    <h2 className="text-3xl md:text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-white/60 mb-4 tracking-tight">
                        Rank Candidates Intelligently
                    </h2>
                    <p className="text-white/40 text-lg max-w-2xl mx-auto font-light">
                        Traditional keyword filters miss the best talent. Discover how our Proof-of-Concept leverages AI to find the perfect fit.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 lg:gap-10">
                    {features.map((feature, index) => (
                        <div
                            key={index}
                            className={cn(
                                "group relative p-8 rounded-3xl bg-white/[0.02] border border-white/[0.05]",
                                "hover:bg-white/[0.04] transition-all duration-500 ease-in-out",
                                "hover:border-white/[0.1] hover:shadow-[0_8px_32px_0_rgba(255,255,255,0.05)]"
                            )}
                        >
                            <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-indigo-500/[0.05] via-transparent to-rose-500/[0.05] opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                            
                            <div className="relative z-10 flex flex-col gap-4">
                                <div className="h-12 w-12 rounded-full bg-white/[0.05] border border-white/[0.1] flex items-center justify-center group-hover:scale-110 transition-transform duration-500">
                                    <feature.icon className="h-5 w-5 text-indigo-400" />
                                </div>
                                <h3 className="text-xl font-semibold text-white/90">
                                    {feature.title}
                                </h3>
                                <p className="text-white/40 leading-relaxed font-light">
                                    {feature.description}
                                </p>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
}
