"use client";

import { buttonVariants } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { useMediaQuery } from "@/hooks/use-media-query";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import { Check, Star } from "lucide-react";
import Link from "next/link";
import { useState, useRef } from "react";
import confetti from "canvas-confetti";
import NumberFlow from "@number-flow/react";
import { BGPattern } from "@/components/ui/bg-pattern";

interface PricingPlan {
  name: string;
  price: string;
  yearlyPrice: string;
  period: string;
  features: string[];
  description: string;
  buttonText: string;
  href: string;
  isPopular: boolean;
  badge?: string;
}

interface PricingProps {
  plans: PricingPlan[];
  title?: string;
  description?: string;
}

export function Pricing({
  plans,
  title = "Simple, Transparent Pricing",
  description = "Choose the plan that works for you\nAll plans include access to our platform, lead generation tools, and dedicated support.",
}: PricingProps) {
  const [isMonthly, setIsMonthly] = useState(true);
  const isDesktop = useMediaQuery("(min-width: 768px)");
  const [selectedPlanIndex, setSelectedPlanIndex] = useState<number>(
    plans.findIndex((p) => p.isPopular) !== -1 ? plans.findIndex((p) => p.isPopular) : 1
  );
  const switchRef = useRef<HTMLButtonElement>(null);

  const handleToggle = (checked: boolean) => {
    setIsMonthly(!checked);
    if (checked && switchRef.current) {
      const rect = switchRef.current.getBoundingClientRect();
      const x = rect.left + rect.width / 2;
      const y = rect.top + rect.height / 2;

      confetti({
        particleCount: 50,
        spread: 60,
        origin: {
          x: x / window.innerWidth,
          y: y / window.innerHeight,
        },
        colors: [
          "#ea580c", // indigo-600
          "#fb923c", // indigo-400
          "#f59e0b", // rose-500
          "#fbbf24", // rose-400
        ],
        ticks: 200,
        gravity: 1.2,
        decay: 0.94,
        startVelocity: 30,
        shapes: ["circle"],
      });
    }
  };

  return (
    <div id="pricing" className="w-full relative bg-[#030303] py-24 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-t from-indigo-500/[0.02] via-transparent to-[#030303] pointer-events-none z-10" />
        <BGPattern 
            variant="checkerboard" 
            mask="fade-edges" 
            fill="rgba(99, 102, 241, 0.03)" 
            size={40} 
            className="absolute inset-0 opacity-50" 
        />
      <div className="relative z-10 max-w-6xl mx-auto px-4 md:px-6">
      <div className="text-center space-y-4 mb-12">
        <h2 className="text-4xl md:text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-white/60 tracking-tight">
          {title}
        </h2>
        <p className="text-white/40 text-lg whitespace-pre-line max-w-2xl mx-auto font-light">
          {description}
        </p>
      </div>

      <div className="flex justify-center items-center gap-3 mb-16">
        <span className={cn("text-sm font-medium transition-colors", isMonthly ? "text-white/90" : "text-white/40")}>Monthly</span>
        <label className="relative inline-flex items-center cursor-pointer">
          <Label>
            <Switch
              ref={switchRef as any}
              checked={!isMonthly}
              onCheckedChange={handleToggle}
              className="relative"
            />
          </Label>
        </label>
        <span className={cn("text-sm font-medium transition-colors", !isMonthly ? "text-white/90" : "text-white/40")}>
          Annually <span className="text-indigo-400 ml-1">(Save 20%)</span>
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8">
        {plans.map((plan, index) => {
          const isSelected = selectedPlanIndex === index;
          return (
          <motion.div
            key={`${index}-${isMonthly}`}
            onClick={() => setSelectedPlanIndex(index)}
            initial={{ y: 50, opacity: 0, scale: 0.95 }}
            animate={
              isDesktop
                ? {
                    y: isSelected ? -20 : 0,
                    opacity: 1,
                    scale: 1,
                  }
                : {
                    y: 0,
                    opacity: 1,
                    scale: 1,
                  }
            }
            transition={{
              duration: 0.4,
              type: "spring",
              stiffness: 300,
              damping: 25,
            }}
            className={cn(
              `rounded-3xl border-[1px] p-8 bg-white/[0.02] text-center lg:flex lg:flex-col lg:justify-center relative backdrop-blur-sm transition-all duration-300 ease-in-out hover:bg-white/[0.04] hover:border-white/[0.1] hover:shadow-[0_8px_32px_0_rgba(255,255,255,0.05)] cursor-pointer`,
              isSelected ? "border-indigo-500/50 shadow-[0_0_40px_rgba(99,102,241,0.1)] hover:border-indigo-500/70" : "border-white/[0.05]",
              "flex flex-col group",
              !isSelected && "mt-5 lg:mt-0"
            )}
          >
            {isSelected && (
              <div className="absolute top-0 right-8 bg-indigo-600/20 border border-indigo-500/30 py-1 px-3 rounded-b-xl flex items-center">
                <Star className="text-indigo-400 h-3 w-3 fill-current" />
                <span className="text-indigo-400 ml-1.5 text-xs font-semibold uppercase tracking-wider">
                  {plan.badge || "POPULAR"}
                </span>
              </div>
            )}
            <div className="flex-1 flex flex-col">
              <p className="text-lg font-semibold text-white/90">
                {plan.name}
              </p>
              <div className="mt-6 flex items-center justify-center gap-x-2">
                <span className="text-5xl font-bold tracking-tight text-white">
                  <NumberFlow
                    value={
                      isMonthly ? Number(plan.price) : Number(plan.yearlyPrice)
                    }
                    format={{
                      style: "currency",
                      currency: "USD",
                      minimumFractionDigits: 0,
                      maximumFractionDigits: 0,
                    }}
                    transformTiming={{
                      duration: 500,
                      easing: "ease-out",
                    }}
                    willChange
                    className="font-variant-numeric: tabular-nums"
                  />
                </span>
                {plan.period !== "Next 3 months" && (
                  <span className="text-sm font-semibold leading-6 tracking-wide text-white/40">
                    / {plan.period}
                  </span>
                )}
              </div>

              <p className="text-xs leading-5 text-white/40 mt-2">
                {isMonthly ? "billed monthly" : "billed annually"}
              </p>

              <ul className="mt-8 gap-4 flex flex-col">
                {plan.features.map((feature, idx) => (
                  <li key={idx} className="flex items-start gap-3">
                    <Check className="h-5 w-5 text-indigo-400 flex-shrink-0" />
                    <span className="text-left text-white/70 font-light">{feature}</span>
                  </li>
                ))}
              </ul>

              <hr className="w-full my-8 border-white/[0.05]" />

              <Link
                href={plan.href}
                className={cn(
                  buttonVariants({
                    variant: "default",
                  }),
                  "w-full transition-all duration-300",
                  isSelected
                    ? "bg-indigo-600 hover:bg-indigo-500 text-white border-0 hover:scale-105 hover:shadow-[0_0_20px_rgba(99,102,241,0.4)]"
                    : "bg-white/[0.03] hover:bg-white/[0.08] text-white hover:text-white border border-white/[0.1] hover:scale-105 hover:border-white/[0.2]"
                )}
              >
                {plan.buttonText}
              </Link>
              <p className="mt-6 text-xs leading-5 text-white/30 font-light">
                {plan.description}
              </p>
            </div>
          </motion.div>
          );
        })}
      </div>
      </div>
    </div>
  );
}
