import { HeroGeometric } from "@/components/ui/shape-landing-hero"
import { BGPattern } from "@/components/ui/bg-pattern"

export function DemoHeroGeometric() {
    return (
        <div className="relative min-h-[500px] w-full">
            <BGPattern 
                variant="grid" 
                mask="fade-bottom" 
                fill="rgba(99, 102, 241, 0.05)" 
                size={50} 
                className="absolute inset-0 z-0 opacity-40" 
            />
            <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/[0.05] via-transparent to-rose-500/[0.05] blur-3xl" />
            <div className="relative z-10">
                <HeroGeometric badge="Find Perfect"
                    title1="From Resumes "
                    title2="to Real Talent" />
            </div>
        </div>
    )
}
