import os
import re

filepath = r"e:\Curezy-ai\curezy-chat\src\pages\Landing.jsx"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update imports
if 'useMotionValueEvent' not in content:
    content = content.replace("useTransform, AnimatePresence } from 'framer-motion'", "useTransform, AnimatePresence, useMotionValueEvent } from 'framer-motion'")

# 2. Add PromptTransition Component
component_code = """
const FULL_PROMPT = "32yo female, severe headache, nausea, and sensitivity to light for 3 days."

function PromptTransition() {
    const containerRef = useRef(null)
    const { scrollYProgress } = useScroll({ target: containerRef, offset: ["start end", "end start"] })
    
    // Scale up slightly and fade in from bottom
    const scale = useTransform(scrollYProgress, [0.1, 0.3], [0.8, 1]);
    const opacity = useTransform(scrollYProgress, [0.15, 0.35], [0, 1]);
    const y = useTransform(scrollYProgress, [0.1, 0.3], [100, 0]);
    
    // Typing length
    const typeLength = useTransform(scrollYProgress, [0.4, 0.65], [0, FULL_PROMPT.length]);
    const [typedStr, setTypedStr] = useState("");
    
    useMotionValueEvent(typeLength, "change", (latest) => {
        setTypedStr(FULL_PROMPT.slice(0, Math.floor(latest)));
    });

    // "Generating" status pops in
    const generatingOpacity = useTransform(scrollYProgress, [0.7, 0.75], [0, 1]);
    const generatingScale = useTransform(scrollYProgress, [0.7, 0.75], [0.9, 1]);

    return (
        <section ref={containerRef} className="relative h-[250vh]">
            <div className="sticky top-0 h-screen flex flex-col items-center justify-center pointer-events-none px-6 z-10 w-full max-w-7xl mx-auto">
                <motion.div 
                    style={{ scale, opacity, y }}
                    className="w-full max-w-5xl h-[70vh] bg-[#0a0a15] rounded-[2rem] border border-white/10 shadow-[0_0_100px_rgba(77,77,255,0.1)] flex flex-col overflow-hidden relative"
                >
                    {/* Fake Browser header */}
                    <div className="h-14 border-b border-white/5 bg-[#050510]/50 flex items-center px-6 gap-4 z-10 shrink-0 backdrop-blur-md">
                        <div className="flex gap-2.5">
                            <div className="w-3.5 h-3.5 rounded-full bg-white/20" />
                            <div className="w-3.5 h-3.5 rounded-full bg-white/20" />
                            <div className="w-3.5 h-3.5 rounded-full bg-white/20" />
                        </div>
                        <div className="flex-1 flex justify-center">
                            <div className="w-1/3 h-7 rounded-lg bg-white/5 border border-white/5 flex items-center justify-center opacity-70">
                                <p className="text-xs text-gray-400 font-mono">app.curezy.ai / new</p>
                            </div>
                        </div>
                    </div>

                    {/* Window Content */}
                    <div className="flex-1 flex flex-col items-center justify-center p-8 relative bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] bg-opacity-[0.02]">
                         {/* Centered big Prompt Input */}
                         <div className="w-full max-w-3xl bg-[#050510] border border-white/10 rounded-3xl p-8 lg:p-12 shadow-2xl relative min-h-[220px] flex flex-col justify-center transform transition-all">
                              <div className="absolute -inset-0.5 bg-gradient-to-r from-[#FF7A00]/20 to-[#4D4DFF]/20 blur-xl opacity-50 rounded-3xl -z-10" />
                              <h3 className="text-[#4D4DFF] font-black text-sm uppercase tracking-widest mb-6 flex items-center gap-2">
                                  <Sparkles className="w-4 h-4" /> Intake Session
                              </h3>
                              <p className="text-2xl md:text-3xl font-semibold text-white leading-normal md:leading-relaxed">
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
                    </div>
                </motion.div>
            </div>
        </section>
    )
}
"""

insert_idx = content.find("export default function Landing() {")
if insert_idx != -1:
    content = content[:insert_idx] + component_code + "\n\n" + content[insert_idx:]

hero_end_idx = content.find("            {/* 2. AI Pipeline Section (Scroll Sticky) */}")
if hero_end_idx != -1:
    content = content[:hero_end_idx] + "            {/* Scroll Mockup Transition */}\n            <PromptTransition />\n\n" + content[hero_end_idx:]

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Added PromptTransition component successfully.")
