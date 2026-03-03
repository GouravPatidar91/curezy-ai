import React from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, Rocket, MapPin, Briefcase, Zap } from 'lucide-react';
import { Link } from 'react-router-dom';

const JOBS = [
    { title: "Senior AI Engineer (LLM Inference)", location: "San Francisco, CA / Remote", type: "Full-Time", salary: "$180k - $250k" },
    { title: "Clinical Deep Learning Researcher", location: "New York, NY / Remote", type: "Full-Time", salary: "$200k - $280k" },
    { title: "Product Designer (Web3/AI)", location: "Remote", type: "Contract", salary: "$90 - $140/hr" },
    { title: "Chief Medical Officer (CMO)", location: "Remote", type: "Full-Time", salary: "Competitive + Equity" }
];

export default function Careers() {
    return (
        <div className="relative min-h-screen bg-[#050510] text-gray-300 overflow-hidden font-sans">
            <div className="fixed inset-0 pointer-events-none opacity-20" style={{ backgroundImage: 'radial-gradient(circle, #ffffff 1px, transparent 1px)', backgroundSize: '40px 40px' }} />

            <div className="max-w-5xl mx-auto px-6 py-24 relative z-10">
                <Link to="/" className="inline-flex items-center gap-2 text-gray-400 hover:text-white mb-12 transition-colors">
                    <ArrowLeft className="w-4 h-4" />
                    Back to Home
                </Link>

                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-20">
                    <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-white mb-6">Build the future of <span className="text-[#4D4DFF]">medicine.</span></h1>
                    <p className="text-xl text-gray-400 max-w-2xl leading-relaxed">
                        Join an elite team of hackers and doctors pushing the absolute bleeding edge of embodied clinical AI. We are well-funded, moving incredibly fast, and shipping world-changing features weekly.
                    </p>
                </motion.div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-20">
                    <div className="bg-white/5 border border-white/10 p-8 rounded-3xl">
                        <Rocket className="w-8 h-8 text-[#FF7A00] mb-4" />
                        <h3 className="text-white font-bold text-xl mb-2">High Velocity</h3>
                        <p className="text-sm text-gray-400">Zero corporate bureaucracy. We ship code directly to production and test against the hardest medical challenges daily.</p>
                    </div>
                    <div className="bg-white/5 border border-white/10 p-8 rounded-3xl">
                        <Zap className="w-8 h-8 text-[#4D4DFF] mb-4" />
                        <h3 className="text-white font-bold text-xl mb-2">Maximum Impact</h3>
                        <p className="text-sm text-gray-400">Your models won't optimize ad clicks; they will literally act as the second-opinion engine saving human lives globally.</p>
                    </div>
                </div>

                <div>
                    <h2 className="text-3xl font-bold text-white mb-8 border-b border-white/10 pb-4">Open Positions</h2>

                    <div className="space-y-4">
                        {JOBS.map((job, i) => (
                            <motion.div
                                key={i}
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: i * 0.1 }}
                                className="group flex flex-col md:flex-row md:items-center justify-between bg-white/5 hover:bg-white/10 border border-white/10 p-6 rounded-2xl transition-all cursor-pointer"
                            >
                                <div>
                                    <h3 className="text-xl font-bold text-white mb-2 group-hover:text-[#4D4DFF] transition-colors">{job.title}</h3>
                                    <div className="flex flex-wrap items-center gap-4 text-xs font-medium text-gray-400">
                                        <div className="flex items-center gap-1.5"><MapPin className="w-3.5 h-3.5" /> {job.location}</div>
                                        <div className="flex items-center gap-1.5"><Briefcase className="w-3.5 h-3.5" /> {job.type}</div>
                                        <div className="text-[#FF7A00]">{job.salary}</div>
                                    </div>
                                </div>
                                <button className="mt-4 md:mt-0 px-6 py-2 bg-white/10 text-white rounded-full font-semibold hover:bg-[#4D4DFF] hover:border-[#4D4DFF] border border-white/20 transition-all font-sans text-sm">
                                    Apply Now
                                </button>
                            </motion.div>
                        ))}
                    </div>

                    <div className="mt-12 text-center p-8 border border-dashed border-white/20 rounded-3xl bg-white/5">
                        <p className="text-gray-400 mb-4">Don't see a role that fits but still want to build with us?</p>
                        <a href="mailto:careers@curezy.com" className="text-white font-bold underline decoration-[#4D4DFF] underline-offset-4 hover:text-[#4D4DFF] transition-colors">
                            Send us your portfolio.
                        </a>
                    </div>
                </div>
            </div>
        </div>
    );
}
