import UnifiedPipeline from '../components/UnifiedPipeline';
import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, useScroll, useTransform, AnimatePresence, useMotionValueEvent } from 'framer-motion'
import { loginUser, signupUser } from '../api/client'
import { Sparkles, ArrowRight, Play, X, Loader2, BrainCircuit, ActivitySquare, ShieldCheck, HeartPulse, CheckCircle2, Database, MessageSquare } from 'lucide-react'

// Constants & Data
const FEATURES = [
    { icon: BrainCircuit, title: "Council of Experts", desc: "Three specialized models debating differential diagnoses." },
    { icon: ActivitySquare, title: "Radiology Analysis", desc: "Upload X-Rays and MRIs for instant AI screening." },
    { icon: ShieldCheck, title: "HIPAA Compliant", desc: "Your medical data is encrypted and never stored permanently." },
    { icon: HeartPulse, title: "Specialist Referrals", desc: "Connects you instantly with top-rated local doctors." }
]

const ROADMAP = [
    { title: "Symptom Checker", status: "Shipped", desc: "The core AI Council debate engine.", active: true },
    { title: "Radiology Beta", status: "Beta", desc: "Computer vision for medical imaging.", active: true },
    { title: "EHR Integration", status: "Upcoming", desc: "Seamless sync with major health records.", active: false },
    { title: "Voice Intake", status: "Upcoming", desc: "Talk directly to your AI physician.", active: false }
]

