import React, { useRef, useState } from 'react';
import { motion, useScroll, useMotionValueEvent, AnimatePresence } from 'framer-motion';
import { CheckCircle2, BrainCircuit, ActivitySquare, Database, MessageSquare } from 'lucide-react';

const CouncilVisual = () => (
    <div className="relative w-full flex-1 min-h-[220px] bg-gradient-to-b from-white/5 to-transparent rounded-2xl border border-white/10 mb-6 flex items-center justify-center overflow-hidden">
        {/* Abstract Isometric / Floating 3D Grid background */}
        <div className="absolute inset-0 opacity-20" style={{ backgroundImage: 'linear-gradient(#ffffff 1px, transparent 1px), linear-gradient(90deg, #ffffff 1px, transparent 1px)', backgroundSize: '20px 20px', transform: 'perspective(500px) rotateX(60deg) scale(2)' }} />

        {/* Neural Network Nodes */}
        <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 20, ease: "linear" }} className="absolute w-48 h-48 border border-white/5 rounded-full flex items-center justify-center">
            <div className="absolute -top-2 left-1/2 w-4 h-4 bg-[#FF7A00] rounded-full shadow-[0_0_15px_#FF7A00]" />
            <div className="absolute bottom-4 -left-1 w-3 h-3 bg-[#4D4DFF] rounded-full shadow-[0_0_15px_#4D4DFF]" />
            <div className="absolute bottom-2 -right-2 w-5 h-5 bg-white rounded-full shadow-[0_0_10px_white]" />
        </motion.div>

        {/* Central Core */}
        <div className="relative z-10 w-20 h-20 bg-black/80 backdrop-blur-xl border border-white/20 rounded-2xl flex items-center justify-center shadow-[0_0_30px_rgba(255,122,0,0.3)]">
            <BrainCircuit className="w-10 h-10 text-[#FF7A00]" />
            <div className="absolute inset-0 bg-[#FF7A00]/20 animate-ping rounded-2xl" />
        </div>
    </div>
);

const XRayVisual = () => (
    <div className="relative w-full flex-1 min-h-[220px] bg-[#0a0f18] rounded-2xl border border-white/10 mb-6 flex flex-col items-center justify-center overflow-hidden shadow-inner">
        {/* Medical UI Headers */}
        <div className="absolute top-0 inset-x-0 h-6 bg-white/5 border-b border-white/10 flex items-center px-3 gap-1.5 z-20">
            <div className="w-2 h-2 rounded-full bg-red-500/50" />
            <div className="w-2 h-2 rounded-full bg-yellow-500/50" />
            <div className="w-2 h-2 rounded-full bg-green-500/50" />
            <span className="text-[8px] text-gray-500 ml-2 uppercase tracking-widest font-mono">Scan_0492.dcm</span>
        </div>

        {/* Wireframe Body / Organ Mockup */}
        <div className="relative w-32 h-36 border border-[#4D4DFF]/30 rounded-[40px] mt-6 flex items-center justify-center opacity-70">
            <ActivitySquare className="w-16 h-16 text-[#4D4DFF]/30" />

            {/* Animated Scanning Laser Box */}
            <motion.div
                animate={{ top: ["0%", "75%", "0%"] }}
                transition={{ repeat: Infinity, duration: 3, ease: "easeInOut" }}
                className="absolute left-0 right-0 h-10 border border-[#FF7A00] bg-[#FF7A00]/10 rounded-lg overflow-hidden"
            >
                <div className="absolute bottom-0 inset-x-0 h-0.5 bg-[#FF7A00] shadow-[0_0_10px_#FF7A00]" />
            </motion.div>
        </div>
    </div>
);

