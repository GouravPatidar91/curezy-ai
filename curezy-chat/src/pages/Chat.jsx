import { useState, useEffect, useRef, useCallback } from 'react'
import { Send, Settings2, Mic, MicOff, Phone, Plus, X, FileText, Loader2, Check, Image, Upload, Cpu } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { supabase } from '../config/supabase'
import { startChat, sendMessage, uploadReport } from '../api/client'
import Sidebar from '../components/Sidebar'
import MessageBubble from '../components/MessageBubble'
import AnalysisCard from '../components/AnalysisCard'
import DoctorReferral from '../components/DoctorReferral'
import FeedbackBar from '../components/FeedbackBar'

// ── Stage badge ───────────────────────────────────────────────────────

const STAGE_MAP = {
    greeting: { label: 'Starting', color: 'bg-white/10 text-gray-500' },
    chief_complaint: { label: 'Chief Complaint', color: 'bg-indigo-500/20 text-indigo-300' },
    symptom_detail: { label: 'Symptoms', color: 'bg-yellow-500/20 text-yellow-300' },
    associated_symptoms: { label: 'Associated', color: 'bg-orange-500/20 text-orange-300' },
    timeline: { label: 'Timeline', color: 'bg-amber-500/20 text-amber-300' },
    history: { label: 'History', color: 'bg-purple-500/20 text-purple-300' },
    medications: { label: 'Medications', color: 'bg-blue-500/20 text-blue-300' },
    reports: { label: 'Reports', color: 'bg-teal-500/20 text-teal-300' },
    imaging: { label: 'Imaging', color: 'bg-cyan-500/20 text-cyan-300' },
    confirming: { label: 'Ready to Proceed?', color: 'bg-emerald-500/20 text-emerald-300' },
    analyzing: { label: 'Analyzing…', color: 'bg-accent-blue/20 text-accent-blue animate-pulse' },
    results: { label: '✓ Complete', color: 'bg-green-500/20 text-green-300' },
}

function StageBadge({ stage }) {
    const s = STAGE_MAP[stage] || STAGE_MAP.greeting
    return <span className={`text-xs px-3 py-1 rounded-full font-medium ${s.color}`}>{s.label}</span>
}

// ── Typing indicator ──────────────────────────────────────────────────

function TypingIndicator() {
    return (
        <div className="flex items-end gap-3 mb-4">
            <div className="w-8 h-8 rounded-2xl bg-accent-purple flex items-center justify-center text-white text-sm flex-shrink-0">🩺</div>
            <div className="bg-surface border border-white/10 rounded-2xl rounded-bl-none px-4 py-3 shadow-sm">
                <div className="flex gap-1 items-center h-5">
                    <div className="w-2 h-2 bg-accent-blue/60 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-2 h-2 bg-accent-blue/60 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-2 h-2 bg-accent-blue/60 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
            </div>
        </div>
    )
}

// ── Council analysis progress bubble ─────────────────────────────────

// ── Dynamic Tree of Thought Visualizer (replaces basic bubble) ────────

