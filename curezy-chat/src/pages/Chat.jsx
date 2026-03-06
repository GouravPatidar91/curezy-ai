import { useState, useEffect, useRef, useCallback } from 'react'
import { Send, Mic, MicOff, Phone, Plus, X, FileText, Loader2, Check, Image, Paperclip, ChevronDown, ArrowUp, Brain, Search, Activity, Heart, ShieldCheck } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { supabase } from '../config/supabase'
import { startChat, sendMessage, uploadReport, resumeChat } from '../api/client'
import Sidebar from '../components/Sidebar'
import MessageBubble from '../components/MessageBubble'
import AnalysisCard from '../components/AnalysisCard'
import FeedbackBar from '../components/FeedbackBar'
import DoctorReferral from '../components/DoctorReferral'

// ── Helpers ──────────────────────────────────────────────────────────

// ── Stage badge ───────────────────────────────────────────────────────

const STAGE_MAP = {
    greeting: { label: 'Starting' },
    chief_complaint: { label: 'Chief Complaint' },
    symptom_detail: { label: 'Symptoms' },
    associated_symptoms: { label: 'Associated' },
    timeline: { label: 'Timeline' },
    history: { label: 'History' },
    medications: { label: 'Medications' },
    reports: { label: 'Reports' },
    imaging: { label: 'Imaging' },
    confirming: { label: 'Ready to Proceed?' },
    analyzing: { label: 'Analyzing...' },
    results: { label: 'Complete' },
}

function StageBadge({ stage }) {
    const s = STAGE_MAP[stage] || STAGE_MAP.greeting
    const isAnalyzing = stage === 'analyzing'
    const isResults = stage === 'results'
    const baseClass = 'text-[11px] px-2 py-0.5 rounded font-medium'
    const colorClass = isAnalyzing
        ? 'bg-accent-green/10 text-accent-green animate-pulse'
        : isResults
            ? 'bg-accent-green/10 text-accent-green'
            : 'bg-[#2a2a2a] text-[#888]'
    return <span className={`${baseClass} ${colorClass}`}>{s.label}</span>
}

// ── Typing indicator ──────────────────────────────────────────────────

function TypingIndicator() {
    return (
        <div className="flex items-start gap-3 mb-5">
            <img src="/curezy logo.png" alt="Curezy" className="w-7 h-7 rounded-full object-contain flex-shrink-0 mt-0.5 bg-[#2f2f2f]" />
            <div className="pt-2">
                <div className="flex gap-1">
                    <div className="w-2 h-2 bg-[#555] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-2 h-2 bg-[#555] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-2 h-2 bg-[#555] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
            </div>
        </div>
    )
}

// ── Council analysis thinking block ──────────────────────────────────

