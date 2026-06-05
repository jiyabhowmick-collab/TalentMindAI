import { DemoHeroGeometric } from "@/components/demo";
import { FeaturesSection } from "@/components/features-section";
import { Footer } from "@/components/footer";
import { Navbar } from "@/components/navbar";

export default function Home() {
  return (
    <main className="bg-[#030303] min-h-screen">
      <Navbar />
      <DemoHeroGeometric />
      <FeaturesSection />
      <Footer />
    </main>
  );
}