export default function Landing() {
    const [showAuth, setShowAuth] = useState(false)
    const [isLogin, setIsLogin] = useState(true)
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [fullName, setFullName] = useState('')
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)
    const [success, setSuccess] = useState('')
    const navigate = useNavigate()

    // Scroll Animations
    const { scrollYProgress: heroScroll } = useScroll({ offset: ["start start", "end start"] })
    const heroOpacity = useTransform(heroScroll, [0, 0.5], [1, 0])
    const heroY = useTransform(heroScroll, [0, 0.5], [0, 150])

    const containerRef = useRef(null)
    const { scrollYProgress: pipelineScroll } = useScroll({ target: containerRef, offset: ["start start", "end end"] })

    const handleSubmit = async () => {
        setError(''); setSuccess(''); setLoading(true)
        try {
            if (isLogin) {
                const { error } = await loginUser(email, password)
                if (error) throw error
                navigate('/chat')
            } else {
                const { error } = await signupUser(email, password, fullName)
                if (error) throw error
                setSuccess('Account created! Please check your email to confirm.')
            }
        } catch (err) {
            setError(err.message || 'Something went wrong')
        }
        setLoading(false)
    }

    return (
        <div className="relative min-h-screen bg-[#050510] text-white selection:bg-accent-purple/30 selection:text-white font-sans">

            {/* Ambient Starfield / Noise (Simulated) */}
            <div className="fixed inset-0 z-0 pointer-events-none opacity-20" style={{ backgroundImage: 'radial-gradient(circle, #ffffff 1px, transparent 1px)', backgroundSize: '40px 40px' }} />

            {/* Navbar */}
            <motion.nav
                initial={{ y: -20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ duration: 0.8, ease: "easeOut" }}
                className="fixed top-0 inset-x-0 z-50 flex items-center justify-between px-6 py-5 md:px-12 backdrop-blur-xl bg-[#050510]/60 border-b border-white/5"
            >
                <div className="flex items-center gap-3 cursor-pointer">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-[#4D4DFF] to-white flex items-center justify-center shadow-[0_0_15px_rgba(77,77,255,0.4)]">
                        <div className="flex gap-0.5">
                            <div className="w-1 h-3.5 bg-black rounded-full" />
                            <div className="w-1 h-5 bg-black rounded-full -translate-y-0.5" />
                            <div className="w-1 h-3 bg-black rounded-full translate-y-1" />
                        </div>
                    </div>
                    <span className="text-xl font-bold tracking-tight">Curezy</span>
                </div>

                <div className="hidden md:flex items-center gap-10 text-sm font-medium text-gray-300">
                    <a href="#pipeline" className="hover:text-white transition-colors">Overview</a>
                    <a href="#features" className="hover:text-white transition-colors">Features</a>
                    <a href="#roadmap" className="hover:text-white transition-colors">Roadmap</a>
                    <a href="#faq" className="hover:text-white transition-colors">FAQ</a>
                </div>

                <button
                    onClick={() => { setShowAuth(true); setIsLogin(true) }}
                    className="relative px-6 py-2.5 rounded-full overflow-hidden font-semibold text-sm transition-all hover:scale-105 border border-white/10 bg-white/5 hover:bg-white/10"
                >
                    <span className="relative flex items-center gap-2">
                        Get Started <ArrowRight size={14} />
                    </span>
                </button>
            </motion.nav>

            {/* 1. Hero Section */}
            <section className="relative z-10 pt-24 pb-12 px-6 md:px-12 flex flex-col items-center justify-center min-h-screen">
                <motion.div
                    style={{ opacity: heroOpacity, y: heroY }}
                    className="w-full max-w-5xl mx-auto flex flex-col items-center text-center"
                >
                    {/* Glowing Center Logo / Orb */}
                    <motion.div
                        initial={{ scale: 0.8, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        transition={{ duration: 1.2, ease: "easeOut" }}
                        className="relative w-24 h-24 mb-6 group"
                    >
                        {/* Outer Glow */}
                        <div className="absolute -inset-4 rounded-full bg-gradient-to-tr from-[#FF7A00] via-[#4D4DFF] to-white blur-xl opacity-60 group-hover:opacity-80 transition duration-1000 animate-pulse" style={{ animationDuration: '4s' }} />
                        {/* Solid Inner */}
                        <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-black to-[#1a1a3a] border border-white/20 flex items-center justify-center shadow-inner">
                            <Sparkles className="text-white w-8 h-8" />
                        </div>
                    </motion.div>

                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8, delay: 0.2 }}
                        className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-xs font-medium text-gray-300 mb-8 backdrop-blur-sm shadow-xl"
                    >
                        <span className="text-white font-bold">Curezy AI</span> <span className="text-gray-500 bg-white/10 px-1.5 rounded text-[10px]">Beta</span>
                    </motion.div>

                    <motion.h1
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8, delay: 0.3 }}
                        className="text-5xl md:text-7xl lg:text-[80px] font-bold tracking-tight text-white mb-8 leading-[1.1] max-w-4xl"
                    >
                        Clinical precision beyond imagination, <br className="hidden md:block" />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-gray-400 to-gray-600">one diagnosis away.</span>
                    </motion.h1>

                    {/* Search/Prompt Bar */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8, delay: 0.5 }}
                        className="w-full max-w-2xl relative mt-4 group"
                    >
                        {/* Glow Behind Bar */}
                        <div className="absolute -inset-0.5 rounded-full bg-gradient-to-r from-transparent via-[#4D4DFF]/30 to-transparent blur-md opacity-0 group-hover:opacity-100 transition duration-500" />

                        <div className="relative flex items-center bg-[#11111a] border border-white/10 rounded-full p-2 pl-6 shadow-2xl backdrop-blur-xl">
                            <Sparkles className="text-white w-5 h-5 mr-3 shrink-0" />
                            <input
                                type="text"
                                readOnly
                                value="Severe headache, nausea, and sensitivity to light for 3 days."
                                className="flex-1 bg-transparent text-sm md:text-base text-gray-400 outline-none truncate cursor-pointer font-medium"
                                onClick={() => { setShowAuth(true); setIsLogin(true) }}
                            />
                            <button
                                onClick={() => { setShowAuth(true); setIsLogin(true) }}
                                className="ml-2 px-6 py-3 rounded-full bg-white/10 text-white font-semibold text-sm hover:bg-white/20 transition-colors flex items-center gap-2 border border-white/5"
                            >
                                Generate <ArrowRight size={14} />
                            </button>
                        </div>
                    </motion.div>

                    <motion.button
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.8, duration: 1 }}
                        className="mt-10 flex items-center gap-2 text-sm font-medium text-gray-400 hover:text-white transition-colors border border-white/10 rounded-full px-4 py-2 bg-white/5 backdrop-blur"
                    >
                        <Play size={14} className="fill-current" /> Watch the video
                    </motion.button>
                </motion.div>

                {/* The "Planet/Dome" Background Glow */}
                <div className="absolute top-[60vh] left-1/2 -translate-x-1/2 w-[150vw] h-[100vh] bg-gradient-to-b from-[#4D4DFF]/10 to-transparent border-t border-white/10 rounded-[100%] z-[-1] blur-sm transition-opacity opacity-70" />
            </section>

            {/* Unified AI Pipeline (Morphing) */}
            <UnifiedPipeline />

            {/* 3. Features Section */}
            <section id="features" className="relative z-20 border-t border-white/5 bg-black/40 py-32">
                <div className="max-w-7xl mx-auto px-6 md:px-12 text-center">
                    <h3 className="text-[#FF7A00] font-bold text-xl mb-4">Key Features</h3>
                    <h2 className="text-4xl md:text-5xl font-bold tracking-tight mb-6">The first AI that truly<br />understands medicine.</h2>
                    <p className="text-xl text-gray-400 mb-20">Analyzing clinical data for any symptom, in any standard format.</p>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {FEATURES.map((f, i) => (
                            <motion.div
                                key={i}
                                initial={{ opacity: 0, y: 30 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true, margin: "-100px" }}
                                transition={{ duration: 0.6, delay: i * 0.1 }}
                                className="bg-white/[0.03] border border-white/[0.08] hover:bg-white/[0.05] hover:border-white/20 transition-all rounded-3xl p-8 text-left group"
                            >
                                <div className="w-12 h-12 bg-white/10 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 group-hover:bg-[#4D4DFF]/20 transition-transform">
                                    <f.icon className="text-white w-6 h-6" />
                                </div>
                                <h4 className="text-lg font-bold mb-3">{f.title}</h4>
                                <p className="text-sm text-gray-400 leading-relaxed">{f.desc}</p>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* 4. Roadmap Section */}
            <section id="roadmap" className="relative z-20 py-32 max-w-7xl mx-auto px-6 md:px-12">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-16">
                    <div>
                        <h3 className="text-[#FF7A00] font-bold text-xl mb-4">Roadmap</h3>
                        <h2 className="text-4xl md:text-5xl font-bold tracking-tight mb-6 leading-tight">The tool that evolves<br />and grows with you.</h2>
                        <p className="text-gray-400 text-lg mb-12">Curezy AI is still in beta... features currently in development for future versions:</p>

                        <div className="space-y-6">
                            {ROADMAP.map((item, i) => (
                                <motion.div
                                    key={i}
                                    initial={{ opacity: 0, x: -20 }}
                                    whileInView={{ opacity: 1, x: 0 }}
                                    viewport={{ once: true }}
                                    transition={{ delay: i * 0.1 }}
                                    className="flex items-start gap-4"
                                >
                                    <div className="mt-1">
                                        {item.active ? (
                                            <CheckCircle2 className="text-[#4D4DFF] w-6 h-6" />
                                        ) : (
                                            <div className="w-6 h-6 border-2 border-white/20 rounded-full" />
                                        )}
                                    </div>
                                    <div>
                                        <div className="flex items-center gap-3 mb-1">
                                            <h4 className={`text-xl font-bold ${item.active ? 'text-white' : 'text-gray-500'}`}>{item.title}</h4>
                                            <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full ${item.active ? 'bg-white/10 text-white' : 'bg-transparent border border-gray-600 text-gray-600'}`}>
                                                {item.status}
                                            </span>
                                        </div>
                                        <p className="text-gray-400 text-sm">{item.desc}</p>
                                    </div>
                                </motion.div>
                            ))}
                        </div>
                    </div>

                    {/* Visual Card Side */}
                    <div className="flex items-center justify-center">
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            whileInView={{ scale: 1, opacity: 1 }}
                            viewport={{ once: true }}
                            className="w-full max-w-sm aspect-square bg-gradient-to-br from-[#1a1a3a] to-black border border-white/10 rounded-3xl p-8 relative overflow-hidden shadow-2xl"
                        >
                            <div className="absolute -inset-10 bg-[#FF7A00]/20 blur-3xl rounded-full opacity-50 mix-blend-screen" />
                            <div className="relative z-10 h-full flex flex-col justify-between">
                                <ActivitySquare className="w-12 h-12 text-[#FF7A00]" />
                                <div>
                                    <p className="text-xs font-bold text-[#FF7A00] tracking-wider uppercase mb-2">Beta Feature Spotlight</p>
                                    <h3 className="text-2xl font-bold text-white mb-2">X-Ray Analysis</h3>
                                    <p className="text-sm text-gray-400">Upload your DICOM or JPEG radiology scans for a multi-model read.</p>
                                </div>
                            </div>
                        </motion.div>
                    </div>
                </div>
            </section>

            {/* 5. Footer */}
            <footer className="relative z-20 border-t border-white/10 bg-black pt-20 pb-10">
                <div className="max-w-7xl mx-auto px-6 md:px-12 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-12 lg:gap-8 mb-16">
                    <div className="lg:col-span-2">
                        <div className="flex items-center gap-2 mb-6">
                            <Sparkles className="text-white w-6 h-6" />
                            <span className="text-2xl font-bold tracking-tight">Curezy AI</span>
                        </div>
                        <p className="text-gray-400 mb-8 max-w-sm">Medicine for the future. Diagnosing complexities at the speed of thought.</p>
                        <button
                            onClick={() => { setShowAuth(true); setIsLogin(true) }}
                            className="px-6 py-2.5 rounded-full bg-white text-black font-semibold text-sm hover:scale-105 transition-transform"
                        >
                            Get Started
                        </button>
                    </div>

                    <div>
                        <h4 className="text-white font-bold mb-6">Product</h4>
                        <ul className="space-y-4 text-sm text-gray-400">
                            <li><a href="#" className="hover:text-white transition-colors">Council Models</a></li>
                            <li><a href="#" className="hover:text-white transition-colors">Pricing</a></li>
                            <li><a href="#" className="hover:text-white transition-colors">Changelog</a></li>
                            <li><a href="#" className="hover:text-white transition-colors">API Keys</a></li>
                        </ul>
                    </div>

                    <div>
                        <h4 className="text-white font-bold mb-6">Resources</h4>
                        <ul className="space-y-4 text-sm text-gray-400">
                            <li><a href="#" className="hover:text-white transition-colors">Documentation</a></li>
                            <li><a href="#" className="hover:text-white transition-colors">Medical Disclaimers</a></li>
                            <li><a href="#" className="hover:text-white transition-colors">Help Center</a></li>
                        </ul>
                    </div>

                    <div>
                        <h4 className="text-white font-bold mb-6">Company</h4>
                        <ul className="space-y-4 text-sm text-gray-400">
                            <li><a href="#" className="hover:text-white transition-colors">About Us</a></li>
                            <li><a href="#" className="hover:text-white transition-colors">Careers</a></li>
                            <li><a href="#" className="hover:text-white transition-colors">Privacy Policy</a></li>
                            <li><a href="#" className="hover:text-white transition-colors">Terms of Service</a></li>
                        </ul>
                    </div>
                </div>

                <div className="max-w-7xl mx-auto px-6 md:px-12 border-t border-white/10 pt-8 flex flex-col md:flex-row items-center justify-between text-xs text-gray-500">
                    <p>© 2026 Curezy AI Lab. All rights reserved.</p>
                    <div className="flex gap-4 mt-4 md:mt-0">
                        <a href="#" className="hover:text-white">Twitter</a>
                        <a href="#" className="hover:text-white">Discord</a>
                        <a href="#" className="hover:text-white">LinkedIn</a>
                    </div>
                </div>
            </footer>

            {/* Auth Modal Overlay (Re-used from previous Plan) */}
            <AnimatePresence>
                {showAuth && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-[100] flex items-center justify-center p-4"
                    >
                        <div className="absolute inset-0 bg-black/60 backdrop-blur-md" onClick={() => setShowAuth(false)} />

                        <motion.div
                            initial={{ scale: 0.95, y: 20 }}
                            animate={{ scale: 1, y: 0 }}
                            exit={{ scale: 0.95, y: 20 }}
                            className="relative w-full max-w-md bg-[#050510]/90 border border-white/10 rounded-3xl p-8 overflow-hidden backdrop-blur-xl shadow-[0_0_50px_rgba(0,0,0,0.8)]"
                        >
                            <button onClick={() => setShowAuth(false)} className="absolute top-4 right-4 text-gray-400 hover:text-white p-2 rounded-full hover:bg-white/10 transition-colors">
                                <X size={20} />
                            </button>

                            <div className="text-center mb-8">
                                <div className="w-12 h-12 rounded-full bg-gradient-to-tr from-[#4D4DFF] to-white flex items-center justify-center mx-auto mb-4 shadow-[0_0_20px_rgba(77,77,255,0.4)]">
                                    <Sparkles className="text-black w-6 h-6" />
                                </div>
                                <h2 className="text-2xl font-bold text-white mb-2 tracking-tight">
                                    {isLogin ? 'Welcome back' : 'Start the Magic'}
                                </h2>
                                <p className="text-gray-400 text-sm">
                                    {isLogin ? 'Sign in to access your medical copilot' : 'Create an account to begin'}
                                </p>
                            </div>

                            {error && (
                                <div className="bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3 mb-5 text-red-400 text-sm font-medium">
                                    {error}
                                </div>
                            )}
                            {success && (
                                <div className="bg-green-500/10 border border-green-500/20 rounded-xl px-4 py-3 mb-5 text-green-400 text-sm font-medium">
                                    {success}
                                </div>
                            )}

                            <div className="space-y-4">
                                {!isLogin && (
                                    <div>
                                        <input
                                            type="text" value={fullName} onChange={e => setFullName(e.target.value)}
                                            placeholder="Full Name (e.g. Dr. John Smith)"
                                            className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3.5 text-sm text-white focus:outline-none focus:border-[#4D4DFF] transition-all placeholder-gray-600 shadow-inner"
                                        />
                                    </div>
                                )}

                                <div>
                                    <input
                                        type="email" value={email} onChange={e => setEmail(e.target.value)}
                                        placeholder="Email Address"
                                        className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3.5 text-sm text-white focus:outline-none focus:border-[#4D4DFF] transition-all placeholder-gray-600 shadow-inner"
                                    />
                                </div>

                                <div>
                                    <input
                                        type="password" value={password} onChange={e => setPassword(e.target.value)}
                                        placeholder="Password" onKeyDown={e => e.key === 'Enter' && handleSubmit()}
                                        className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3.5 text-sm text-white focus:outline-none focus:border-[#4D4DFF] transition-all placeholder-gray-600 shadow-inner"
                                    />
                                </div>

                                <button
                                    onClick={handleSubmit} disabled={loading}
                                    className="relative w-full overflow-hidden rounded-xl font-bold py-4 text-sm text-white disabled:opacity-50 mt-4 group bg-white/5 border border-white/10 hover:bg-white/10 transition-colors"
                                >
                                    <span className="relative flex items-center justify-center gap-2">
                                        {loading && <Loader2 size={16} className="animate-spin" />}
                                        {loading ? 'Please wait...' : isLogin ? 'Sign In Securely' : 'Create Account'}
                                    </span>
                                </button>
                            </div>

                            <div className="mt-6 text-center">
                                <button
                                    onClick={() => { setIsLogin(!isLogin); setError(''); setSuccess('') }}
                                    className="text-gray-500 hover:text-white text-sm font-medium transition-colors"
                                >
                                    {isLogin ? "Don't have an account? Sign up" : 'Already have an account? Sign in'}
                                </button>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    )
}
