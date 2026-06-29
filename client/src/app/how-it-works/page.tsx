"use client";

import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { BGPattern } from "@/components/ui/bg-pattern";
import { 
  FileText, 
  BrainCircuit, 
  Crosshair, 
  ListOrdered, 
  Download, 
  ArrowRight,
  Database,
  Cpu,
  Filter,
  CheckCircle2,
  Settings,
  Server,
  ArrowDown
} from "lucide-react";
import { motion } from "framer-motion";

export default function HowItWorksPage() {
  const flowSteps = [
    {
      id: 1,
      title: "Step 1: Parallel Parsing & Pre-filtering",
      subtitle: "JD-Adaptive Triage at O(n) Speed",
      description: "Upload a Job Description and a bulk candidate file (100k+ records). Our ThreadPool parsing engine ingests the data in parallel, while an intelligent pre-filter instantly eliminates up to 85% of irrelevant candidates by analyzing JD-specific title and skill keywords.",
      icon: Database,
      color: "text-indigo-400",
      bg: "bg-indigo-400/10",
      border: "border-indigo-500/20"
    },
    {
      id: 2,
      title: "Step 2: Targeted Normalization",
      subtitle: "Focusing Compute on True Contenders",
      description: "Instead of wasting time processing everyone, we run expensive data normalization only on the survivors of the pre-filter. This standardizes candidate profiles, extracts structured signals, and enables lightning-fast real-time performance.",
      icon: Settings,
      color: "text-rose-400",
      bg: "bg-rose-400/10",
      border: "border-rose-500/20"
    },
    {
      id: 3,
      title: "Step 3: Multi-Dimensional Semantic Scoring",
      subtitle: "Token-Overlap, Jaccard Similarity & Synonym Expansion",
      description: "Our engine evaluates candidates across 5 dimensions: JD Title relevance, Skill F-beta scoring with broad synonym expansion, TF-IDF token-overlap, experience fit, and seniority alignment. It goes far beyond simple keyword matching.",
      icon: BrainCircuit,
      color: "text-indigo-500",
      bg: "bg-indigo-500/10",
      border: "border-indigo-600/20"
    },
    {
      id: 4,
      title: "Step 4: Fast Selection & Behavioral Reranking",
      subtitle: "O(n log k) Sorting + Signal Boosts",
      description: "We utilize highly optimized algorithms (heapq) to instantly select the top candidates. Then, an aggressive reranking pass boosts the absolute best based on crucial behavioral signals like response rates, notice periods, and interview completion.",
      icon: ListOrdered,
      color: "text-rose-500",
      bg: "bg-rose-500/10",
      border: "border-rose-600/20"
    },
    {
      id: 5,
      title: "Step 5: Actionable Results Export",
      subtitle: "Tiered CSVs and Dynamic Reasonings",
      description: "The system outputs neatly organized, monotonically scored candidates, complete with dynamically generated AI reasonings explaining exactly why they fit (or what they lack). Download the Top 10, 50, or 100 for immediate action.",
      icon: Download,
      color: "text-indigo-400",
      bg: "bg-indigo-400/10",
      border: "border-indigo-500/20"
    }
  ];

  return (
    <main className="bg-[#030303] min-h-screen pt-16 flex flex-col font-sans">
      <Navbar />
      
      <div className="relative flex-grow flex flex-col items-center py-24 px-4 md:px-8 overflow-hidden">
        {/* Background Pattern */}
        <BGPattern 
            variant="checkerboard" 
            mask="fade-edges" 
            fill="rgba(99, 102, 241, 0.03)" 
            size={40} 
            className="absolute inset-0 opacity-50 pointer-events-none" 
        />
        
        <div className="relative z-10 max-w-5xl mx-auto w-full">
          <div className="text-center space-y-6 mb-24">
            <h1 className="text-4xl md:text-6xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-white/60 tracking-tight">
              How It Works
            </h1>
            <p className="text-white/50 text-xl max-w-3xl mx-auto font-light leading-relaxed">
              We've completely re-engineered the recruitment pipeline. Discover how our optimized, JD-adaptive architecture transforms raw candidate datasets into a highly accurate, ranked shortlist in just seconds.
            </p>
          </div>

          <div className="flex flex-col max-w-3xl mx-auto mb-32">
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

          {/* Architecture Diagram Section */}
          <div className="pt-20 border-t border-white/5">
            <div className="text-center space-y-4 mb-16">
              <h2 className="text-3xl md:text-5xl font-bold text-white tracking-tight">
                Pipeline Architecture
              </h2>
              <p className="text-white/50 text-lg">
                The 3-phase, highly optimized flow
              </p>
            </div>

            <ArchitectureDiagram />
          </div>

        </div>
      </div>

      <Footer />
    </main>
  );
}

