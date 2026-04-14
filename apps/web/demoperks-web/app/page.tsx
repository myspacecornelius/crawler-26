import Link from "next/link";
import { Gift, Search, Bookmark, ArrowRight } from "lucide-react";

export default function HomePage() {
  return (
    <div className="animate-fade-in">
      {/* ─── Hero ─────────────────────────────────────── */}
      <section className="relative overflow-hidden py-24 sm:py-32">
        <div className="absolute inset-0 -z-10">
          <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] rounded-full bg-brand-600/20 blur-[120px]" />
        </div>

        <div className="mx-auto max-w-4xl px-6 text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-zinc-800 bg-zinc-900/60 px-4 py-1.5 text-sm text-zinc-400 mb-8">
            <Gift className="h-4 w-4 text-brand-400" />
            <span>Discover B2B demo incentives</span>
          </div>

          <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight leading-tight">
            Get <span className="gradient-text">rewarded</span> for evaluating software
          </h1>

          <p className="mt-6 text-lg sm:text-xl text-zinc-400 max-w-2xl mx-auto leading-relaxed">
            Demo Offers is the directory for vendor-sponsored B2B demo incentives.
            Find gift cards, credits, and perks offered by top software companies —
            just for taking a product demo.
          </p>

          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/offers"
              className="inline-flex items-center gap-2 rounded-lg bg-brand-600 hover:bg-brand-500 text-white px-8 py-3.5 font-semibold transition-colors text-lg"
            >
              Browse Offers
              <ArrowRight className="h-5 w-5" />
            </Link>
            <Link
              href="/auth/signup"
              className="inline-flex items-center gap-2 rounded-lg border border-zinc-700 hover:border-zinc-500 text-zinc-300 hover:text-white px-8 py-3.5 font-semibold transition-colors text-lg"
            >
              Create Account
            </Link>
          </div>
        </div>
      </section>

      {/* ─── How It Works ─────────────────────────────── */}
      <section className="py-20 border-t border-zinc-800/50">
        <div className="mx-auto max-w-5xl px-6">
          <h2 className="text-2xl sm:text-3xl font-bold text-center mb-16">
            How it works
          </h2>

          <div className="grid sm:grid-cols-3 gap-8">
            {[
              {
                icon: Search,
                title: "Discover",
                desc: "Browse verified demo incentive offers from B2B software vendors.",
              },
              {
                icon: Gift,
                title: "Evaluate",
                desc: "Take a product demo and meet the simple requirements to qualify.",
              },
              {
                icon: Bookmark,
                title: "Earn",
                desc: "Receive your reward — gift cards, account credits, or exclusive perks.",
              },
            ].map((step, i) => (
              <div
                key={i}
                className="glass rounded-xl p-8 text-center hover-lift"
              >
                <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-full bg-brand-600/15 text-brand-400">
                  <step.icon className="h-7 w-7" />
                </div>
                <h3 className="text-lg font-semibold mb-2">{step.title}</h3>
                <p className="text-zinc-400 text-sm leading-relaxed">
                  {step.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── CTA ──────────────────────────────────────── */}
      <section className="py-20 border-t border-zinc-800/50">
        <div className="mx-auto max-w-3xl px-6 text-center">
          <h2 className="text-2xl sm:text-3xl font-bold mb-4">
            Ready to get started?
          </h2>
          <p className="text-zinc-400 mb-8 text-lg">
            Join professionals who are already saving and earning through demo
            incentives.
          </p>
          <Link
            href="/offers"
            className="inline-flex items-center gap-2 rounded-lg bg-brand-600 hover:bg-brand-500 text-white px-8 py-3.5 font-semibold transition-colors"
          >
            Explore Offers
            <ArrowRight className="h-5 w-5" />
          </Link>
        </div>
      </section>
    </div>
  );
}