function AnalysisBubble() {
    const [logs, setLogs] = useState([])
    const [expanded, setExpanded] = useState(true)
    const endRef = useRef(null)

    useEffect(() => {
        endRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [logs, expanded])

    useEffect(() => {
        const sequence = [
            { t: 0, msg: "Initializing Secure Diagnostic Environment...", type: "system", icon: <ShieldCheck size={14} className="text-[#666]" /> },
            { t: 800, msg: "Curezy AURIX: Extracting clinical markers from patterns...", type: "gemma", icon: <Brain size={14} className="text-blue-400" /> },
            { t: 2500, msg: "Curezy AURA: Mapping symptoms to biomedical knowledge base...", type: "bio", icon: <Search size={14} className="text-emerald-400" /> },
            { t: 5000, msg: "Curezy AURIX: Formulating initial differential prioritizations...", type: "gemma", icon: <Brain size={14} className="text-blue-400" /> },
            { t: 7500, msg: "Curezy AURIS: Stress-testing hypotheses for inconsistencies...", type: "mistral", icon: <Activity size={14} className="text-amber-400" /> },
            { t: 10500, msg: "Curezy AURA: Verifying compliance with latest clinical guidelines...", type: "bio", icon: <Search size={14} className="text-emerald-400" /> },
            { t: 13000, msg: "Synthesizing Council consensus and evidence clusters...", type: "system", icon: <Heart size={14} className="text-pink-400" /> },
            { t: 15500, msg: "AURIS: Conceding to high-probability pathology markers.", type: "mistral", icon: <Activity size={14} className="text-amber-400" /> },
            { t: 17500, msg: "Finalizing diagnostic confidence weights...", type: "system", icon: <ShieldCheck size={14} className="text-[#666]" /> },
            { t: 19000, msg: "Compiling detailed clinical assessment report...", type: "system", icon: <ShieldCheck size={14} className="text-[#666]" /> },
        ]

        const timers = sequence.map(({ t, msg, type, icon }) =>
            setTimeout(() => setLogs(p => [...p, { msg, type, icon }]), t)
        )
        return () => timers.forEach(clearTimeout)
    }, [])

    return (
        <div className="mb-6 max-w-2xl">
            <div className="bg-[#1a1a1a]/40 border border-[#2a2a2a] rounded-2xl overflow-hidden backdrop-blur-sm transition-all duration-300 hover:border-[#333]">
                <button
                    onClick={() => setExpanded(!expanded)}
                    className="w-full px-4 py-3 border-b border-[#2a2a2a] flex items-center justify-between hover:bg-[#222]/50 transition-colors"
                >
                    <div className="flex items-center gap-3">
                        <div className="relative">
                            <Brain size={16} className="text-accent-green" />
                            <div className="absolute inset-0 bg-accent-green/20 blur-md animate-pulse rounded-full" />
                        </div>
                        <span className="text-[13px] text-white/90 font-medium flex items-center gap-2">
                            Thinking
                            <span className="inline-flex gap-0.5">
                                <span className="w-1 h-1 bg-accent-green rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                <span className="w-1 h-1 bg-accent-green rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                <span className="w-1 h-1 bg-accent-green rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                            </span>
                        </span>
                    </div>
                    <ChevronDown size={14} className={`text-[#666] transition-transform duration-300 ${expanded ? 'rotate-180' : ''}`} />
                </button>

                {expanded && (
                    <div className="p-4 bg-[#1a1a1a]/60 font-medium text-[12px] leading-relaxed space-y-3.5 max-h-[320px] overflow-y-auto custom-scrollbar">
                        {logs.map((log, i) => (
                            <div key={i} className="flex gap-3 fade-in items-start group">
                                <span className="shrink-0 mt-0.5 opacity-80 group-hover:opacity-100 transition-opacity">
                                    {log.icon || <span className="text-[#444]">&#10095;</span>}
                                </span>
                                <span className="text-[#888] group-hover:text-[#aaa] transition-colors">{log.msg}</span>
                            </div>
                        ))}
                        <div ref={endRef} />
                    </div>
                )}
            </div>
        </div>
    )
}

// ── Empty state ───────────────────────────────────────────────────────

function EmptyState({ onNewChat }) {
    return (
        <div className="flex flex-col items-center justify-center h-full text-center pb-24 select-none">
            <img src="/curezy logo.png" alt="Curezy" className="w-16 h-16 rounded-2xl object-contain mb-6 bg-[#2f2f2f] p-2" />
            <h3 className="text-xl font-semibold text-white mb-2 tracking-tight">Curezy Medical Council</h3>
            <p className="text-[#777] text-sm max-w-sm leading-relaxed mb-8">
                3 specialized AI doctors analyze your symptoms in parallel and debate to reach the most accurate diagnosis.
            </p>
            <button onClick={onNewChat}
                className="flex items-center gap-2 bg-white text-[#212121] px-6 py-2.5 rounded-xl text-sm font-semibold transition-all hover:bg-[#e5e5e5]">
                <Plus size={16} /> Start a Consultation
            </button>
        </div>
    )
}


// ── Model selector options ────────────────────────────────────────────

const MODEL_OPTIONS = [
    { key: 'council', label: 'AURANET (Thinking)', desc: 'Full council debate -- most accurate' },
    { key: 'medgemma', label: 'AURIX', desc: 'Primary diagnostician' },
    { key: 'openbiollm', label: 'AURA', desc: 'Biomedical evidence engine' },
    { key: 'mistral', label: 'AURIS', desc: "Fast lightweight -- Devil's advocate" },
]

// ── Model selector dropdown (now inside input area) ───────────────────

function ModelSelector({ selectedModel, onSelect }) {
    const [open, setOpen] = useState(false)
    const ref = useRef(null)
    const active = MODEL_OPTIONS.find(m => m.key === selectedModel) || MODEL_OPTIONS[0]

    useEffect(() => {
        const handler = e => { if (ref.current && !ref.current.contains(e.target)) setOpen(false) }
        document.addEventListener('mousedown', handler)
        return () => document.removeEventListener('mousedown', handler)
    }, [])

    return (
        <div ref={ref} className="relative">
            <button
                onClick={() => setOpen(o => !o)}
                className="flex items-center gap-1 text-[12px] text-[#777] hover:text-[#bbb] transition-colors rounded px-1 py-0.5"
            >
                {active.label}
                <ChevronDown size={12} className={`transition-transform ${open ? 'rotate-180' : ''}`} />
            </button>
            {open && (
                <div className="absolute bottom-full left-0 mb-2 w-72 bg-[#2a2a2a] border border-[#3a3a3a] rounded-xl shadow-2xl overflow-hidden z-50">
                    <div className="px-3 py-2 border-b border-[#333]">
                        <p className="text-[11px] text-[#666] font-medium uppercase tracking-wide">Model</p>
                    </div>
                    {MODEL_OPTIONS.map(m => (
                        <button
                            key={m.key}
                            onClick={() => { onSelect(m.key); setOpen(false) }}
                            className={`w-full flex items-center justify-between px-3 py-2.5 text-left transition-colors ${selectedModel === m.key ? 'bg-[#333]' : 'hover:bg-[#333]'
                                }`}
                        >
                            <div className="min-w-0">
                                <p className="text-[13px] font-medium text-[#ddd]">{m.label}</p>
                                <p className="text-[11px] text-[#666] leading-tight">{m.desc}</p>
                            </div>
                            {selectedModel === m.key && <Check size={14} className="text-accent-green flex-shrink-0 ml-2" />}
                        </button>
                    ))}
                </div>
            )}
        </div>
    )
}

// ── Attachment dropdown ───────────────────────────────────────────────

function AttachDropdown({ backendConvId, onUploadDone }) {
    const [open, setOpen] = useState(false)
    const [mode, setMode] = useState(null)
    const [file, setFile] = useState(null)
    const [uploading, setUploading] = useState(false)
    const [done, setDone] = useState(null)
    const ref = useRef(null)
    const inputRef = useRef(null)

    useEffect(() => {
        const handler = e => { if (ref.current && !ref.current.contains(e.target)) { setOpen(false); setMode(null); setFile(null); setDone(null) } }
        document.addEventListener('mousedown', handler)
        return () => document.removeEventListener('mousedown', handler)
    }, [])

    const accept = mode === 'img' ? '.jpg,.jpeg,.png,.webp' : '.pdf,.txt,.docx'

    const doUpload = async () => {
        if (!file || !backendConvId) return
        setUploading(true)
        try {
            const res = await uploadReport(backendConvId, file)
            setDone(res.data)
            onUploadDone && onUploadDone(res.data)
            setTimeout(() => { setOpen(false); setMode(null); setFile(null); setDone(null) }, 1500)
        } catch { setDone({ success: false, message: 'Upload failed.' }) }
        setUploading(false)
    }

    const handleChoose = (type) => {
        setMode(type)
        setFile(null)
        setDone(null)
        setTimeout(() => inputRef.current?.click(), 50)
    }

    return (
        <div ref={ref} className="relative">
            <button
                onClick={() => { setOpen(o => !o); setMode(null); setFile(null); setDone(null) }}
                className="p-1.5 rounded-lg text-[#666] hover:text-[#aaa] transition-colors"
                title="Attach file"
            >
                <Paperclip size={18} />
            </button>
            {open && !mode && (
                <div className="absolute bottom-full left-0 mb-2 w-56 bg-[#2a2a2a] border border-[#3a3a3a] rounded-xl shadow-2xl overflow-hidden z-50">
                    <button onClick={() => handleChoose('doc')} className="w-full flex items-center gap-3 px-4 py-3 hover:bg-[#333] transition-colors text-left">
                        <FileText size={16} className="text-[#999]" />
                        <div>
                            <p className="text-[13px] text-[#ddd]">Upload Document</p>
                            <p className="text-[11px] text-[#666]">PDF, TXT, DOCX</p>
                        </div>
                    </button>
                    <div className="border-t border-[#333]" />
                    <button onClick={() => handleChoose('img')} className="w-full flex items-center gap-3 px-4 py-3 hover:bg-[#333] transition-colors text-left">
                        <Image size={16} className="text-[#999]" />
                        <div>
                            <p className="text-[13px] text-[#ddd]">Upload Image</p>
                            <p className="text-[11px] text-[#666]">X-Ray, CT, MRI</p>
                        </div>
                    </button>
                </div>
            )}
            {open && mode && (
                <div className="absolute bottom-full left-0 mb-2 w-64 bg-[#2a2a2a] border border-[#3a3a3a] rounded-xl shadow-2xl overflow-hidden z-50 p-3">
                    <input ref={inputRef} type="file" accept={accept} className="hidden"
                        onChange={e => { if (e.target.files[0]) setFile(e.target.files[0]) }} />
                    {done ? (
                        <div className={`text-xs px-3 py-2 rounded-lg ${done.success !== false ? 'text-accent-green' : 'text-red-400'}`}>
                            {done.success !== false ? `Uploaded ${done.filename}` : done.message}
                        </div>
                    ) : !file ? (
                        <button onClick={() => inputRef.current?.click()}
                            className="w-full border border-dashed border-[#444] hover:border-[#666] rounded-xl py-5 text-center text-xs text-[#666] hover:text-[#aaa] transition-colors">
                            Click to choose file
                        </button>
                    ) : (
                        <div className="flex items-center gap-2">
                            <FileText size={14} className="text-[#999] flex-shrink-0" />
                            <span className="text-xs text-[#ddd] truncate flex-1">{file.name}</span>
                            <button onClick={doUpload} disabled={uploading}
                                className="bg-accent-green text-white px-3 py-1.5 rounded-lg text-xs font-medium disabled:opacity-50 transition-colors hover:bg-[#0d8c6b]">
                                {uploading ? <Loader2 size={11} className="animate-spin inline" /> : 'Upload'}
                            </button>
                        </div>
                    )}
                </div>
            )}
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

    const [convId, setConvId] = useState(null)
    const backendConvIdRef = useRef(null)

    const [selectedModel, setSelectedModel] = useState('council')

    const [convTitle, setConvTitle] = useState('New Consultation')
    const [stage, setStage] = useState('greeting')
    const [analysisResult, setAnalysisResult] = useState(null)
    const [analysisStep, setAnalysisStep] = useState('initializing')
    const [showingAnalysis, setShowingAnalysis] = useState(false)
    const [showReferral, setShowReferral] = useState(false)
    const [refreshSidebar, setRefreshSidebar] = useState(0)
    const [isRecording, setIsRecording] = useState(false)
    const bottomRef = useRef(null)
    const recognitionRef = useRef(null)
    const initialized = useRef(false)
    const analysisTimerRef = useRef(null)

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages, loading, showingAnalysis])

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

    const handleNewChat = useCallback(async () => {
        console.log('[Chat] Starting new session...')
        clearInterval(analysisTimerRef.current)
        setMessages([]); setAnalysisResult(null); setStage('greeting')
        setConvTitle('New Consultation'); setShowReferral(false)
        setShowingAnalysis(false)
        setInput(''); setAnalysisStep('initializing'); setLoading(true)
        try {
            const res = await startChat()
            const newBackendId = res.data?.conversation_id
            const greeting = res.data?.message || "Hello! I'm Curezy AI. What brings you in today?"
            const firstStage = res.data?.stage || 'chief_complaint'

            if (!newBackendId) {
                console.warn('[Chat] Backend returned no ID, using fallback')
                throw new Error('No conversion ID')
            }

            backendConvIdRef.current = newBackendId
            setConvId(newBackendId)
            setStage(firstStage)
            setMessages([{ role: 'assistant', content: greeting, timestamp: new Date().toISOString() }])

            await dbUpsertConversation(user?.id, newBackendId, 'New Consultation')
            await dbInsertMessage(user?.id, newBackendId, 'assistant', greeting)
            setRefreshSidebar(n => n + 1)
        } catch (err) {
            console.error('[Chat] handleNewChat failed:', err)
            const fallbackId = `temp_${Date.now()}`
            setConvId(fallbackId)
            backendConvIdRef.current = fallbackId
            const fallbackGreeting = "Hello! I'm Curezy AI Medical Council. What brings you in today?"
            setMessages([{ role: 'assistant', content: fallbackGreeting, timestamp: new Date().toISOString() }])
        } finally {
            setLoading(false)
        }
    }, [user?.id])

    useEffect(() => {
        if (initialized.current || !user?.id) return
        initialized.current = true
        const restore = async () => {
            console.log('[Chat] Restoring session for user:', user.id)
            setConvLoading(true)
            try {
                const { data: convs } = await supabase
                    .from('conversations').select('conversation_id, title, updated_at')
                    .eq('user_id', user.id).order('updated_at', { ascending: false }).limit(1)
                const last = convs?.[0]
                if (last) {
                    const convId = last.conversation_id
                    setConvId(convId)
                    setConvTitle(last.title || 'Consultation')

                    // Sync with backend state
                    try {
                        const res = await resumeChat(convId)
                        if (res.data?.success) {
                            setMessages(res.data.messages || [])
                            setStage(res.data.stage || 'chief_complaint')
                            if (res.data.analysis_result) {
                                const ar = res.data.analysis_result
                                setAnalysisResult({
                                    analysis: normalizeAnalysis(ar.analysis || ar),
                                    confidence: ar.confidence,
                                    dataGaps: ar.data_gaps
                                })
                                setShowReferral(true)
                            }
                        } else {
                            // Fallback to basic message loading if resumeChat fails
                            const msgs = await dbLoadMessages(convId)
                            setMessages(msgs)
                            const hasResults = msgs.some(m => m.role === 'assistant' && (m.content.includes('diagnosis') || m.content.includes('condition')))
                            setStage(hasResults ? 'results' : msgs.length > 0 ? 'chief_complaint' : 'greeting')
                        }
                    } catch (e) {
                        console.warn('[Chat] resumeChat failed, fallback to local restore:', e)
                        const msgs = await dbLoadMessages(convId)
                        setMessages(msgs)
                        const hasResults = msgs.some(m => m.role === 'assistant' && (m.content.includes('diagnosis') || m.content.includes('condition')))
                        setStage(hasResults ? 'results' : msgs.length > 0 ? 'chief_complaint' : 'greeting')
                    }

                    backendConvIdRef.current = convId
                } else {
                    await handleNewChat()
                }
            } catch (err) {
                console.error('[Chat] Restore failed:', err)
                await handleNewChat()
            } finally {
                setConvLoading(false)
            }
        }
        restore()
    }, [user?.id, bootBackendSession, handleNewChat])

    const handleSelectConv = useCallback(async (selectedId) => {
        if (selectedId === convId) return
        setConvLoading(true); setMessages([]); setAnalysisResult(null)
        setStage('greeting'); setShowReferral(false)
        setShowingAnalysis(false); setInput('')

        setConvId(selectedId)
        backendConvIdRef.current = selectedId

        try {
            const res = await resumeChat(selectedId)
            if (res.data?.success) {
                setMessages(res.data.messages || [])
                setStage(res.data.stage || 'chief_complaint')
                if (res.data.analysis_result) {
                    const ar = res.data.analysis_result
                    setAnalysisResult({
                        analysis: normalizeAnalysis(ar.analysis || ar),
                        confidence: ar.confidence,
                        dataGaps: ar.data_gaps
                    })
                    setShowReferral(true)
                }
            } else {
                const msgs = await dbLoadMessages(selectedId)
                setMessages(msgs)
                const hasResults = msgs.some(m => m.role === 'assistant' && (m.content.includes('diagnosis') || m.content.includes('condition')))
                setStage(hasResults ? 'results' : msgs.length > 0 ? 'chief_complaint' : 'greeting')
            }
        } catch (e) {
            console.warn('[Chat] handleSelectConv resumeChat failed:', e)
            const msgs = await dbLoadMessages(selectedId)
            setMessages(msgs)
            const hasResults = msgs.some(m => m.role === 'assistant' && (m.content.includes('diagnosis') || m.content.includes('condition')))
            setStage(hasResults ? 'results' : msgs.length > 0 ? 'chief_complaint' : 'greeting')
        }

        const { data: conv } = await supabase.from('conversations').select('title').eq('conversation_id', selectedId).single()
        setConvTitle(conv?.title || 'Consultation')

        setConvLoading(false)
    }, [convId])

    const handleSend = useCallback(async (overrideText) => {
        const text = (overrideText || input).trim()
        if (!text || loading || !convId) return
        setInput('')

        const userMsg = { role: 'user', content: text, timestamp: new Date().toISOString() }
        setMessages(prev => [...prev, userMsg])
        setLoading(true)

        if (stage === 'confirming') {
            setShowingAnalysis(true)
            startAnalysisSequence()
        }

        await dbInsertMessage(user?.id, convId, 'user', text)

        const userMsgCount = messages.filter(m => m.role === 'user').length
        if (userMsgCount === 0) {
            const title = text.length > 48 ? text.slice(0, 48) + '...' : text
            setConvTitle(title)
            await dbUpsertConversation(user?.id, convId, title)
            setRefreshSidebar(n => n + 1)
        }

        const doSend = async (backendId) => {
            return await sendMessage(backendId, text, selectedModel)
        }

        let res
        try {
            res = await doSend(backendConvIdRef.current)
        } catch (err) {
            if (err?.response?.status === 404) {
                console.warn('[Chat] Backend session expired, recovering...')
                const newBId = await bootBackendSession()
                if (!newBId) throw err
                res = await doSend(newBId)
            } else if (err?.code === 'ECONNABORTED' || err?.message?.toLowerCase().includes('timeout')) {
                console.warn('[Chat] Request timed out — backend still processing.')
                const waitMsg = {
                    role: 'assistant',
                    content: 'The AI Council is still analyzing your case -- this can take a few minutes for complex diagnostics. Please wait, results will appear shortly.',
                    timestamp: new Date().toISOString(),
                    isInfo: true,
                }
                setMessages(prev => [...prev, waitMsg])
                setLoading(false)
                return
            } else {
                throw err
            }
        }

        try {
            const reply = res.data?.message || 'Sorry, I could not process that.'

            if (res.data?.success === false) {
                throw new Error(reply)
            }

            const nextStage = res.data?.stage || stage
            setStage(nextStage)

            const normAnalysis = normalizeAnalysis(res.data)

            if (nextStage === 'analyzing' || normAnalysis) {
                if (!showingAnalysis) {
                    setShowingAnalysis(true)
                    startAnalysisSequence()
                }

                if (normAnalysis) {
                    setAnalysisResult({ analysis: normAnalysis, confidence: res.data.confidence, dataGaps: res.data.data_gaps })
                    clearInterval(analysisTimerRef.current)
                    setAnalysisStep('done')
                    setTimeout(() => { setShowingAnalysis(false); setStage('results'); setShowReferral(true) }, 3000)
                } else {
                    const aiMsg = { role: 'assistant', content: reply, timestamp: new Date().toISOString() }
                    setMessages(prev => [...prev, aiMsg])
                    await dbInsertMessage(user?.id, convId, 'assistant', reply)
                }
            } else {
                const aiMsg = { role: 'assistant', content: reply, timestamp: new Date().toISOString() }
                setMessages(prev => [...prev, aiMsg])
                await dbInsertMessage(user?.id, convId, 'assistant', reply)
            }

            await dbTouchConversation(user?.id, convId)
        } catch (err) {
            console.error('[Chat] response handling error:', err)
            clearInterval(analysisTimerRef.current)
            setShowingAnalysis(false)
            setAnalysisStep('initializing')
            setStage(prev => prev === 'analyzing' ? 'confirming' : prev)
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
    }, [input, loading, convId, stage, messages, showingAnalysis, user?.id, startAnalysisSequence, bootBackendSession, selectedModel])

    const handleRetry = useCallback((failedText) => {
        setMessages(prev => {
            const arr = [...prev]
            const idx = arr.findLastIndex(m => m.role === 'user' && m.isFailed && m.content === failedText)
            if (idx !== -1) arr.splice(idx, 1)
            return arr
        })
        handleSend(failedText)
    }, [handleSend])

    const handleKeyDown = e => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
    }

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

    const handleUploadDone = useCallback((uploadRes) => {
        if (!uploadRes) return
        const summary = uploadRes.type === 'document' && uploadRes.parsed_fields && Object.keys(uploadRes.parsed_fields).length > 0
            ? `*${uploadRes.filename}* uploaded -- medical information extracted.`
            : uploadRes.type === 'image' && uploadRes.image_findings?.findings
                ? `*${uploadRes.filename}* analyzed -- ${uploadRes.image_findings.findings}`
                : `*${uploadRes.filename}* uploaded successfully.`
        const aiMsg = { role: 'assistant', content: summary, timestamp: new Date().toISOString() }
        setMessages(prev => [...prev, aiMsg])
        dbInsertMessage(user?.id, convId, 'assistant', summary)
    }, [user?.id, convId])

    const isIdle = messages.length === 0 && !loading && !convLoading
    const chips = STAGE_CHIP_OPTIONS[stage] || []

    return (
        <div className="flex h-screen bg-[#212121] overflow-hidden relative">
            <Sidebar user={user} currentConvId={convId} refreshTrigger={refreshSidebar}
                onNewChat={handleNewChat} onSelectConv={handleSelectConv} />

            <div className="flex-1 flex flex-col min-w-0 relative z-10">

                {/* Minimal header */}
                <div className="bg-[#212121] border-b border-[#2a2a2a] px-5 py-2 flex items-center justify-between z-20">
                    <StageBadge stage={stage} />
                    <div className="flex items-center gap-3">
                        {stage === 'results' && (
                            <button onClick={() => setShowReferral(true)}
                                className="flex items-center gap-1.5 text-[#888] hover:text-white text-[12px] transition-colors px-2.5 py-1 rounded-lg hover:bg-[#2f2f2f]">
                                <Phone size={13} /> See a Doctor
                            </button>
                        )}
                    </div>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto px-4 py-6 w-full max-w-3xl mx-auto z-10">

                    {convLoading && (
                        <div className="flex items-center justify-center py-20 gap-3 text-[#666]">
                            <Loader2 size={18} className="animate-spin text-[#888]" />
                            <span className="text-sm">Loading conversation...</span>
                        </div>
                    )}

                    {isIdle && !convLoading && <EmptyState onNewChat={handleNewChat} />}

                    {!convLoading && messages
                        .map((msg, i) => (
                            <MessageBubble
                                key={`${msg.role}-${i}-${msg.timestamp}`}
                                message={msg}
                                onRetry={handleRetry}
                                analysisResult={analysisResult}
                                selectedModel={selectedModel}
                                modelOptions={MODEL_OPTIONS}
                                sessionId={backendConvIdRef.current}
                                user={user}
                            />
                        ))}

                    {showingAnalysis && !convLoading && <AnalysisBubble currentStep={analysisStep} />}

                    {analysisResult && stage === 'results' && !convLoading && messages.length > 0 &&
                        !messages.some(m => m.role === 'assistant' && m.content?.includes('## 🩺 Curezy AI Health Assessment')) && (
                            /* Fallback only if the trigger message is missing from history */
                            <>
                                <AnalysisCard
                                    {...analysisResult}
                                    modelLabel={MODEL_OPTIONS.find(m => m.key === selectedModel)?.label}
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
                <div className="px-4 pb-4 pt-2 z-20">
                    <div className="max-w-3xl mx-auto">

                        {/* Quick chips */}
                        {chips.length > 0 && !showingAnalysis && stage !== 'results' && (
                            <div className="flex flex-wrap gap-1.5 mb-3">
                                {chips.map(chip => (
                                    <button key={chip} onClick={() => handleSend(chip)} disabled={loading}
                                        className="text-[12px] px-3 py-1.5 rounded-full border border-[#3a3a3a] text-[#999] hover:bg-[#2f2f2f] hover:text-[#ddd] hover:border-[#555] transition-colors disabled:opacity-40">
                                        {chip}
                                    </button>
                                ))}
                            </div>
                        )}

                        {/* Input container */}
                        {!showingAnalysis && (
                            <div className="bg-[#2f2f2f] border border-[#3a3a3a] rounded-2xl focus-within:border-[#555] transition-colors">
                                {/* Textarea row */}
                                <div className="flex items-end gap-2 px-3 pt-3 pb-2">
                                    <AttachDropdown backendConvId={backendConvIdRef.current} onUploadDone={handleUploadDone} />
                                    <textarea
                                        value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKeyDown}
                                        placeholder={stage === 'results' ? 'Ask a follow-up question...' : 'Describe your symptoms...'}
                                        rows={1} disabled={loading || convLoading}
                                        className="flex-1 bg-transparent text-[14px] resize-none focus:outline-none text-[#ececec] placeholder-[#666] max-h-36 disabled:opacity-50 leading-relaxed"
                                        style={{ minHeight: '24px' }}
                                    />
                                </div>
                                {/* Bottom bar: model selector + actions */}
                                <div className="flex items-center justify-between px-3 pb-2.5">
                                    <ModelSelector selectedModel={selectedModel} onSelect={setSelectedModel} />
                                    <div className="flex items-center gap-1">
                                        <button onClick={toggleRecording} title={isRecording ? 'Stop' : 'Voice input'}
                                            className={`p-1.5 rounded-lg transition-colors ${isRecording ? 'text-red-400 animate-pulse' : 'text-[#666] hover:text-[#aaa]'}`}>
                                            {isRecording ? <MicOff size={18} /> : <Mic size={18} />}
                                        </button>
                                        <button onClick={() => handleSend()} disabled={loading || convLoading || !input.trim()}
                                            className="bg-white text-[#212121] p-1.5 rounded-lg transition-all disabled:opacity-20 disabled:cursor-not-allowed hover:bg-[#e5e5e5]">
                                            <ArrowUp size={16} strokeWidth={2.5} />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        )}

                        <p className="text-center text-[11px] text-[#555] mt-2.5">
                            Curezy AI is not a substitute for professional medical advice
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
