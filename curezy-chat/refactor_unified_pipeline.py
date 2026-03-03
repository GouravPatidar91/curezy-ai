import os

filepath = r"e:\Curezy-ai\curezy-chat\src\pages\Landing.jsx"
unified_path = r"e:\Curezy-ai\curezy-chat\src\components\UnifiedPipeline.jsx"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# EXTRACT PIPELINE_STEPS and PipelineVisuals
steps_start = content.find("const PIPELINE_STEPS = [")
steps_end = content.find("const roadmapData = [") # usually after steps

if steps_start == -1 or steps_end == -1:
    print("Could not find dependencies in Landing.jsx!")
    exit(1)

extracted_deps = content[steps_start:steps_end].strip()
if extracted_deps.endswith("}") == False and "function PipelineVisuals({ activeStep }) {" in extracted_deps:
    pass # we have the whole block

# Clean up any PromptTransition logic that might be above it
prompt_trans_start = content.find("const FULL_PROMPT =")
if prompt_trans_start != -1 and prompt_trans_start < steps_start:
    # Delete PromptTransition
    prompt_trans_end = content.find("export default function Landing() {")
    content = content[:prompt_trans_start] + content[prompt_trans_end:]


unified_jsx = """
import React, { useRef, useState } from 'react';
import { motion, useScroll, useTransform, AnimatePresence, useMotionValueEvent } from 'framer-motion';
import { Sparkles, Loader2, ActivitySquare, Database, MessageSquare, LineChart, FileText, CheckCircle2, FlaskConical, Stethoscope } from 'lucide-react';

const FULL_PROMPT = "32yo female, severe headache, nausea, and sensitivity to light for 3 days.";

""" + extracted_deps + """

export default function UnifiedPipeline() {
    const containerRef = useRef(null);
    const { scrollYProgress } = useScroll({ target: containerRef, offset: ["start start", "end end"] });

    // PHASE 1 (0.00 - 0.20): Mockup Enter
    const mockupScale = useTransform(scrollYProgress, [0, 0.15], [0.8, 1]);
    const mockupOpacity = useTransform(scrollYProgress, [0, 0.15], [0, 1]);
    const mockupY = useTransform(scrollYProgress, [0, 0.15], [100, 0]);

    // PHASE 2 (0.20 - 0.40): Typing
    const typeLength = useTransform(scrollYProgress, [0.15, 0.35], [0, FULL_PROMPT.length]);
    const [typedStr, setTypedStr] = useState("");
    useMotionValueEvent(typeLength, "change", (latest) => setTypedStr(FULL_PROMPT.slice(0, Math.floor(latest))));
    const generatingOpacity = useTransform(scrollYProgress, [0.35, 0.4], [0, 1]);
    const generatingScale = useTransform(scrollYProgress, [0.35, 0.4], [0.9, 1]);

    // PHASE 3 (0.45 - 0.55): THE SHIFT
    // The mockup right-aligns and shrinks to make room on the left
    const mockupWidth = useTransform(scrollYProgress, [0.45, 0.55], ["100%", "58.333%"]);
    
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
        if (latest < 0.73) setActiveStep(0);
        else if (latest < 0.86) setActiveStep(1);
        else setActiveStep(2);
    });
    
    const pipelineFill = useTransform(scrollYProgress, [0.6, 1], ["0%", "80%"]);
    const starTop = useTransform(scrollYProgress, [0.6, 1], ["10%", "90%"]);

    return (
        <section ref={containerRef} id="pipeline" className="relative h-[500vh] w-full">
            <div className="sticky top-0 h-screen w-full flex items-center justify-center overflow-hidden">
                <div className="w-full max-w-7xl mx-auto px-6 h-full flex items-center justify-end relative">
                    
                    {/* Left Column (Fades in during Phase 3) */}
                    <motion.div 
                        style={{ opacity: leftPanelOpacity, x: leftPanelX }}
                        className="absolute left-6 w-[41.666%] h-[600px] flex flex-col justify-center pointer-events-none z-0"
                    >
                         <div className="mb-12">
                            <h3 className="text-[#FF7A00] font-bold text-lg mb-2">AI Pipeline</h3>
                            <h2 className="text-4xl lg:text-5xl font-bold tracking-tight text-white leading-tight">Diagnostics,<br />end-to-end.</h2>
                        </div>
                        
                        <div className="relative pl-12 h-full py-8">
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

                            <div className="space-y-16">
                                {PIPELINE_STEPS.map((step, idx) => {
                                    const stepOp = useTransform(scrollYProgress, 
                                        [0.6 + (idx - 0.5)*0.13, 0.6 + idx*0.13, 0.6 + (idx + 0.5)*0.13], 
                                        [0.3, 1, 0.3]
                                    );
                                    const stepColor = useTransform(stepOp, [0.3, 1], ['#6b7280', '#ffffff']);
                                    return (
                                        <motion.div key={idx} style={{ opacity: stepOp }} className="relative">
                                            <motion.h4 style={{ color: stepColor }} className="text-2xl font-bold mb-3 transition-colors duration-300">
                                                {step.title}
                                            </motion.h4>
                                            <p className="text-gray-400 text-lg leading-relaxed">{step.desc}</p>
                                        </motion.div>
                                    )
                                })}
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
                        className="h-[600px] w-full bg-[#0a0a15] rounded-[2rem] border border-white/10 shadow-[0_0_100px_rgba(77,77,255,0.1)] flex flex-col overflow-hidden relative z-10"
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
                                  style={{ opacity: intakeContentOpacity, pointerEvents: useTransform(intakeContentOpacity, v => v > 0 ? "auto" : "none") }}
                                  className="absolute inset-0 flex flex-col items-center justify-center p-8 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] bg-opacity-[0.02]"
                              >
                                  <div className="w-full max-w-3xl bg-[#050510] border border-white/10 rounded-3xl p-8 lg:p-12 shadow-2xl relative min-h-[220px] flex flex-col justify-center">
                                      <div className="absolute -inset-0.5 bg-gradient-to-r from-[#FF7A00]/20 to-[#4D4DFF]/20 blur-xl opacity-50 rounded-3xl -z-10" />
                                      <h3 className="text-[#4D4DFF] font-black text-sm uppercase tracking-widest mb-6 flex items-center gap-2">
                                          <Sparkles className="w-4 h-4" /> Intake Session
                                      </h3>
                                      <p className="text-2xl md:text-3xl font-semibold text-white leading-normal">
                                          {typedStr}
                                          <motion.span 
                                            animate={{ opacity: [1, 0] }}
                                            transition={{ repeat: Infinity, duration: 0.8, ease: "linear" }}
                                            className="inline-block w-1.5 h-[1em] bg-[#FF7A00] ml-1 align-middle" 
                                          />
                                      </p>
                                      
                                      <motion.div 
                                        style={{ opacity: generatingOpacity, scale: generatingScale }}
                                        className="absolute bottom-[-24px] right-8"
                                      >
                                          <div className="px-8 py-4 bg-white text-black font-black rounded-xl shadow-[0_20px_40px_rgba(255,255,255,0.2)] flex items-center gap-3 text-lg">
                                              Running Analysis <Loader2 className="w-6 h-6 animate-spin" />
                                          </div>
                                      </motion.div>
                                  </div>
                              </motion.div>

                              {/* 2. Pipeline Visuals */}
                              <motion.div 
                                  style={{ opacity: pipelineVisualsOpacity, pointerEvents: useTransform(pipelineVisualsOpacity, v => v > 0 ? "auto" : "none") }}
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
"""