const EHRVisual = () => (
    <div className="relative w-full flex-1 min-h-[220px] bg-gradient-to-tr from-white/5 to-transparent rounded-2xl border border-white/10 mb-6 flex items-center justify-center overflow-hidden">
        {/* Isometric Sync Pipeline */}
        <div className="flex gap-4 items-center">
            <motion.div animate={{ y: [-5, 5, -5] }} transition={{ repeat: Infinity, duration: 3, ease: "easeInOut" }} className="w-16 h-24 bg-white/10 backdrop-blur-md border border-white/20 rounded-xl relative shadow-2xl flex flex-col items-center justify-center gap-2">
                <Database className="w-5 h-5 text-gray-400" />
                <div className="w-8 h-1 bg-white/20 rounded-full" />
                <div className="w-6 h-1 bg-white/20 rounded-full" />
            </motion.div>

            {/* Sync Arrows */}
            <div className="flex flex-col gap-2">
                <motion.div animate={{ x: [0, 8, 0] }} transition={{ repeat: Infinity, duration: 1.5 }} className="w-10 h-0.5 bg-gradient-to-r from-transparent to-[#4D4DFF] relative">
                    <div className="absolute right-0 -top-1 w-2 h-2 border-t-2 border-r-2 border-[#4D4DFF] rotate-45" />
                </motion.div>
                <motion.div animate={{ x: [0, -8, 0] }} transition={{ repeat: Infinity, duration: 1.5, delay: 0.75 }} className="w-10 h-0.5 bg-gradient-to-l from-transparent to-[#FF7A00] relative">
                    <div className="absolute left-0 -top-1 w-2 h-2 border-b-2 border-l-2 border-[#FF7A00] rotate-45" />
                </motion.div>
            </div>

            <motion.div animate={{ y: [5, -5, 5] }} transition={{ repeat: Infinity, duration: 3, ease: "easeInOut" }} className="w-16 h-24 bg-white/10 backdrop-blur-md border border-[#FF7A00]/30 rounded-xl relative shadow-2xl flex flex-col items-center justify-center gap-2">
                <div className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-[#FF7A00] rounded-full flex items-center justify-center shadow-[0_0_10px_#FF7A00]">
                    <CheckCircle2 className="w-3.5 h-3.5 text-black" />
                </div>
                <Database className="w-5 h-5 text-[#FF7A00]" />
                <div className="w-8 h-1 bg-[#FF7A00]/50 rounded-full" />
            </motion.div>
        </div>
    </div>
);

const VoiceVisual = () => (
    <div className="relative w-full flex-1 min-h-[220px] bg-gradient-to-b from-black to-[#1a1a3a] rounded-2xl border border-white/10 mb-6 flex items-center justify-center overflow-hidden">
        {/* Central Orb */}
        <div className="relative flex items-center justify-center">
            <motion.div animate={{ scale: [1, 1.3, 1] }} transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }} className="absolute w-28 h-28 bg-gradient-to-tr from-[#FF7A00] to-[#4D4DFF] rounded-full blur-2xl opacity-40" />
            <div className="relative z-10 w-16 h-16 bg-black border border-white/20 rounded-full flex items-center justify-center shadow-xl">
                <MessageSquare className="w-6 h-6 text-white" />
            </div>

            {/* Spinning Equalizer Rings */}
            <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 10, ease: "linear" }} className="absolute w-36 h-36 border border-dashed border-[#4D4DFF]/50 rounded-full" />
            <motion.div animate={{ rotate: -360 }} transition={{ repeat: Infinity, duration: 15, ease: "linear" }} className="absolute w-44 h-44 border border-dotted border-[#FF7A00]/50 rounded-full" />
        </div>
    </div>
);

const ROADMAP = [
    {
        title: "Symptom Checker", status: "Shipped", desc: "The core AI Council debate engine.", active: true,
        icon: BrainCircuit, cardSubtitle: "Current Release", cardTitle: "AI Council Engine", cardDesc: "Three specialized models debating differential diagnoses in real-time.",
        Visual: CouncilVisual
    },
    {
        title: "Radiology Beta", status: "Beta", desc: "Computer vision for medical imaging.", active: true,
        icon: ActivitySquare, cardSubtitle: "Beta Feature Spotlight", cardTitle: "X-Ray Analysis", cardDesc: "Upload your DICOM or JPEG radiology scans for a multi-model read.",
        Visual: XRayVisual
    },
    {
        title: "EHR Integration", status: "Upcoming", desc: "Seamless sync with major health records.", active: false,
        icon: Database, cardSubtitle: "Coming Soon", cardTitle: "EHR Syncing", cardDesc: "Connect Curezy directly with Epic and Cerner for immediate patient history.",
        Visual: EHRVisual
    },
    {
        title: "Voice Intake", status: "Upcoming", desc: "Talk directly to your AI physician.", active: false,
        icon: MessageSquare, cardSubtitle: "In Development", cardTitle: "Voice AI Agents", cardDesc: "Voice-first symptom recording with conversational AI follow-up.",
        Visual: VoiceVisual
    }
]