function ArchitectureDiagram() {
  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.3
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 300, damping: 24 } }
  };

  return (
    <div className="relative w-full max-w-4xl mx-auto bg-white/[0.02] border border-white/10 rounded-3xl p-8 md:p-16 overflow-hidden">
      
      {/* Animated Flow Lines */}
      <div className="absolute inset-0 opacity-20 pointer-events-none flex justify-center">
        <div className="w-[2px] h-full bg-gradient-to-b from-indigo-500/0 via-indigo-500 to-rose-500/0" />
      </div>

      <motion.div 
        variants={containerVariants}
        initial="hidden"
        whileInView="show"
        viewport={{ once: true, margin: "-100px" }}
        className="relative z-10 flex flex-col items-center space-y-12"
      >
        {/* Phase 1 Inputs */}
        <motion.div variants={itemVariants} className="flex flex-col sm:flex-row gap-6 w-full justify-center">
          <div className="bg-neutral-900/80 border border-white/10 rounded-2xl p-6 text-center w-full sm:w-64 backdrop-blur-sm">
            <FileText className="h-8 w-8 text-indigo-400 mx-auto mb-3" />
            <h4 className="text-white font-medium">Raw Candidates</h4>
            <p className="text-white/40 text-sm mt-1">100k+ JSONL Records</p>
          </div>
          <div className="bg-neutral-900/80 border border-white/10 rounded-2xl p-6 text-center w-full sm:w-64 backdrop-blur-sm">
            <Server className="h-8 w-8 text-indigo-400 mx-auto mb-3" />
            <h4 className="text-white font-medium">Job Description</h4>
            <p className="text-white/40 text-sm mt-1">Requirements & Domain</p>
          </div>
        </motion.div>

        <motion.div variants={itemVariants} className="flex justify-center w-full">
          <ArrowDown className="h-6 w-6 text-white/20 animate-bounce" />
        </motion.div>

        {/* Phase 1 Parser & Filter */}
        <motion.div variants={itemVariants} className="bg-indigo-500/10 border border-indigo-500/20 rounded-2xl p-6 md:p-8 w-full max-w-2xl backdrop-blur-sm relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/0 via-indigo-500/5 to-indigo-500/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
          <div className="flex items-center gap-4 mb-4">
            <div className="h-10 w-10 bg-indigo-500/20 rounded-lg flex items-center justify-center">
              <Filter className="h-5 w-5 text-indigo-400" />
            </div>
            <div>
              <h3 className="text-white font-bold text-xl">Phase 1: Parse & Pre-Filter</h3>
              <p className="text-indigo-300/80 text-sm">Thread-Pool Executor + JD-Adaptive Triage</p>
            </div>
          </div>
          <div className="bg-black/40 rounded-xl p-4 text-white/60 text-sm border border-white/5">
            <span className="text-rose-400 font-medium line-through mr-2">Discards ~85%</span> 
            <span>Instantly removes candidates lacking core title/skill overlap at O(n) speed.</span>
          </div>
        </motion.div>

        <motion.div variants={itemVariants} className="flex justify-center w-full">
          <ArrowDown className="h-6 w-6 text-white/20 animate-bounce" />
        </motion.div>

        {/* Phase 2 Scorer */}
        <motion.div variants={itemVariants} className="bg-purple-500/10 border border-purple-500/20 rounded-2xl p-6 md:p-8 w-full max-w-2xl backdrop-blur-sm relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-r from-purple-500/0 via-purple-500/5 to-purple-500/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
          <div className="flex items-center gap-4 mb-4">
            <div className="h-10 w-10 bg-purple-500/20 rounded-lg flex items-center justify-center">
              <Cpu className="h-5 w-5 text-purple-400" />
            </div>
            <div>
              <h3 className="text-white font-bold text-xl">Phase 2: Normalize & Score</h3>
              <p className="text-purple-300/80 text-sm">Focused Computation (~15k Survivors)</p>
            </div>
          </div>
          <div className="bg-black/40 rounded-xl p-4 text-white/60 text-sm border border-white/5 flex flex-wrap gap-2">
            <span className="bg-white/5 px-2 py-1 rounded text-xs text-white/80">Jaccard Title Overlap</span>
            <span className="bg-white/5 px-2 py-1 rounded text-xs text-white/80">Skill F-Beta Expansion</span>
            <span className="bg-white/5 px-2 py-1 rounded text-xs text-white/80">Token-Overlap Analysis</span>
            <span className="bg-white/5 px-2 py-1 rounded text-xs text-white/80">Exp & Seniority Match</span>
          </div>
        </motion.div>

        <motion.div variants={itemVariants} className="flex justify-center w-full">
          <ArrowDown className="h-6 w-6 text-white/20 animate-bounce" />
        </motion.div>

        {/* Phase 3 Ranker */}
        <motion.div variants={itemVariants} className="bg-rose-500/10 border border-rose-500/20 rounded-2xl p-6 md:p-8 w-full max-w-2xl backdrop-blur-sm relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-r from-rose-500/0 via-rose-500/5 to-rose-500/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
          <div className="flex items-center gap-4 mb-4">
            <div className="h-10 w-10 bg-rose-500/20 rounded-lg flex items-center justify-center">
              <ListOrdered className="h-5 w-5 text-rose-400" />
            </div>
            <div>
              <h3 className="text-white font-bold text-xl">Phase 3: Fast Select & Rerank</h3>
              <p className="text-rose-300/80 text-sm">heapq Selection + Behavioral Boosts</p>
            </div>
          </div>
          <div className="bg-black/40 rounded-xl p-4 text-white/60 text-sm border border-white/5">
            O(n log k) selection pulls the absolute best candidates instantly. Top 10 are reranked based on behavioral engagement (response rates, notice periods).
          </div>
        </motion.div>

        <motion.div variants={itemVariants} className="flex justify-center w-full">
          <ArrowDown className="h-6 w-6 text-white/20 animate-bounce" />
        </motion.div>

        {/* Output */}
        <motion.div variants={itemVariants} className="bg-neutral-900/80 border border-emerald-500/30 rounded-2xl p-6 text-center w-full max-w-sm backdrop-blur-sm shadow-[0_0_30px_rgba(16,185,129,0.1)]">
          <CheckCircle2 className="h-10 w-10 text-emerald-400 mx-auto mb-3" />
          <h4 className="text-white font-bold text-xl">Ranked Shortlist</h4>
          <p className="text-emerald-400/80 text-sm mt-1">Tiered Export (Top 10 / 50 / 100)</p>
        </motion.div>

      </motion.div>
    </div>
  );
}
