"use client";

import { Pricing } from "@/components/blocks/pricing";

const demoPlans = [
  {
    name: "STARTER",
    badge: "VALUE",
    price: "49",
    yearlyPrice: "39",
    period: "per month",
    features: [
      "Up to 500 resume parses",
      "Basic keyword matching",
      "Standard candidate shortlisting",
      "Email support",
    ],
    description: "Perfect for independent recruiters and small agencies.",
    buttonText: "Start Free Trial",
    href: "#",
    isPopular: false,
  },
  {
    name: "PROFESSIONAL",
    badge: "POPULAR",
    price: "149",
    yearlyPrice: "119",
    period: "per month",
    features: [
      "Unlimited resume parsing",
      "Deep semantic matching AI",
      "Behavioral & activity signals",
      "Instant smart ranking",
      "Export to CSV/PDF",
      "Priority support",
    ],
    description: "Ideal for growing HR teams needing intelligent insights.",
    buttonText: "Get Started",
    href: "#",
    isPopular: true,
  },
  {
    name: "ENTERPRISE",
    badge: "PREMIUM",
    price: "499",
    yearlyPrice: "399",
    period: "per month",
    features: [
      "Everything in Professional",
      "Custom ATS integrations",
      "Dedicated account manager",
      "1-hour support response time",
      "SSO Authentication",
      "Custom AI model training",
    ],
    description: "For large organizations with high-volume hiring.",
    buttonText: "Contact Sales",
    href: "#",
    isPopular: false,
  },
];

export function PricingBasic() {
  return (
    <Pricing 
      plans={demoPlans}
      title="Simple, Transparent Pricing"
      description={"Choose the plan that works for you\nAll plans include access to our platform, lead generation tools, and dedicated support."}
    />
  );
}
