import React, { useRef, useState, useEffect } from 'react';
import { motion, useScroll, useTransform, AnimatePresence, useMotionValueEvent } from 'framer-motion';
import { Sparkles, Loader2, ActivitySquare, Database, MessageSquare, LineChart, FileText, CheckCircle2, FlaskConical, Stethoscope } from 'lucide-react';

const FULL_PROMPT = "32yo female, severe headache, nausea, and sensitivity to light for 3 days.";

const PIPELINE_STEPS = [
    { title: "Analyzing symptoms...", desc: "Curezy AI breaks down your chief complaints, history, and timeline." },
    { title: "Cross-referencing...", desc: "Next, it matches symptoms against vast medical databases and journals." },
    { title: "Debate, iterate, diagnose!", desc: "The AI Council debates to bring out the most accurate clinical assessment." }
]

function PipelineVisuals({ activeStep }) {
    return (
        <div className="relative w-full h-full flex items-center justify-center bg-[#0a0a15] overflow-hidden rounded-b-3xl">
            <AnimatePresence mode="popLayout">
                {activeStep === 0 && (
                    <motion.div
                        key="step0"
                        initial={{ opacity: 0, scale: 0.95, y: 15 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 1.05, y: -15 }}
                        transition={{ duration: 0.6, ease: 'easeOut' }}
                        className="absolute inset-0 flex flex-col items-center justify-center gap-6 z-10"
                    >
                        <div className="w-16 h-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center">
                            <ActivitySquare className="text-[#FF7A00] w-8 h-8 animate-pulse" />
                        </div>
                        <div className="space-y-3 w-full max-w-sm bg-[#050510] p-6 rounded-2xl border border-white/5 shadow-2xl">
                            <div className="h-4 w-3/4 bg-white/10 rounded overflow-hidden relative">
                                <motion.div className="h-full bg-gradient-to-r from-[#FF7A00]/50 to-transparent w-full"
                                    animate={{ x: ['-100%', '100%'] }} transition={{ repeat: Infinity, duration: 1.5, ease: "linear" }}
                                />
                            </div>
                            <div className="h-4 w-1/2 bg-white/10 rounded" />
                            <div className="h-4 w-5/6 bg-white/10 rounded" />
                        </div>
                    </motion.div>
                )}

                {activeStep === 1 && (
                    <motion.div
                        key="step1"
                        initial={{ opacity: 0, scale: 0.95, y: 15 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 1.05, y: -15 }}
                        transition={{ duration: 0.6, ease: 'easeOut' }}
                        className="absolute inset-0 flex flex-col items-center justify-center z-10"
                    >
                        <div className="relative w-40 h-40">
                            <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 20, ease: "linear" }} className="absolute inset-0 border border-dashed border-[#4D4DFF]/40 rounded-full" />
                            <motion.div animate={{ rotate: -360 }} transition={{ repeat: Infinity, duration: 15, ease: "linear" }} className="absolute inset-4 border border-[#4D4DFF]/20 rounded-full flex items-center justify-center">
                                <Database className="text-[#4D4DFF] w-12 h-12" />
                            </motion.div>
                            <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 20, ease: "linear" }} className="absolute inset-0 origin-center">
                                <div className="w-3 h-3 bg-white rounded-full absolute -top-1.5 left-1/2 shadow-[0_0_10px_#fff]" />
                            </motion.div>
                        </div>
                        <p className="mt-8 text-white/70 font-mono text-sm border-t border-white/10 pt-4 w-full text-center max-w-xs">querying specialized journals...</p>
                    </motion.div>
                )}

                {activeStep === 2 && (
                    <motion.div
                        key="step2"
                        initial={{ opacity: 0, scale: 0.95, y: 15 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 1.05, y: -15 }}
                        transition={{ duration: 0.6, ease: 'easeOut' }}
                        className="absolute inset-0 flex flex-col items-center justify-center z-10"
                    >
                        <div className="flex flex-col items-center justify-center relative">
                            <motion.div
                                initial={{ scale: 0.9 }}
                                animate={{ scale: [0.9, 1, 0.9] }}
                                transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
                                className="relative w-48 h-48 mb-6"
                            >
                                <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-[#FF7A00] to-[#4D4DFF] shadow-[0_0_50px_rgba(77,77,255,0.4)] blur-md" />
                                <div className="absolute inset-1 rounded-full bg-[#050510] flex items-center justify-center z-10">
                                    <MessageSquare className="text-white w-12 h-12 opacity-80" />
                                </div>
                            </motion.div>
                            <h3 className="text-3xl font-black text-center text-white">Curezy Council</h3>
                            <p className="text-center text-sm text-[#FF7A00] font-bold mt-2 uppercase tracking-widest">Diagnosis Ready</p>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
            <div className="absolute inset-0 z-0 bg-gradient-to-b from-transparent to-[#050510]/50 pointer-events-none" />
        </div>
    )
}

export default function UnifiedPipeline() {
    const containerRef = useRef(null);
    const { scrollYProgress } = useScroll({ target: containerRef, offset: ["start start", "end end"] });

    const [isMobile, setIsMobile] = useState(false);
    useEffect(() => {
        const checkMobile = () => setIsMobile(window.innerWidth < 1024);
        checkMobile();
        window.addEventListener('resize', checkMobile);
        return () => window.removeEventListener('resize', checkMobile);
    }, []);

    // PHASE 1 (0.00 - 0.20): Mockup Enter
    const mockupScale = useTransform(scrollYProgress, [0, 0.15], [0.8, 1]);
    const mockupOpacity = useTransform(scrollYProgress, [0, 0.15], [0, 1]);
    const mockupY = useTransform(scrollYProgress, [0, 0.15, 0.45, 0.55], [100, 0, 0, isMobile ? 120 : 0]);

    // PHASE 2 (0.20 - 0.40): Typing
    const typeLength = useTransform(scrollYProgress, [0.15, 0.35], [0, FULL_PROMPT.length]);
    const [typedStr, setTypedStr] = useState("");
    useMotionValueEvent(typeLength, "change", (latest) => setTypedStr(FULL_PROMPT.slice(0, Math.floor(latest))));
    const generatingOpacity = useTransform(scrollYProgress, [0.35, 0.4], [0, 1]);
    const generatingScale = useTransform(scrollYProgress, [0.35, 0.4], [0.9, 1]);

    // PHASE 3 (0.45 - 0.55): THE SHIFT -> Shrink width and right-align!
    // We animate from exactly matching max-w-5xl (which is 1024px) down to 58.333% (7/12 grid cols)
    const mockupWidth = useTransform(scrollYProgress, [0.45, 0.55], ["100%", isMobile ? "92%" : "58.333%"]);

    // Left panel fades in and slides 
    const leftPanelOpacity = useTransform(scrollYProgress, [0.5, 0.6], [0, 1]);
    const leftPanelX = useTransform(scrollYProgress, [0.45, 0.55], [-50, 0]);

    // Intake Content fades out
    const intakeContentOpacity = useTransform(scrollYProgress, [0.45, 0.5], [1, 0]);

    // Pipeline Visuals fades in
    const pipelineVisualsOpacity = useTransform(scrollYProgress, [0.5, 0.55], [0, 1]);

    // PHASE 4 (0.60 - 1.00): 3 Steps Progress
    const [activeStep, setActiveStep] = useState(0);
    useMotionValueEvent(scrollYProgress, "change", (latest) => {
        if (latest < 0.7) setActiveStep(0);
        else if (latest < 0.85) setActiveStep(1);
        else setActiveStep(2);
    });

    const pipelineFill = useTransform(scrollYProgress, [0.6, 1], ["0%", "80%"]);
    const starTop = useTransform(scrollYProgress, [0.6, 1], ["10%", "90%"]);

    // Pipeline Step Opacities (Defined at top level to avoid Rule of Hooks violation)
    const step0Op = useTransform(scrollYProgress, [0.52, 0.62, 0.72], [0.3, 1, 0.3]);
    const step1Op = useTransform(scrollYProgress, [0.65, 0.77, 0.90], [0.3, 1, 0.3]);
    const step2Op = useTransform(scrollYProgress, [0.82, 0.92, 1.05], [0.3, 1, 0.3]);
    const stepOps = [step0Op, step1Op, step2Op];

    const intakePointerEvents = useTransform(intakeContentOpacity, v => v > 0 ? "auto" : "none");
    const visualsPointerEvents = useTransform(pipelineVisualsOpacity, v => v > 0 ? "auto" : "none");

    // Pipeline Step Colors (Defined at top level to avoid Rule of Hooks violation)
    const step0Color = useTransform(step0Op, [0.3, 1], ['#6b7280', '#ffffff']);
    const step1Color = useTransform(step1Op, [0.3, 1], ['#6b7280', '#ffffff']);
    const step2Color = useTransform(step2Op, [0.3, 1], ['#6b7280', '#ffffff']);
    const stepColors = [step0Color, step1Color, step2Color];

    return (
        <section ref={containerRef} id="pipeline" className="relative h-[600vh] w-full">
            <div className="sticky top-0 h-screen w-full flex items-center justify-center overflow-hidden pt-20">
                <div className="w-full max-w-7xl mx-auto px-6 h-full flex items-center justify-end relative">

                    {/* Left Column (Fades in during Phase 3) */}
                    <motion.div
                        style={{ opacity: leftPanelOpacity, x: isMobile ? 0 : leftPanelX }}
                        className={`absolute flex flex-col justify-center pointer-events-none z-0 
                            ${isMobile
                                ? 'top-12 left-0 w-full px-6 h-auto text-center items-center'
                                : 'left-6 w-[41.666%] h-[520px] items-start'}`}
                    >
                        <div className={isMobile ? "mb-4" : "mb-8"}>
                            <h3 className="text-[#FF7A00] font-bold text-sm lg:text-lg mb-1 lg:mb-2 text-center lg:text-left">AI Pipeline</h3>
                            <h2 className="text-2xl lg:text-5xl font-bold tracking-tight text-white leading-tight text-center lg:text-left">Diagnostics,<br className="hidden lg:block" /> {isMobile && " "} end-to-end.</h2>
                        </div>

                        <div className={`relative h-full ${isMobile ? 'py-4 px-2' : 'pl-12 py-8'}`}>
                            {!isMobile && (
                                <>
                                    <div className="absolute left-[3px] top-[10%] bottom-[10%] w-0.5 bg-white/10" />
                                    <motion.div
                                        className="absolute left-[3px] top-[10%] w-0.5 bg-gradient-to-b from-[#FF7A00] to-[rgba(255,122,0,0.4)] to-transparent origin-top"
                                        style={{ height: pipelineFill }}
                                    />
                                    <motion.div
                                        className="absolute left-[-6px] w-5 h-5 border rounded-sm rotate-45 flex items-center justify-center bg-[#050510] border-[#FF7A00] shadow-[0_0_10px_rgba(255,122,0,0.5)] z-10"
                                        style={{ top: starTop }}
                                    >
                                        <div className="w-1.5 h-1.5 bg-white rounded-full" />
                                    </motion.div>
                                </>
                            )}

                            <div className={isMobile ? "relative h-32 w-full" : "space-y-8"}>
                                {isMobile ? (
                                    <div className="flex flex-col items-center justify-center w-full">
                                        <AnimatePresence mode="wait">
                                            <motion.div
                                                key={activeStep}
                                                initial={{ opacity: 0, y: 10 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                exit={{ opacity: 0, y: -10 }}
                                                transition={{ duration: 0.4 }}
                                                className="text-center px-4"
                                            >
                                                <h4 className="text-xl font-bold text-white mb-2">
                                                    {PIPELINE_STEPS[activeStep].title}
                                                </h4>
                                                <p className="text-gray-400 text-sm leading-relaxed max-w-xs mx-auto">
                                                    {PIPELINE_STEPS[activeStep].desc}
                                                </p>
                                            </motion.div>
                                        </AnimatePresence>
                                    </div>
                                ) : (
                                    PIPELINE_STEPS.map((step, idx) => {
                                        const stepOp = stepOps[idx];
                                        const stepColor = stepColors[idx];

                                        return (
                                            <motion.div key={idx} style={{ opacity: stepOp }} className="relative">
                                                <motion.h4 style={{ color: stepColor }} className="text-2xl font-bold mb-3 transition-colors duration-300">
                                                    {step.title}
                                                </motion.h4>
                                                <p className="text-gray-400 text-lg leading-relaxed">{step.desc}</p>
                                            </motion.div>
                                        )
                                    })
                                )}
                            </div>
                        </div>
                    </motion.div>

                    {/* Morphing Mockup */}
                    <motion.div
                        style={{
                            width: mockupWidth,
                            scale: mockupScale,
                            opacity: mockupOpacity,
                            y: mockupY
                        }}
                        className={`${isMobile ? 'h-[400px]' : 'h-[520px]'} bg-[#0a0a15] rounded-[2rem] border border-white/10 shadow-[0_0_100px_rgba(77,77,255,0.1)] flex flex-col overflow-hidden relative z-10 mx-auto lg:mr-0`}
                    >
                        {/* Browser header */}
                        <div className="h-12 border-b border-white/5 bg-[#050510]/50 flex items-center px-4 gap-4 z-20 shrink-0 backdrop-blur-md">
                            <div className="flex gap-2">
                                <div className="w-3 h-3 rounded-full bg-white/20" />
                                <div className="w-3 h-3 rounded-full bg-white/20" />
                                <div className="w-3 h-3 rounded-full bg-white/20" />
                            </div>
                            <div className="flex-1 flex justify-center">
                                <div className="w-1/3 h-6 rounded-md bg-white/5 border border-white/5 flex items-center justify-center opacity-70">
                                    <p className="text-[10px] text-gray-400 font-mono">app.curezy.ai / runtime</p>
                                </div>
                            </div>
                        </div>

                        <div className="flex-1 relative">
                            {/* 1. Intake Session */}
                            <motion.div
                                style={{ opacity: intakeContentOpacity, pointerEvents: intakePointerEvents }}
                                className="absolute inset-0 flex flex-col items-center justify-center p-8 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] bg-opacity-[0.02]"
                            >
                                <div className="w-full max-w-3xl bg-[#050510] border border-white/10 rounded-3xl p-8 lg:p-12 shadow-2xl relative min-h-[220px] flex flex-col items-center text-center justify-center">
                                    <div className="absolute -inset-0.5 bg-gradient-to-r from-[#FF7A00]/20 to-[#4D4DFF]/20 blur-xl opacity-50 rounded-3xl -z-10" />
                                    <h3 className="text-[#4D4DFF] font-black text-sm uppercase tracking-widest mb-6 flex items-center justify-center gap-2 w-full">
                                        <Sparkles className="w-4 h-4" /> Intake Session
                                    </h3>
                                    <p className="text-2xl md:text-3xl font-semibold text-white leading-normal text-center">
                                        {typedStr}
                                        <motion.span
                                            animate={{ opacity: [1, 0] }}
                                            transition={{ repeat: Infinity, duration: 0.8, ease: "linear" }}
                                            className="inline-block w-1.5 h-[1em] bg-[#FF7A00] ml-1 align-middle"
                                        />
                                    </p>

                                    <motion.div
                                        style={{ opacity: generatingOpacity, scale: generatingScale }}
                                        className="absolute bottom-[-24px] xl:right-8 right-0 left-0 xl:left-auto flex justify-center xl:justify-end"
                                    >
                                        <div className="px-8 py-4 bg-white text-black font-black rounded-xl shadow-[0_20px_40px_rgba(255,255,255,0.2)] flex items-center gap-3 text-lg">
                                            Running Analysis <Loader2 className="w-6 h-6 animate-spin" />
                                        </div>
                                    </motion.div>
                                </div>
                            </motion.div>

                            {/* 2. Pipeline Visuals */}
                            <motion.div
                                style={{ opacity: pipelineVisualsOpacity, pointerEvents: visualsPointerEvents }}
                                className="absolute inset-0 bg-[#0a0a15]"
                            >
                                <PipelineVisuals activeStep={activeStep} />
                            </motion.div>
                        </div>
                    </motion.div>
                </div>
            </div>
        </section>
    );
}
