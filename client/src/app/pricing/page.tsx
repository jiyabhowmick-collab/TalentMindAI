import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { PricingBasic } from "@/components/demo-pricing";

export default function PricingPage() {
  return (
    <main className="bg-[#030303] min-h-screen pt-16">
      <Navbar />
      <PricingBasic />
      <Footer />
    </main>
  );
}
