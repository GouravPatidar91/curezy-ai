import React from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';
import { Users, Activity, Sparkles, Quote, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function AboutUs() {
    const { scrollYProgress } = useScroll();
    const y = useTransform(scrollYProgress, [0, 1], ["0%", "50%"]);

    return (
        <div className="relative min-h-screen bg-[#050510] text-gray-300 overflow-hidden font-sans">
            <div className="fixed inset-0 pointer-events-none opacity-20" style={{ backgroundImage: 'radial-gradient(circle, #ffffff 1px, transparent 1px)', backgroundSize: '40px 40px' }} />

            <header className="relative pt-32 pb-20 px-6 max-w-5xl mx-auto z-10">
                <Link to="/" className="inline-flex items-center gap-2 text-gray-400 hover:text-white mb-12 transition-colors">
                    <ArrowLeft className="w-4 h-4" />
                    Back to Home
                </Link>
                <motion.h1 initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} className="text-5xl md:text-7xl font-bold tracking-tight text-white mb-6">
                    Minds over matter.<br />
                    <span className="text-[#FF7A00]">Data over doubt.</span>
                </motion.h1>
                <motion.p initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="text-xl text-gray-400 max-w-2xl leading-relaxed">
                    We're an elite team of engineers, clinical researchers, and data scientists fundamentally rewriting how medical diagnoses are formulated using multi-agent debate architecture.
                </motion.p>
            </header>

            <section className="relative px-6 py-20 bg-white/5 border-t border-b border-white/10 z-10">
                <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-12">
                    <div>
                        <Users className="w-8 h-8 text-[#4D4DFF] mb-4" />
                        <h3 className="text-white text-xl font-bold mb-3">The Council Model</h3>
                        <p className="text-sm leading-relaxed text-gray-400">Instead of relying on a single LLM, we engineered three proprietary expert models that debate each symptom input in real-time, drastically reducing hallucination.</p>
                    </div>
                    <div>
                        <Activity className="w-8 h-8 text-[#FF7A00] mb-4" />
                        <h3 className="text-white text-xl font-bold mb-3">Clinical Precision</h3>
                        <p className="text-sm leading-relaxed text-gray-400">Our models are fine-tuned on million-patient datasets, specialized radiological imaging, and peer-reviewed medical journals, enabling unparalleled diagnostic accuracy.</p>
                    </div>
                    <div>
                        <Sparkles className="w-8 h-8 text-purple-400 mb-4" />
                        <h3 className="text-white text-xl font-bold mb-3">Seamless Access</h3>
                        <p className="text-sm leading-relaxed text-gray-400">We believe world-class second opinions should be instantly available anywhere on earth. No waiting rooms, no clipboards, just instantaneous clarity.</p>
                    </div>
                </div>
            </section>

            <section className="relative px-6 py-32 max-w-4xl mx-auto z-10 text-center">
                <Quote className="w-12 h-12 text-[#FF7A00] mx-auto mb-8 opacity-50" />
                <h2 className="text-3xl md:text-4xl font-bold text-white leading-tight mb-8">
                    "Curezy AI didn't just automate triage; it gave our attending physicians a tireless, brilliant colleague that never sleeps and never stops reading."
                </h2>
                <p className="text-[#4D4DFF] font-bold tracking-widest uppercase text-sm">Dr. Sarah Jenkins, Head of Emergency Medicine</p>
            </section>
        </div>
    );
}
