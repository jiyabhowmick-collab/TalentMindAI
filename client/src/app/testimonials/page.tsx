import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { BGPattern } from "@/components/ui/bg-pattern";
import { Play } from "lucide-react";

const testimonials = [
  {
    quote: "Talent-Mind POC completely transformed our hiring process. We reduced our time-to-hire by 60% and found candidates we would have completely missed with standard keyword filters.",
    name: "Sarah Jenkins",
    role: "Head of Talent Acquisition, TechCorp",
    avatar: "S"
  },
  {
    quote: "The semantic matching is unbelievable. It understands the context of a candidate's experience rather than just looking for exact string matches. A game changer for tech recruitment.",
    name: "Marcus Aurelius",
    role: "Engineering Manager, DataSystems",
    avatar: "M"
  },
  {
    quote: "We used to spend hours manually screening resumes. Now, the AI gives us a perfectly ranked top 10 list instantly. The behavioral signals feature is especially impressive.",
    name: "Elena Rodriguez",
    role: "HR Director, GlobalTech",
    avatar: "E"
  }
];

export default function TestimonialsPage() {
  return (
    <main className="bg-[#030303] min-h-screen pt-16 flex flex-col relative overflow-hidden">
      {/* Global Background Pattern for the page */}
      <BGPattern 
          variant="checkerboard" 
          mask="fade-y" 
          fill="rgba(99, 102, 241, 0.03)" 
          size={40} 
          className="absolute inset-0 z-0 opacity-60" 
      />
      
      <div className="relative z-10 flex-grow">
        <Navbar />
        
        <div className="max-w-6xl mx-auto px-4 py-24">
          
          {/* Header */}
          <div className="text-center space-y-6 mb-20">
            <h1 className="text-4xl md:text-6xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-white/60 tracking-tight">
              See It In Action
            </h1>
            <p className="text-white/50 text-xl max-w-2xl mx-auto font-light leading-relaxed">
              Watch our live demo to see how semantic matching creates perfect candidate shortlists.
            </p>
          </div>

          {/* Video Section */}
          <div className="w-full max-w-4xl mx-auto mb-32 relative group cursor-pointer">
            <div className="absolute -inset-1 bg-gradient-to-r from-indigo-600 to-rose-600 rounded-2xl blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200"></div>
            <div className="relative aspect-video bg-[#0A0A0A] border border-white/10 rounded-2xl overflow-hidden flex flex-col items-center justify-center hover:border-indigo-500/30 transition-colors">
                <BGPattern variant="grid" mask="fade-center" fill="rgba(99,102,241,0.1)" size={20} className="absolute inset-0" />
                <div className="h-20 w-20 rounded-full bg-indigo-500/20 backdrop-blur-md flex items-center justify-center border border-indigo-500/30 group-hover:scale-110 transition-transform duration-500 z-10">
                    <Play className="h-8 w-8 text-indigo-400 translate-x-1" />
                </div>
                <span className="mt-6 text-white/50 font-light z-10">Demo Video Area (Add Video Here)</span>
            </div>
          </div>

          {/* Testimonials Grid */}
          <div className="text-center space-y-4 mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white/90">What Our Partners Say</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8">
            {testimonials.map((t, i) => (
              <div key={i} className="flex flex-col p-8 rounded-3xl bg-white/[0.02] border border-white/[0.05] hover:bg-white/[0.04] hover:border-white/[0.1] transition-all duration-300 relative backdrop-blur-sm">
                <div className="text-indigo-500/50 text-5xl font-serif absolute top-4 left-6">"</div>
                <p className="text-white/70 font-light leading-relaxed relative z-10 mt-4 mb-8 flex-grow">
                  {t.quote}
                </p>
                <div className="flex items-center gap-4 mt-auto">
                  <div className="h-12 w-12 rounded-full bg-gradient-to-br from-indigo-500 to-rose-600 flex items-center justify-center text-white font-bold text-lg">
                    {t.avatar}
                  </div>
                  <div className="flex flex-col">
                    <span className="text-white/90 font-medium">{t.name}</span>
                    <span className="text-white/40 text-sm font-light">{t.role}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>

        </div>
      </div>

      <Footer />
    </main>
  );
}
