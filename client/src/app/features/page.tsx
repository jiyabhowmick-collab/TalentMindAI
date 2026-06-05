import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { BGPattern } from "@/components/ui/bg-pattern";
import { FileText, BrainCircuit, Crosshair, ListOrdered, Download, ArrowDown } from "lucide-react";

export default function FeaturesPage() {
  const flowSteps = [
    {
      id: 1,
      title: "Step 1: Input Data & Configuration",
      subtitle: "JD (text/upload) + Candidate CSV",
      description: "Recruiters start by uploading the Job Description (JD) and a bulk candidate CSV file containing resumes and details. You can configure specific parameters like required skills, experience thresholds, and preferred educational backgrounds right at the beginning.",
      icon: FileText,
      color: "text-indigo-400",
      bg: "bg-indigo-400/10",
      border: "border-indigo-500/20"
    },
    {
      id: 2,
      title: "Step 2: Deep AI Analysis",
      subtitle: "Extracting key requirements & skills",
      description: "Our core AI engine processes the JD to extract not just explicit keywords, but implicit requirements. It builds a semantic profile of the ideal candidate, parsing through complex industry jargon to understand exactly what the role demands.",
      icon: BrainCircuit,
      color: "text-rose-400",
      bg: "bg-rose-400/10",
      border: "border-rose-500/20"
    },
    {
      id: 3,
      title: "Step 3: Semantic & Behavioral Matching",
      subtitle: "Match each candidate AGAINST the JD semantically",
      description: "Traditional ATS systems rely on exact keyword matches. We go beyond that. The engine semantically compares each candidate's resume against the synthesized JD profile, understanding context, synonyms, and even behavioral activity signals to find hidden gems.",
      icon: Crosshair,
      color: "text-indigo-500",
      bg: "bg-indigo-500/10",
      border: "border-indigo-600/20"
    },
    {
      id: 4,
      title: "Step 4: Intelligent Scoring & Ranking",
      subtitle: "Rank by fit score & behavioral signals",
      description: "Every candidate is assigned a multi-dimensional Fit Score. This score aggregates semantic match accuracy, experience alignment, and cultural fit predictions. The system automatically ranks thousands of candidates from best-fit to worst-fit in seconds.",
      icon: ListOrdered,
      color: "text-rose-500",
      bg: "bg-rose-500/10",
      border: "border-rose-600/20"
    },
    {
      id: 5,
      title: "Step 5: Tiered Results Export",
      subtitle: "Output: Top 1000 → 100 → 50 → 10 CSVs",
      description: "Finally, the system generates neatly organized CSV outputs tiered by quality. You can instantly download the Top 10 for immediate interviews, the Top 50 for a broader review, or full analytics for your entire candidate pool.",
      icon: Download,
      color: "text-indigo-400",
      bg: "bg-indigo-400/10",
      border: "border-indigo-500/20"
    }
  ];

  return (
    <main className="bg-[#030303] min-h-screen pt-16 flex flex-col">
      <Navbar />
      
      <div className="relative flex-grow flex flex-col items-center py-24 px-4 md:px-8 overflow-hidden">
        {/* Background Pattern */}
        <BGPattern 
            variant="checkerboard" 
            mask="fade-edges" 
            fill="rgba(99, 102, 241, 0.03)" 
            size={40} 
            className="absolute inset-0 opacity-50" 
        />
        
        <div className="relative z-10 max-w-5xl mx-auto w-full">
          <div className="text-center space-y-6 mb-24">
            <h1 className="text-4xl md:text-6xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-white/60 tracking-tight">
              Under the Hood
            </h1>
            <p className="text-white/50 text-xl max-w-3xl mx-auto font-light leading-relaxed">
              We've completely re-engineered the recruitment pipeline. Here is exactly how our AI transforms raw data into a highly accurate, ranked shortlist in just a few clicks.
            </p>
          </div>

          <div className="flex flex-col max-w-3xl mx-auto">
            {flowSteps.map((step, index) => (
              <div key={step.id} className="w-full flex flex-col md:flex-row gap-8 items-start mb-16 md:mb-24 group relative z-10">
                
                {/* Icon */}
                <div className={`h-20 w-20 shrink-0 rounded-2xl flex items-center justify-center ${step.bg} border border-white/10 shadow-[0_0_30px_rgba(99,102,241,0.05)] transition-transform duration-500`}>
                    <step.icon className={`h-8 w-8 ${step.color}`} />
                </div>

                {/* Content */}
                <div className="flex flex-col flex-1 pt-2">
                  <h3 className="text-3xl font-bold text-white/90 mb-3">{step.title}</h3>
                  <h4 className="text-indigo-400 font-medium text-lg mb-4">{step.subtitle}</h4>
                  <p className="text-white/60 font-light leading-relaxed text-lg">{step.description}</p>
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