export default function AnimatedRoadmap() {
    const containerRef = useRef(null);
    const [activeIndex, setActiveIndex] = useState(0);

    const { scrollYProgress } = useScroll({
        target: containerRef,
        offset: ["start start", "end end"]
    });

    useMotionValueEvent(scrollYProgress, "change", (latest) => {
        // Divide the 0-1 progress into 4 segments (0.00-0.25, 0.25-0.50, 0.50-0.75, 0.75-1.00)
        let index = Math.floor(latest * ROADMAP.length);
        if (index >= ROADMAP.length) index = ROADMAP.length - 1; // clamp
        setActiveIndex(index);
    });

    return (
        <section id="roadmap" ref={containerRef} className="relative h-[400vh]">
            <div className="sticky top-0 h-screen w-full flex items-center justify-center overflow-hidden">
                <div className="w-full max-w-6xl mx-auto px-6 md:px-12 grid grid-cols-1 md:grid-cols-2 gap-12 md:gap-20 items-center">

                    {/* Left Side: Headlines and List */}
                    <div>
                        <h3 className="text-[#FF7A00] font-bold text-xl mb-4">Roadmap</h3>
                        <h2 className="text-4xl md:text-5xl font-bold tracking-tight mb-6 leading-tight text-white">
                            The tool that evolves<br />and grows with you.
                        </h2>
                        <p className="text-gray-400 text-lg mb-12">
                            Curezy AI is continually learning. Here are features actively in development for future versions:
                        </p>

                        <div className="space-y-6 relative border-l-2 border-white/10 ml-3 pl-8">
                            {ROADMAP.map((item, i) => (
                                <div
                                    key={i}
                                    className={`relative transition-all duration-500 ease-in-out ${i === activeIndex
                                        ? 'opacity-100 scale-105 translate-x-2'
                                        : i < activeIndex
                                            ? 'opacity-40 scale-100'
                                            : 'opacity-20 scale-95'
                                        }`}
                                >
                                    {/* Timeline Dot */}
                                    <div className={`absolute -left-[45px] top-1.5 w-6 h-6 rounded-full flex items-center justify-center transition-all duration-500 ${i === activeIndex
                                        ? 'bg-[#4D4DFF] shadow-[0_0_15px_rgba(77,77,255,0.6)]'
                                        : i < activeIndex
                                            ? 'bg-[#4D4DFF]/50 border border-[#4D4DFF]'
                                            : 'bg-black border-2 border-white/20'
                                        }`}>
                                        {i <= activeIndex && item.active ? (
                                            <CheckCircle2 className="text-white w-4 h-4" />
                                        ) : (
                                            <div className="w-2 h-2 rounded-full bg-white/40" />
                                        )}
                                    </div>

                                    <div>
                                        <div className="flex items-center gap-3 mb-1">
                                            <h4 className={`text-xl font-bold transition-colors duration-500 ${i === activeIndex ? 'text-white' : 'text-gray-400'
                                                }`}>
                                                {item.title}
                                            </h4>
                                            <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full transition-colors duration-500 ${i === activeIndex && item.active ? 'bg-[#4D4DFF]/20 text-[#4D4DFF] border border-[#4D4DFF]/30'
                                                : item.active ? 'bg-white/10 text-white'
                                                    : 'bg-transparent border border-gray-600 text-gray-600'
                                                }`}>
                                                {item.status}
                                            </span>
                                        </div>
                                        <p className={`text-sm transition-colors duration-500 ${i === activeIndex ? 'text-gray-300' : 'text-gray-500'
                                            }`}>
                                            {item.desc}
                                        </p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Right Side: Visual Card Overlay */}
                    <div className="flex items-center justify-center relative w-full aspect-square md:aspect-auto md:h-[500px]">
                        <AnimatePresence mode="wait">
                            <motion.div
                                key={activeIndex}
                                initial={{ opacity: 0, scale: 0.9, y: 20 }}
                                animate={{ opacity: 1, scale: 1, y: 0 }}
                                exit={{ opacity: 0, scale: 0.95, y: -20 }}
                                transition={{ duration: 0.5, ease: "easeOut" }}
                                className="absolute w-full max-w-sm aspect-square md:aspect-[4/5] bg-gradient-to-br from-[#1a1a3a] to-black border border-white/10 rounded-3xl p-8 overflow-hidden shadow-2xl flex flex-col justify-between"
                            >
                                <div className="absolute -inset-10 bg-[#FF7A00]/10 blur-3xl rounded-full opacity-50 mix-blend-screen transition-all duration-1000" />

                                <div className="relative z-10 flex flex-col justify-between h-full">
                                    <div className="w-full mt-2">
                                        {React.createElement(ROADMAP[activeIndex].Visual)}
                                    </div>

                                    <div className="mt-auto">
                                        <p className="text-xs font-bold text-[#FF7A00] tracking-wider uppercase mb-2">
                                            {ROADMAP[activeIndex].cardSubtitle}
                                        </p>
                                        <h3 className="text-2xl font-bold text-white mb-2">
                                            {ROADMAP[activeIndex].cardTitle}
                                        </h3>
                                        <p className="text-sm text-gray-400 leading-relaxed">
                                            {ROADMAP[activeIndex].cardDesc}
                                        </p>
                                    </div>
                                </div>

                                {/* Aesthetic Grid Background for Card */}
                                <div className="absolute inset-0 pointer-events-none opacity-20"
                                    style={{ backgroundImage: 'linear-gradient(to right, #404040 1px, transparent 1px), linear-gradient(to bottom, #404040 1px, transparent 1px)', backgroundSize: '40px 40px' }}
                                />
                            </motion.div>
                        </AnimatePresence>
                    </div>

                </div>
            </div>
        </section>
    );
}
