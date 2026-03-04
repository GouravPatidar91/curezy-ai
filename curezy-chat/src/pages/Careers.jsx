import React from "react";
import { motion } from "framer-motion";
import { ArrowLeft, Rocket, Zap } from "lucide-react";
import { Link } from "react-router-dom";

export default function Careers() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-[#050510] font-sans text-gray-300">
      {/* Background grid */}
      <div
        className="pointer-events-none fixed inset-0 opacity-20"
        style={{
          backgroundImage:
            "radial-gradient(circle, #ffffff 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />

      <div className="relative z-10 mx-auto max-w-5xl px-6 py-24">
        {/* Back link */}
        <Link
          to="/"
          className="mb-12 inline-flex items-center gap-2 text-gray-400 transition-colors hover:text-white"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Home
        </Link>

        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-20"
        >
          <h1 className="mb-6 text-5xl font-bold tracking-tight text-white md:text-7xl">
            Build the future of{" "}
            <span className="text-[#4D4DFF]">medicine.</span>
          </h1>

          <p className="max-w-2xl text-xl leading-relaxed text-gray-400">
            Join an elite team of hackers and doctors pushing the absolute
            bleeding edge of embodied clinical AI. We are well-funded, moving
            incredibly fast, and shipping world-changing features.
          </p>
        </motion.div>

        {/* Feature cards */}
        <div className="mb-20 grid grid-cols-1 gap-8 md:grid-cols-2">
          <div className="rounded-3xl border border-white/10 bg-white/5 p-8">
            <Rocket className="mb-4 h-8 w-8 text-[#FF7A00]" />
            <h3 className="mb-2 text-xl font-bold text-white">High Velocity</h3>
            <p className="text-sm text-gray-400">
              Zero corporate bureaucracy. We ship code directly to production
              and test against the hardest medical challenges daily.
            </p>
          </div>

          <div className="rounded-3xl border border-white/10 bg-white/5 p-8">
            <Zap className="mb-4 h-8 w-8 text-[#4D4DFF]" />
            <h3 className="mb-2 text-xl font-bold text-white">
              Maximum Impact
            </h3>
            <p className="text-sm text-gray-400">
              Your models won&apos;t optimize ad clicks; they will literally act
              as the second-opinion engine saving human lives globally.
            </p>
          </div>
        </div>

        {/* CTA */}
        <div className="mt-12 rounded-3xl border border-dashed border-white/20 bg-white/5 p-8 text-center">
          <p className="mb-4 text-gray-400">Want to build with us?</p>
          <a
            href="mailto:hr@curezy.in"
            className="font-bold text-white underline decoration-[#4D4DFF] underline-offset-4 transition-colors hover:text-[#4D4DFF]"
          >
            Send us your portfolio.
          </a>
        </div>
      </div>
    </div>
  );
}