os.makedirs(os.path.dirname(unified_path), exist_ok=True)
with open(unified_path, 'w', encoding='utf-8') as f:
    f.write(unified_jsx)

# NOW REMOVE THE OLD PIPELINE AND PROMPT TRANSITION FROM Landing.jsx
import_statement = "import UnifiedPipeline from '../components/UnifiedPipeline';\n"
if "import UnifiedPipeline" not in content:
    idx = content.find("import {")
    content = content[:idx] + import_statement + content[idx:]

# Find where hero section ends
pipeline_start = content.find("{/* 2. AI Pipeline Section (Scroll Sticky) */}")
if pipeline_start == -1: # fallback
    pipeline_start = content.find("{/* Scroll Mockup Transition */}")

pipeline_end = content.find("{/* 3. Features Grid")

if pipeline_start != -1 and pipeline_end != -1:
    clean_landing = content[:pipeline_start] + "            {/* Unified AI Pipeline (Morphing) */}\n            <UnifiedPipeline />\n\n            " + content[pipeline_end:]
    
    # Strip the leftover PipelineVisuals and PIPELINE_STEPS from Landing
    import re
    # Remove FULL_PROMPT block
    clean_landing = re.sub(r'const FULL_PROMPT =.*?;', '', clean_landing, flags=re.DOTALL)
    # Remove PromptTransition func block
    clean_landing = re.sub(r'function PromptTransition\(\) \{.*?\n}\n', '', clean_landing, flags=re.DOTALL)
    # Remove PIPELINE_STEPS
    clean_landing = re.sub(r'const PIPELINE_STEPS = \[.*?}];', '', clean_landing, flags=re.DOTALL)
    # Remove PipelineVisuals func
    clean_landing = re.sub(r'function PipelineVisuals\(\{.*?\}\) \{.*?\n}\n', '', clean_landing, flags=re.DOTALL)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(clean_landing)
    print("Successfully refactored into UnifiedPipeline!")
else:
    print("Could not locate pipeline markers in Landing.jsx")

