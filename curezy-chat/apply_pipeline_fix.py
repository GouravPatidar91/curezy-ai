import os
import re

filepath = r"e:\Curezy-ai\curezy-chat\src\pages\Landing.jsx"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update PipelineVisuals function
pipeline_visuals_new = """function PipelineVisuals({ pipelineScroll }) {
    const [activeStep, setActiveStep] = useState(0)

    useEffect(() => {
        return pipelineScroll.on("change", (latest) => {
            if (latest < 0.33) setActiveStep(0)
            else if (latest >= 0.33 && latest < 0.66) setActiveStep(1)
            else setActiveStep(2)
        })
    }, [pipelineScroll])

    return (
        <div className="relative w-full h-full flex items-center justify-center">
            <AnimatePresence>
                {activeStep === 0 && (
                    <motion.div
                        key="step0"
                        initial={{ opacity: 0, scale: 0.95, y: 15 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 1.05, y: -15 }}
                        transition={{ duration: 0.6, ease: 'easeOut' }}
                        className="absolute inset-0 flex flex-col items-center justify-center gap-6"
                    >
                        <div className="w-16 h-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center">
                            <ActivitySquare className="text-[#FF7A00] w-8 h-8 animate-pulse" />
                        </div>
                        <div className="space-y-3 w-full max-w-sm bg-[#050510] p-6 rounded-2xl border border-white/5">
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
                        className="absolute inset-0 flex flex-col items-center justify-center"
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
                        className="absolute inset-0 flex flex-col items-center justify-center"
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
        </div>
    )
}"""
start_idx = content.find("function PipelineVisuals({ pipelineScroll }) {")
end_idx = content.find("export default function Landing() {")
if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + pipeline_visuals_new + "\n\n" + content[end_idx:]

# 2. Update useScroll inside Landing
content = re.sub(
    r'const \{ scrollYProgress: pipelineScroll \} = useScroll\(\{.*?\}\)',
    r'const { scrollYProgress: pipelineScroll } = useScroll({ target: containerRef, offset: ["start start", "end end"] })',
    content,
    flags=re.DOTALL
)

# 3. Update the Pipeline Section block
pipeline_section_new = """            {/* 2. AI Pipeline Section (Scroll Sticky) */}
            <section id="pipeline" className="relative z-20 max-w-7xl mx-auto px-6 md:px-12 py-32" >
                <div className="mb-16">
                    <h3 className="text-[#FF7A00] font-bold text-lg mb-2">AI Pipeline</h3>
                    <h2 className="text-4xl md:text-5xl font-bold tracking-tight">Diagnostics,<br />end-to-end.</h2>
                </div>

                <div ref={containerRef} className="relative h-[250vh]">
                    <div className="sticky top-32 grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-24 h-[600px] overflow-visible">
                        {/* Left: Scroll Progress Text */}
                        <div className="lg:col-span-5 relative flex flex-col justify-center h-full pt-10 pb-16 outline-none border-none">
                            
                            {/* The physical track line (inactive) */}
                            <div className="absolute left-[20px] top-[10%] bottom-[10%] w-0.5 bg-white/10" />
                            
                            {/* The active fill line */}
                            <motion.div
                                className="absolute left-[20px] top-[10%] w-0.5 bg-gradient-to-b from-[#FF7A00] to-[rgba(255,122,0,0.4)] to-transparent origin-top"
                                style={{ height: useTransform(pipelineScroll, [0, 1], ['0%', '80%']) }}
                            />

                            {/* The traveling star tip */}
                            <motion.div 
                                className="absolute left-[10.5px] w-5 h-5 border rounded-sm rotate-45 flex items-center justify-center bg-[#050510] border-[#FF7A00] shadow-[0_0_10px_rgba(255,122,0,0.5)] z-10"
                                style={{ 
                                    top: useTransform(pipelineScroll, [0, 1], ['10%', '90%'])
                                }}
                            >
                                <div className="w-1.5 h-1.5 bg-white rounded-full" />
                            </motion.div>

                            <div className="space-y-20 pl-16">
                                {PIPELINE_STEPS.map((step, idx) => {
                                    // Define active bounds for this step to light up the text
                                    const stepProgress = useTransform(pipelineScroll, 
                                        [Math.max(0, (idx - 0.5) / 3), idx / 3, Math.min(1, (idx + 0.5) / 3)], 
                                        [0.3, 1, 0.3]
                                    )
                                    
                                    return (
                                        <motion.div
                                            key={idx}
                                            className="relative"
                                            style={{ opacity: stepProgress }}
                                        >
                                            <motion.h4 
                                                className="text-2xl font-bold mb-3 transition-colors duration-300"
                                                style={{ color: useTransform(stepProgress, [0.3, 1], ['#6b7280', '#ffffff']) }}
                                            >
                                                {step.title}
                                            </motion.h4>
                                            <p className="text-gray-400 text-lg leading-relaxed">{step.desc}</p>
                                        </motion.div>
                                    )
                                })}
                            </div>
                        </div>

                        {/* Right: Sticky Visual Preview */}
                        <div className="lg:col-span-7 relative h-full hidden lg:block">
                            <div className="w-full h-full rounded-3xl border border-white/10 bg-[#0a0a15] overflow-hidden shadow-2xl flex flex-col">
                                {/* Browser Header Fake */}
                                <div className="h-12 border-b border-white/5 bg-white/5 flex items-center px-4 gap-4 z-10 shrink-0">
                                    <div className="flex gap-2">
                                        <div className="w-3 h-3 rounded-full bg-white/20" />
                                        <div className="w-3 h-3 rounded-full bg-white/20" />
                                        <div className="w-3 h-3 rounded-full bg-white/20" />
                                    </div>
                                    <div className="flex-1 flex justify-center">
                                        <div className="w-1/2 h-6 rounded-md bg-black/50 border border-white/5 flex items-center justify-center opacity-50">
                                            <p className="text-[10px] text-gray-500">app.curezy.ai / diagnosis</p>
                                        </div>
                                    </div>
                                </div>

                                {/* Editor Body */}
                                <div className="flex-1 p-8 relative bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] bg-opacity-5 overflow-hidden">
                                    <PipelineVisuals pipelineScroll={pipelineScroll} />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>"""

sec_start = content.find("{/* 2. AI Pipeline Section (Scroll Sticky) */}")
sec_end = content.find("{/* 3. Features Section */}")
if sec_start != -1 and sec_end != -1:
    content = content[:sec_start] + pipeline_section_new + "\n\n            " + content[sec_end:]

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Landing.jsx updated successfully!")