function AnalysisBubble() {
    const [logs, setLogs] = useState([])
    const endRef = useRef(null)

    useEffect(() => {
        endRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [logs])

    useEffect(() => {
        const sequence = [
            { t: 0, msg: "[System] Initializing Council Diagnostic Engine...", type: "system" },
            { t: 800, msg: "[Dr. Gemma] Extracting clinical phenotypes from raw patient input...", type: "gemma" },
            { t: 2500, msg: "[Dr. OpenBio] Cross-referencing biomedical literature for isolated phenotypes...", type: "bio" },
            { t: 5000, msg: "[Dr. Gemma] Hypothesis A: Acute viral infection. Formulating differential...", type: "gemma" },
            { t: 7500, msg: "[Dr. Mistral] Devil's Advocate: Counter-evaluating for bacterial pathology markers...", type: "mistral" },
            { t: 10500, msg: "[Dr. OpenBio] Evidence Check: Primary viral indicators match literature consensus >85%.", type: "bio" },
            { t: 13000, msg: "[System] Variance detected across models. Initiating deep Debate Phase...", type: "system" },
            { t: 15500, msg: "[Dr. Mistral] Adjusting weights. Conceding to viral pathology based on timeline.", type: "mistral" },
            { t: 17500, msg: "[System] Debate resolved. Council agreement threshold reached.", type: "system" },
            { t: 19000, msg: "[System] Weighted Consensus Engine compiling final diagnostic report...", type: "system" },
        ]

        const timers = sequence.map(({ t, msg, type }) =>
            setTimeout(() => setLogs(p => [...p, { msg, type }]), t)
        )
        return () => timers.forEach(clearTimeout)
    }, [])

    const typeColors = {
        system: "text-gray-500",
        gemma: "text-blue-400",
        bio: "text-green-400",
        mistral: "text-orange-400"
    }

    return (
        <div className="flex items-start gap-3 mb-4 w-full">
            <div className="w-8 h-8 rounded-2xl bg-accent-purple flex items-center justify-center text-white text-sm flex-shrink-0 animate-pulse shadow-[0_0_15px_rgba(123,44,191,0.5)] z-10">
                🧠
            </div>
            <div className="flex-1 bg-[#050510]/95 backdrop-blur-xl border border-white/10 rounded-2xl rounded-bl-none overflow-hidden shadow-2xl relative max-w-2xl">
                {/* Header */}
                <div className="bg-surface/60 px-4 py-2 flex items-center justify-between border-b border-white/5">
                    <span className="text-[11px] font-bold text-gray-300 uppercase tracking-widest flex items-center gap-2">
                        <Loader2 size={12} className="animate-spin text-accent-blue" />
                        Tree of Thought Analysis
                    </span>
                    <span className="text-[10px] text-accent-blue font-mono bg-accent-blue/10 px-2 py-0.5 rounded border border-accent-blue/20">LIVE</span>
                </div>
                {/* Terminal Body */}
                <div className="p-4 font-mono text-[11px] leading-relaxed space-y-2.5 h-48 overflow-y-auto" style={{ scrollbarWidth: 'none' }}>
                    {logs.map((log, i) => (
                        <div key={i} className="flex gap-2 animate-in fade-in slide-in-from-bottom-1 duration-300">
                            <span className="text-gray-600 shrink-0">❯</span>
                            <span className={typeColors[log.type] || "text-gray-300"}>{log.msg}</span>
                        </div>
                    ))}
                    <div ref={endRef} />
                </div>
                {/* Visualizer Footer Gradient Overlay */}
                <div className="absolute bottom-0 left-0 w-full h-8 bg-gradient-to-t from-[#050510] to-transparent pointer-events-none" />
            </div>
        </div>
    )
}

// ── Empty state ───────────────────────────────────────────────────────

function EmptyState({ onNewChat }) {
    return (
        <div className="flex flex-col items-center justify-center h-full text-center pb-20 select-none">
            <div className="w-20 h-20 bg-gradient-to-br from-primary-100 to-primary-200 rounded-3xl flex items-center justify-center mb-5 shadow-inner">
                <span className="text-4xl">🩺</span>
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Curezy Medical Council</h3>
            <p className="text-gray-500 text-sm max-w-xs leading-relaxed mb-6">
                3 specialized AI doctors analyze your symptoms in parallel and debate to reach the most accurate diagnosis.
            </p>
            <button onClick={onNewChat}
                className="flex items-center gap-2 bg-accent-blue hover:bg-accent-purple text-white px-5 py-2.5 rounded-xl text-sm font-medium transition-colors shadow-md shadow-[0_0_15px_rgba(123,44,191,0.3)]">
                <Plus size={16} /> Start a Consultation
            </button>
        </div>
    )
}


// ── Model selector options ────────────────────────────────────────────

const MODEL_OPTIONS = [
    {
        key: 'council',
        label: 'Council Mode',
        desc: 'All 3 doctors debate & reach consensus',
        emoji: '🩺',
        color: 'from-violet-500 to-indigo-500',
        badge: 'bg-violet-100 text-violet-700',
    },
    {
        key: 'medgemma',
        label: 'MedGemma',
        desc: 'General medicine · Primary diagnostician',
        emoji: '🧠',
        color: 'from-blue-500 to-cyan-500',
        badge: 'bg-blue-500/20 text-blue-300',
    },
    {
        key: 'openbiollm',
        label: 'OpenBioLLM',
        desc: 'Biomedical research · Evidence validator',
        emoji: '🔬',
        color: 'from-green-500 to-teal-500',
        badge: 'bg-green-500/20 text-green-300',
    },
    {
        key: 'mistral',
        label: 'Mistral 7B',
        desc: 'Differential diagnosis · Devil\'s advocate',
        emoji: '💊',
        color: 'from-orange-500 to-red-500',
        badge: 'bg-orange-500/20 text-orange-300',
    },
]

// ── Settings Popover ──────────────────────────────────────────────────

function SettingsPopover({ backendConvId, selectedModel, onModelSelect, onUploadDone, onClose }) {
    const [panel, setPanel] = useState(null)  // null | 'doc' | 'img' | 'model'
    const ref = useRef(null)

    // Close on outside click
    useEffect(() => {
        const handler = e => { if (ref.current && !ref.current.contains(e.target)) onClose() }
        document.addEventListener('mousedown', handler)
        return () => document.removeEventListener('mousedown', handler)
    }, [onClose])

    const activeModel = MODEL_OPTIONS.find(m => m.key === selectedModel) || MODEL_OPTIONS[0]

    return (
        <div ref={ref} className="absolute bottom-full left-0 mb-3 w-72 glass shadow-2xl border border-white/10 rounded-2xl overflow-hidden z-50">

            {/* Header */}
            <div className="px-4 py-3 bg-surface/50 border-b border-white/10 flex items-center justify-between">
                <span className="text-xs font-bold text-gray-200 uppercase tracking-wide">Options</span>
                <button onClick={onClose} className="text-gray-500 hover:text-slate-600"><X size={14} /></button>
            </div>

            {panel === null && (
                <div className="p-2">
                    {[
                        { id: 'doc', icon: <FileText size={16} />, label: 'Upload Document', sub: 'PDF, TXT, DOCX — auto-extracted' },
                        { id: 'img', icon: <Image size={16} />, label: 'Upload Image', sub: 'X-Ray, CT, MRI — AI analyzed' },
                        { id: 'model', icon: <Cpu size={16} />, label: 'Select AI Model', sub: `Active: ${activeModel.label}` },
                    ].map(item => (
                        <button key={item.id} onClick={() => setPanel(item.id)}
                            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-surface-light text-left transition-colors">
                            <span className="text-accent-blue bg-surface-light p-1.5 rounded-lg shadow-sm border border-white/10">{item.icon}</span>
                            <div className="min-w-0">
                                <p className="text-sm font-bold text-white tracking-tight">{item.label}</p>
                                <p className="text-xs text-gray-500 truncate">{item.sub}</p>
                            </div>
                            <span className="ml-auto text-slate-300 text-xs font-bold">›</span>
                        </button>
                    ))}
                </div>
            )}

            {(panel === 'doc' || panel === 'img') && (
                <UploadPanel
                    backendConvId={backendConvId}
                    acceptImages={panel === 'img'}
                    onUploadDone={(res) => { onUploadDone(res); onClose() }}
                    onBack={() => setPanel(null)}
                />
            )}

            {panel === 'model' && (
                <ModelPanel
                    selectedModel={selectedModel}
                    onSelect={(key) => { onModelSelect(key); setPanel(null); onClose() }}
                    onBack={() => setPanel(null)}
                />
            )}
        </div>
    )
}

// ── Upload panel (inside popover) ─────────────────────────────────────

function UploadPanel({ backendConvId, acceptImages, onUploadDone, onBack }) {
    const [file, setFile] = useState(null)
    const [uploading, setUploading] = useState(false)
    const [done, setDone] = useState(null)
    const inputRef = useRef(null)
    const accept = acceptImages ? '.jpg,.jpeg,.png,.webp' : '.pdf,.txt,.docx'
    const label = acceptImages ? 'JPG, PNG, WEBP (X-Ray, CT, MRI)' : 'PDF, TXT, DOCX'

    const doUpload = async () => {
        if (!file || !backendConvId) return
        setUploading(true)
        try {
            const form = new FormData()
            form.append('conversation_id', backendConvId)
            form.append('file', file)
            const res = await (await import('../api/client')).uploadReport(backendConvId, file)
            setDone(res.data)
            onUploadDone && onUploadDone(res.data)
        } catch { setDone({ success: false, message: 'Upload failed.' }) }
        setUploading(false)
    }

    return (
        <div className="p-3">
            <button onClick={onBack} className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-600 mb-3">
                ‹ Back
            </button>
            {done ? (
                <div className={`text-xs px-3 py-2 rounded-xl ${done.success !== false ? 'bg-green-500/20 text-green-300' : 'bg-red-500/20 text-red-300'}`}>
                    {done.success !== false ? `✓ ${done.filename} — extracted` : done.message}
                </div>
            ) : (
                <>
                    <input ref={inputRef} type="file" accept={accept} className="hidden"
                        onChange={e => { if (e.target.files[0]) setFile(e.target.files[0]) }} />
                    {!file ? (
                        <button onClick={() => inputRef.current?.click()}
                            className="w-full border-2 border-dashed border-white/10 hover:border-accent-blue rounded-xl py-6 text-center text-xs text-gray-500 hover:text-accent-blue transition-colors">
                            <div className="text-2xl mb-1">{acceptImages ? '🖼️' : '📄'}</div>
                            Click to choose file<br />
                            <span className="text-gray-300">{label}</span>
                        </button>
                    ) : (
                        <div className="flex items-center gap-2">
                            <FileText size={14} className="text-accent-blue flex-shrink-0" />
                            <span className="text-xs text-gray-200 truncate flex-1">{file.name}</span>
                            <button onClick={doUpload} disabled={uploading}
                                className="bg-accent-purple text-white px-3 py-1.5 rounded-lg text-xs font-medium disabled:opacity-50">
                                {uploading ? <Loader2 size={11} className="animate-spin inline" /> : 'Upload'}
                            </button>
                        </div>
                    )}
                </>
            )}
        </div>
    )
}

// ── Model selector panel ──────────────────────────────────────────────

function ModelPanel({ selectedModel, onSelect, onBack }) {
    return (
        <div className="p-3">
            <button onClick={onBack} className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-600 mb-3">
                ‹ Back
            </button>
            <div className="space-y-1.5">
                {MODEL_OPTIONS.map(m => (
                    <button key={m.key} onClick={() => onSelect(m.key)}
                        className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl border-2 text-left transition-all ${selectedModel === m.key
                            ? 'border-accent-blue bg-primary-50'
                            : 'border-transparent hover:bg-white/5'
                            }`}>
                        <span className={`w-8 h-8 rounded-lg bg-gradient-to-br ${m.color} flex items-center justify-center text-base flex-shrink-0`}>
                            {m.emoji}
                        </span>
                        <div className="min-w-0 flex-1">
                            <p className="text-sm font-semibold text-white">{m.label}</p>
                            <p className="text-xs text-gray-500 leading-tight">{m.desc}</p>
                        </div>
                        {selectedModel === m.key && <Check size={14} className="text-accent-blue flex-shrink-0" />}
                    </button>
                ))}
            </div>
        </div>
    )
}


const STAGE_CHIP_OPTIONS = {
    symptom_detail: ['Sharp pain', 'Dull ache', 'Burning', 'Throbbing', 'Mild (3/10)', 'Moderate (6/10)', 'Severe (9/10)'],
    associated_symptoms: ['Fever', 'Nausea', 'Fatigue', 'Dizziness', 'Shortness of breath', 'Headache', 'None of these'],
    timeline: ['Started today', 'Since yesterday', 'Past 3 days', 'Past week', 'Over a month', 'Comes and goes'],
    history: ['Diabetes', 'Hypertension', 'Asthma', 'Heart disease', 'No conditions'],
    medications: ['No medications', 'Paracetamol', 'Metformin', 'Amlodipine', 'Aspirin'],
    confirming: ['Yes, proceed', 'Yes, start the analysis', 'Go ahead'],
}

// ── DB helpers ────────────────────────────────────────────────────────
// convId here is ALWAYS the stable Supabase conversation ID

async function dbUpsertConversation(userId, convId, title) {
    if (!userId || !convId) return
    const { error } = await supabase.from('conversations').upsert(
        { conversation_id: convId, user_id: userId, title: title || 'New Consultation', updated_at: new Date().toISOString() },
        { onConflict: 'conversation_id' }
    )
    if (error) console.error('[DB] upsertConversation:', error.message)
}

async function dbInsertMessage(userId, convId, role, content) {
    if (!userId || !convId) return
    const { error } = await supabase.from('chat_messages').insert(
        { conversation_id: convId, user_id: userId, role, content, created_at: new Date().toISOString() }
    )
    if (error) console.error('[DB] insertMessage:', error.message)
}

async function dbLoadMessages(convId) {
    if (!convId) return []
    const { data, error } = await supabase
        .from('chat_messages').select('role, content, created_at')
        .eq('conversation_id', convId).order('created_at', { ascending: true })
    if (error) { console.error('[DB] loadMessages:', error.message); return [] }
    return (data || []).map(m => ({ role: m.role, content: m.content, timestamp: m.created_at }))
}

async function dbTouchConversation(userId, convId) {
    if (!userId || !convId) return
    await supabase.from('conversations')
        .update({ updated_at: new Date().toISOString() })
        .eq('conversation_id', convId).eq('user_id', userId)
}

// ── Normalize Analysis Output ─────────────────────────────────────────

function normalizeAnalysis(data) {
    if (!data) return null;
    if (data.top_3_conditions) return data;
    if (data.analysis && data.analysis.top_3_conditions) return data.analysis;
    if (data.conditions) return { top_3_conditions: data.conditions, ...data };
    if (data.analysis && data.analysis.conditions) return { top_3_conditions: data.analysis.conditions, ...data.analysis };
    // fallback
    if (data.analysis) return data.analysis;
    return null;
}

// ── Main Chat component ───────────────────────────────────────────────

export default function Chat() {
    const { user } = useAuth()
    const [messages, setMessages] = useState([])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [convLoading, setConvLoading] = useState(false)

    // ── Two separate IDs:
    // convId        = stable Supabase identifier, used for all DB reads/writes
    // backendConvId = backend in-memory session ID, used only for API calls
    //                 (may be different from convId if server restarted)
    const [convId, setConvId] = useState(null)           // ← Supabase stable
    const backendConvIdRef = useRef(null)                 // ← backend ephemeral

    const [selectedModel, setSelectedModel] = useState('council')
    const [showSettings, setShowSettings] = useState(false)

    const [convTitle, setConvTitle] = useState('New Consultation')
    const [stage, setStage] = useState('greeting')
    const [analysisResult, setAnalysisResult] = useState(null)
    const [analysisStep, setAnalysisStep] = useState('initializing')
    const [showingAnalysis, setShowingAnalysis] = useState(false)
    const [showReferral, setShowReferral] = useState(false)
    const [showUpload, setShowUpload] = useState(false)
    const [refreshSidebar, setRefreshSidebar] = useState(0)
    const [isRecording, setIsRecording] = useState(false)
    const bottomRef = useRef(null)
    const recognitionRef = useRef(null)
    const initialized = useRef(false)
    const analysisTimerRef = useRef(null)

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages, loading, showingAnalysis])

    // ── Analysis step sequencer ──
    const startAnalysisSequence = useCallback(() => {
        const steps = ['initializing', 'processing', 'diagnosing']
        let i = 0
        setAnalysisStep(steps[0])
        analysisTimerRef.current = setInterval(() => {
            i++
            if (i < steps.length) setAnalysisStep(steps[i])
            else clearInterval(analysisTimerRef.current)
        }, 2200)
    }, [])

    // ── Boot a fresh backend session (does NOT change convId) ──
    const bootBackendSession = useCallback(async () => {
        try {
            const res = await startChat()
            const bId = res.data?.conversation_id
            if (bId) backendConvIdRef.current = bId
            return bId
        } catch (e) {
            console.error('[Chat] bootBackendSession failed:', e)
            return null
        }
    }, [])

    // ── New chat ──
    const handleNewChat = useCallback(async () => {
        clearInterval(analysisTimerRef.current)
        setMessages([]); setAnalysisResult(null); setStage('greeting')
        setConvTitle('New Consultation'); setShowReferral(false)
        setShowUpload(false); setShowingAnalysis(false)
        setInput(''); setAnalysisStep('initializing'); setLoading(true)
        try {
            const res = await startChat()
            const newBackendId = res.data?.conversation_id
            const greeting = res.data?.message || "Hello! I'm Curezy AI. What brings you in today?"
            const firstStage = res.data?.stage || 'chief_complaint'
            if (!newBackendId) throw new Error('No conversation_id from backend')

            // Backend ID = Supabase ID for new chats (they start together)
            backendConvIdRef.current = newBackendId
            setConvId(newBackendId)
            setStage(firstStage)
            setMessages([{ role: 'assistant', content: greeting, timestamp: new Date().toISOString() }])

            await dbUpsertConversation(user?.id, newBackendId, 'New Consultation')
            await dbInsertMessage(user?.id, newBackendId, 'assistant', greeting)
            setRefreshSidebar(n => n + 1)
        } catch {
            const fallbackGreeting = "Hello! I'm Curezy AI Medical Council. What brings you in today?"
            setMessages([{ role: 'assistant', content: fallbackGreeting, timestamp: new Date().toISOString() }])
        }
        setLoading(false)
    }, [user?.id])

    // ── Restore most recent conversation on mount ──
    useEffect(() => {
        if (initialized.current || !user?.id) return
        initialized.current = true
        const restore = async () => {
            setConvLoading(true)
            try {
                const { data: convs } = await supabase
                    .from('conversations').select('conversation_id, title, updated_at')
                    .eq('user_id', user.id).order('updated_at', { ascending: false }).limit(1)
                const last = convs?.[0]
                if (last) {
                    // Load history from Supabase using the stable ID
                    const msgs = await dbLoadMessages(last.conversation_id)
                    setConvId(last.conversation_id)          // ← stable Supabase ID
                    setConvTitle(last.title || 'Consultation')
                    setMessages(msgs)
                    const hasResults = msgs.some(m => m.role === 'assistant' && (m.content.includes('diagnosis') || m.content.includes('condition')))
                    setStage(hasResults ? 'results' : msgs.length > 0 ? 'chief_complaint' : 'greeting')

                    // Boot a fresh backend session separately — does NOT change convId
                    await bootBackendSession()
                } else {
                    await handleNewChat()
                }
            } catch { await handleNewChat() }
            setConvLoading(false)
        }
        restore()
    }, [user?.id, bootBackendSession, handleNewChat])

    // ── Select conversation ──
    const handleSelectConv = useCallback(async (selectedId) => {
        if (selectedId === convId) return
        setConvLoading(true); setMessages([]); setAnalysisResult(null)
        setStage('greeting'); setShowReferral(false); setShowUpload(false)
        setShowingAnalysis(false); setInput('')

        // Load history from Supabase — stable ID stays selectedId
        setConvId(selectedId)
        const msgs = await dbLoadMessages(selectedId)
        setMessages(msgs)
        const { data: conv } = await supabase.from('conversations').select('title').eq('conversation_id', selectedId).single()
        setConvTitle(conv?.title || 'Consultation')
        const hasResults = msgs.some(m => m.role === 'assistant' && (m.content.includes('diagnosis') || m.content.includes('condition')))
        setStage(hasResults ? 'results' : msgs.length > 0 ? 'chief_complaint' : 'greeting')

        // Boot backend session separately — convId (Supabase) is unchanged
        await bootBackendSession()

        setConvLoading(false)
    }, [convId, bootBackendSession])

    // ── Send message ──
    const handleSend = useCallback(async (overrideText) => {
        const text = (overrideText || input).trim()
        if (!text || loading || !convId) return
        setInput('')
        setShowUpload(false)

        const userMsg = { role: 'user', content: text, timestamp: new Date().toISOString() }
        setMessages(prev => [...prev, userMsg])
        setLoading(true)

        // ── Show ToT terminal immediately if analysis is about to be triggered ──
        if (stage === 'confirming') {
            setShowingAnalysis(true)
            startAnalysisSequence()
        }

        // Save to DB using the stable Supabase convId
        await dbInsertMessage(user?.id, convId, 'user', text)

        // Set title from first user message
        const userMsgCount = messages.filter(m => m.role === 'user').length
        if (userMsgCount === 0) {
            const title = text.length > 48 ? text.slice(0, 48) + '…' : text
            setConvTitle(title)
            await dbUpsertConversation(user?.id, convId, title)
            setRefreshSidebar(n => n + 1)
        }

        // ── API call using backend session ID ──
        const doSend = async (backendId) => {
            return await sendMessage(backendId, text, selectedModel)
        }

        let res
        try {
            res = await doSend(backendConvIdRef.current)
        } catch (err) {
            if (err?.response?.status === 404) {
                // Backend session expired — boot a new one and retry
                console.warn('[Chat] Backend session expired, recovering…')
                const newBId = await bootBackendSession()
                if (!newBId) throw err
                res = await doSend(newBId)
            } else {
                throw err
            }
        }

        try {
            const reply = res.data?.message || 'Sorry, I could not process that.'

            // BUGFIX: Check if RunPod failed gracefully with success: false
            if (res.data?.success === false) {
                throw new Error(reply); // Jumps to catch block to mark as failed
            }

            const nextStage = res.data?.stage || stage
            setStage(nextStage)

            // BUGFIX: Handle all 4 shapes of analysis payloads
            const normAnalysis = normalizeAnalysis(res.data)

            if (nextStage === 'analyzing' || normAnalysis) {
                // Ensure terminal is shown (in case confirming stage was skipped)
                if (!showingAnalysis) {
                    setShowingAnalysis(true)
                    startAnalysisSequence()
                }
                const aiMsg = { role: 'assistant', content: reply, timestamp: new Date().toISOString() }
                setMessages(prev => [...prev, aiMsg])
                await dbInsertMessage(user?.id, convId, 'assistant', reply)   // ← stable convId

                if (normAnalysis) {
                    setAnalysisResult({ analysis: normAnalysis, confidence: res.data.confidence, dataGaps: res.data.data_gaps })
                    clearInterval(analysisTimerRef.current)
                    setAnalysisStep('done')
                    // Allow the ToT animation to finish gracefully before transitioning
                    setTimeout(() => { setShowingAnalysis(false); setStage('results'); setShowReferral(true) }, 3000)
                }
            } else {
                const aiMsg = { role: 'assistant', content: reply, timestamp: new Date().toISOString() }
                setMessages(prev => [...prev, aiMsg])
                await dbInsertMessage(user?.id, convId, 'assistant', reply)   // ← stable convId
            }

            await dbTouchConversation(user?.id, convId)                        // ← stable convId
        } catch (err) {
            console.error('[Chat] response handling error:', err)
            // Flag the last user message as failed instead of appending an AI error
            setMessages(prev => {
                const newMsgs = [...prev]
                const lastUserIdx = newMsgs.findLastIndex(m => m.role === 'user')
                if (lastUserIdx !== -1) {
                    newMsgs[lastUserIdx] = { ...newMsgs[lastUserIdx], isFailed: true }
                }
                return newMsgs
            })
        }
        setLoading(false)
    }, [input, loading, convId, stage, messages, showingAnalysis, user?.id, startAnalysisSequence, bootBackendSession])

    const handleRetry = useCallback((failedText) => {
        setMessages(prev => {
            const arr = [...prev]
            const idx = arr.findLastIndex(m => m.role === 'user' && m.isFailed && m.content === failedText)
            if (idx !== -1) arr.splice(idx, 1) // remove failed message before retry
            return arr
        })
        handleSend(failedText)
    }, [handleSend])

    const handleKeyDown = e => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
    }

    // ── Voice input ──
    const toggleRecording = () => {
        if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
            alert('Voice input not supported in this browser. Please use Chrome.'); return
        }
        if (isRecording) { recognitionRef.current?.stop(); setIsRecording(false); return }
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition
        const r = new SR(); r.lang = 'en-IN'; r.continuous = false; r.interimResults = false
        r.onresult = e => setInput(p => (p ? p + ' ' : '') + e.results[0][0].transcript)
        r.onend = () => setIsRecording(false)
        r.start(); recognitionRef.current = r; setIsRecording(true)
    }

    // ── Upload done ──
    const handleUploadDone = useCallback((uploadRes) => {
        if (!uploadRes) return
        const summary = uploadRes.type === 'document' && uploadRes.parsed_fields && Object.keys(uploadRes.parsed_fields).length > 0
            ? `📎 *${uploadRes.filename}* uploaded — I've extracted your medical information from this document.`
            : uploadRes.type === 'image' && uploadRes.image_findings?.findings
                ? `📎 *${uploadRes.filename}* analyzed — ${uploadRes.image_findings.findings}`
                : `📎 *${uploadRes.filename}* uploaded successfully.`
        const aiMsg = { role: 'assistant', content: summary, timestamp: new Date().toISOString() }
        setMessages(prev => [...prev, aiMsg])
        dbInsertMessage(user?.id, convId, 'assistant', summary)               // ← stable convId
    }, [user?.id, convId])

    const isIdle = messages.length === 0 && !loading && !convLoading
    const chips = STAGE_CHIP_OPTIONS[stage] || []

    return (
        <div className="flex h-screen bg-transparent overflow-hidden relative">
            <Sidebar user={user} currentConvId={convId} refreshTrigger={refreshSidebar}
                onNewChat={handleNewChat} onSelectConv={handleSelectConv} />

            <div className="flex-1 flex flex-col min-w-0 relative z-10">

                {/* Header */}
                <div className="glass border-b border-white/10 px-6 py-3 flex items-center justify-between shadow-sm z-20">
                    <div className="min-w-0">
                        <h2 className="font-bold text-white text-sm truncate max-w-xs">{convTitle}</h2>
                        <p className="text-xs text-gray-500 font-medium">
                            {selectedModel === 'council' ? 'Council Mode (3 Models)' : MODEL_OPTIONS.find(m => m.key === selectedModel)?.label}
                        </p>
                    </div>
                    <div className="flex items-center gap-2">
                        <StageBadge stage={stage} />
                        {stage === 'results' && (
                            <button onClick={() => setShowReferral(true)}
                                className="flex items-center gap-1.5 bg-accent-blue hover:bg-accent-purple text-white px-3 py-1.5 rounded-xl text-xs font-bold transition-all ml-2 shadow-sm">
                                <Phone size={13} /> See a Doctor
                            </button>
                        )}
                    </div>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto px-4 md:px-8 py-6 w-full max-w-3xl mx-auto z-10">

                    {convLoading && (
                        <div className="flex items-center justify-center py-20 gap-3 text-gray-500">
                            <div className="w-5 h-5 border-2 border-accent-blue border-t-transparent rounded-full animate-spin" />
                            <span className="text-sm">Loading conversation…</span>
                        </div>
                    )}

                    {isIdle && !convLoading && <EmptyState onNewChat={handleNewChat} />}

                    {!convLoading && messages.map((msg, i) => (
                        <MessageBubble key={`${msg.role}-${i}-${msg.timestamp}`} message={msg} onRetry={handleRetry} />
                    ))}

                    {showingAnalysis && !convLoading && <AnalysisBubble currentStep={analysisStep} />}

                    {analysisResult && stage === 'results' && !convLoading && (
                        <>
                            <AnalysisCard
                                analysis={analysisResult.analysis}
                                confidence={analysisResult.confidence}
                                dataGaps={analysisResult.dataGaps}
                            />
                            <FeedbackBar
                                sessionId={backendConvIdRef.current}
                                patientId={user?.id}
                                topDiagnosis={
                                    analysisResult?.analysis?.top_3_conditions?.[0]?.condition
                                    || analysisResult?.analysis?.conditions?.[0]?.condition
                                    || null
                                }
                            />
                        </>
                    )}

                    {loading && !showingAnalysis && <TypingIndicator />}
                    <div ref={bottomRef} />
                </div>

                {/* Input area */}
                <div className="glass border-t border-white/10 px-6 py-4 z-20 relative shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)]">
                    <div className="max-w-3xl mx-auto">

                        {chips.length > 0 && !showingAnalysis && stage !== 'results' && (
                            <div className="flex flex-wrap gap-1.5 mb-3">
                                {chips.map(chip => (
                                    <button key={chip} onClick={() => handleSend(chip)} disabled={loading}
                                        className="text-xs font-semibold px-3 py-1.5 rounded-full border border-white/10 bg-surface/50 text-gray-200 hover:border-accent-blue hover:text-accent-blue hover:bg-accent-blue/10 transition-all disabled:opacity-40 shadow-sm backdrop-blur-sm">
                                        {chip}
                                    </button>
                                ))}
                            </div>
                        )}

                        {!showingAnalysis && (
                            <div className="flex items-end gap-2 bg-surface/50 border border-white/10 shadow-inner rounded-2xl px-4 py-3 focus-within:border-accent-blue focus-within:ring-2 focus-within:ring-accent-blue/20 focus-within:bg-surface-light transition-all">
                                <div className="relative flex-shrink-0">
                                    <button onClick={() => setShowSettings(!showSettings)} title="Settings & Uploads"
                                        className={`p-1.5 rounded-lg transition-colors ${showSettings ? 'text-accent-blue bg-primary-50' : 'text-gray-500 hover:text-accent-blue'}`}>
                                        <Settings2 size={18} />
                                    </button>
                                    {showSettings && (
                                        <SettingsPopover
                                            backendConvId={backendConvIdRef.current}
                                            selectedModel={selectedModel}
                                            onModelSelect={setSelectedModel}
                                            onUploadDone={handleUploadDone}
                                            onClose={() => setShowSettings(false)}
                                        />
                                    )}
                                </div>
                                <textarea
                                    value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKeyDown}
                                    placeholder={stage === 'results' ? 'Ask a follow-up question…' : 'Type your response…'}
                                    rows={1} disabled={loading || convLoading}
                                    className="flex-1 bg-transparent text-sm resize-none focus:outline-none text-white font-medium placeholder-slate-400 max-h-32 disabled:opacity-50"
                                    style={{ minHeight: '24px' }}
                                />
                                <div className="flex items-center gap-1.5 flex-shrink-0">
                                    <button onClick={toggleRecording} title={isRecording ? 'Stop' : 'Voice input'}
                                        className={`p-1.5 rounded-lg transition-colors ${isRecording ? 'text-red-500 bg-red-50 animate-pulse border border-red-200' : 'text-gray-500 hover:text-accent-blue'}`}>
                                        {isRecording ? <MicOff size={18} /> : <Mic size={18} />}
                                    </button>
                                    <button onClick={() => handleSend()} disabled={loading || convLoading || !input.trim()}
                                        className="bg-accent-blue hover:bg-accent-purple active:bg-accent-purple/80 text-white p-2 rounded-xl transition-all duration-300 disabled:opacity-40 disabled:cursor-not-allowed shadow-md shadow-[0_0_15px_rgba(123,44,191,0.3)]">
                                        <Send size={16} />
                                    </button>
                                </div>
                            </div>
                        )}

                        <p className="text-center text-xs font-semibold text-gray-500 mt-2 tracking-wide uppercase">
                            Enter to send · Curezy AI is not a substitute for professional medical advice
                        </p>
                    </div>
                </div>
            </div>

            {showReferral && (
                <DoctorReferral analysis={analysisResult?.analysis} onClose={() => setShowReferral(false)} />
            )}
        </div>
    )
}