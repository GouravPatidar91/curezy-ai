import { useState, useEffect, useRef, useCallback } from 'react'
import { Send, Mic, MicOff, Phone, Plus, X, FileText, Loader2, Check, Image, Paperclip, ChevronDown, ArrowUp, Brain, Search, Activity, Heart, ShieldCheck, Menu, User } from 'lucide-react'
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
    basic_info: { label: 'Patient Info' },
    chief_complaint: { label: 'Chief Complaint' },
    onset: { label: 'Onset' },
    provocation: { label: 'Provocation' },
    quality: { label: 'Quality' },
    region: { label: 'Region' },
    severity: { label: 'Severity' },
    timing: { label: 'Timing' },
    associated_symptoms: { label: 'Associated symptoms' },
    history: { label: 'Medical History' },
    medications: { label: 'Medications' },
    allergies: { label: 'Allergies' },
    lifestyle: { label: 'Lifestyle' },
    family_history: { label: 'Family History' },
    red_flags: { label: 'Red Flags' },
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

const IDLE_SUGGESTIONS = [
    { label: 'Check Symptom', text: 'I have a fever', Icon: Activity, color: 'text-blue-400' },
    { label: 'Review Report', text: 'I want to upload a lab report', Icon: FileText, color: 'text-orange-400' },
    { label: 'Get Advice', text: 'I am feeling very tired', Icon: Heart, color: 'text-pink-400' },
    { label: 'More', text: 'I have other symptoms', Icon: Search, color: 'text-[#888]' },
]


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

function AttachDropdown({ backendConvId, onUploadDone, children, triggerClassName }) {
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
                className={triggerClassName || "p-1.5 rounded-lg text-[#666] hover:text-[#aaa] transition-colors"}
                title="Attach file"
            >
                {children || <Paperclip size={18} />}
            </button>
            {open && !mode && (
                <div className="absolute bottom-full left-0 mb-3 w-48 bg-[#2f2f2f] border border-[#3a3a3a] rounded-[20px] shadow-2xl z-50 py-2 flex flex-col">
                    <button onClick={() => handleChoose('img')} className="flex items-center gap-3 px-4 py-2.5 hover:bg-[#3a3a3a] transition-colors text-left text-[#ececec]">
                        <Image size={18} className="text-[#ececec]" />
                        <span className="text-[15px] font-medium">Add photos</span>
                    </button>
                    <button onClick={() => handleChoose('doc')} className="flex items-center gap-3 px-4 py-2.5 hover:bg-[#3a3a3a] transition-colors text-left text-[#ececec]">
                        <Paperclip size={18} className="text-[#ececec]" />
                        <span className="text-[15px] font-medium">Add files</span>
                    </button>
                </div>
            )}
            {open && mode && (
                <div className="absolute bottom-full left-0 mb-3 w-64 bg-[#2f2f2f] border border-[#3a3a3a] rounded-[20px] shadow-2xl z-50 p-3">
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
    basic_info: ['Male, 25', 'Female, 30', 'Male, 45', 'Female, 50', 'Prefer not to say'],
    onset: ['Just now', '1 hour ago', 'Today', 'Yesterday', 'A few days ago', 'Months ago'],
    provocation: ['Movement', 'Eating', 'Pressure', 'Resting', 'Coughing', 'Nothing makes it better'],
    quality: ['Sharp/Stabbing', 'Dull Ache', 'Burning', 'Throbbing', 'Pressure/Tightness', 'Cramping'],
    region: ['Chest', 'Abdomen', 'Head', 'Back', 'Left arm', 'Right leg', 'Localized', 'Spreading'],
    severity: ['Mild (2/10)', 'Moderate (5/10)', 'Severe (8/10)', 'Worst ever (10/10)'],
    timing: ['Constant', 'Comes and goes', 'Getting worse', 'Improved', 'Worse at night'],
    associated_symptoms: ['Fever', 'Nausea', 'Fatigue', 'Dizziness', 'Shortness of breath', 'Headache', 'None of these'],
    history: ['Diabetes', 'Hypertension', 'Asthma', 'Heart disease', 'No prior conditions'],
    medications: ['No medications', 'Paracetamol/Tylenol', 'Aspirin', 'Antacids', 'Prescription meds'],
    lifestyle: ['Non-smoker', 'Occasional smoker', 'Regular smoker', 'Non-drinker', 'Social drinker'],
    allergies: ['No allergies', 'Penicillin', 'Sulfa drugs', 'Peanuts', 'Latex'],
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

/**
 * Fetch the analysis_result stored directly in the conversations table.
 * This is the reliable fallback when the backend in-memory session is gone
 * (e.g. after a server restart or RunPod cold-start).
 */
async function dbLoadAnalysisResult(convId) {
    if (!convId) return null
    const { data, error } = await supabase
        .from('conversations')
        .select('analysis_result, stage')
        .eq('conversation_id', convId)
        .single()
    if (error) { console.warn('[DB] loadAnalysisResult:', error.message); return null }
    return data?.analysis_result || null
}

/**
 * Filter out greeting-only sessions so the idle canvas shows instead of a stale greeting.
 * A session is "greeting-only" if it has NO user messages whatsoever.
 * Returns the original array if real user messages exist, otherwise [].
 */
function filterGreetingOnly(msgs) {
    if (!msgs || !msgs.length) return []
    const hasUserMsg = msgs.some(m => m.role === 'user')
    if (!hasUserMsg) {
        console.log('[Chat] Session has no user messages — treating as idle (skipping greeting)')
        return []
    }
    return msgs
}

// ── DoctorReferral dismiss persistence (localStorage) ────────────────────
// Keyed per-conversation so dismissing on one chat never affects another.

function isReferralDismissed(convId) {
    if (!convId) return false
    return localStorage.getItem(`curezy_ref_dismissed_${convId}`) === '1'
}

function dismissReferral(convId) {
    if (!convId) return
    localStorage.setItem(`curezy_ref_dismissed_${convId}`, '1')
}

function clearReferralDismiss(convId) {
    if (!convId) return
    localStorage.removeItem(`curezy_ref_dismissed_${convId}`)
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

/**
 * Build a professional consultation title from analysis results.
 * Uses top 1-2 diagnosed conditions to create a concise clinical label.
 * Examples:
 *   "Dengue Fever — Health Assessment"
 *   "Viral Fever & Typhoid — Health Assessment"
 *   "Chest Pain — Health Assessment"
 */
function generateConsultationTitle(normAnalysis) {
    try {
        const conditions = normAnalysis?.top_3_conditions || normAnalysis?.conditions || []
        if (!conditions.length) return null

        // Take top 1-2 conditions by probability
        const sorted = [...conditions].sort((a, b) => (b.probability ?? 0) - (a.probability ?? 0))
        const top = sorted.slice(0, 2).map(c => c.condition).filter(Boolean)
        if (!top.length) return null

        const conditionStr = top.join(' & ')
        return `${conditionStr} — Health Assessment`
    } catch {
        return null
    }
}


// ── Main Chat component ───────────────────────────────────────────────

export default function Chat() {
    const { user } = useAuth()
    const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false)
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
            const firstStage = res.data?.stage || 'chief_complaint'

            if (!newBackendId) throw new Error('No conversation ID from backend')

            backendConvIdRef.current = newBackendId
            setConvId(newBackendId)
            setStage(firstStage)
            // ✅ No greeting pushed — idle canvas shows immediately
            await dbUpsertConversation(user?.id, newBackendId, 'New Consultation')
            setRefreshSidebar(n => n + 1)
        } catch (err) {
            console.error('[Chat] handleNewChat failed:', err)
            // Fallback: generate a local temp ID and show idle canvas
            const fallbackId = `temp_${Date.now()}`
            setConvId(fallbackId)
            backendConvIdRef.current = fallbackId
            // Still no greeting — let the idle canvas handle it
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
                            let fetchedMessages = res.data.messages || []
                            fetchedMessages = filterGreetingOnly(fetchedMessages)
                            if (fetchedMessages.length > 0) {
                                setMessages(fetchedMessages)
                            } else {
                                let localMsgs = await dbLoadMessages(convId)
                                localMsgs = filterGreetingOnly(localMsgs)
                                setMessages(localMsgs)
                            }
                            setStage(res.data.stage || 'chief_complaint')
                            if (res.data.analysis_result) {
                                const ar = res.data.analysis_result
                                setAnalysisResult({
                                    analysis: normalizeAnalysis(ar.analysis || ar),
                                    confidence: ar.confidence,
                                    dataGaps: ar.data_gaps
                                })
                                if (!isReferralDismissed(convId)) setShowReferral(true)
                            }
                        } else {
                            // Fallback to basic message loading if resumeChat fails
                            let msgs = await dbLoadMessages(convId)
                            msgs = filterGreetingOnly(msgs)
                            setMessages(msgs)
                            const hasResults = msgs.some(m => m.role === 'assistant' && (m.content.includes('diagnosis') || m.content.includes('condition')))
                            const restoredStage = hasResults ? 'results' : msgs.length > 0 ? 'chief_complaint' : 'greeting'
                            setStage(restoredStage)
                            // Even if resumeChat failed, load the saved analysis result directly from DB
                            if (restoredStage === 'results' || hasResults) {
                                const ar = await dbLoadAnalysisResult(convId)
                                if (ar) {
                                    console.log('[Chat] Restored analysis_result from DB (resume no-result path)')
                                    setAnalysisResult({
                                        analysis: normalizeAnalysis(ar.analysis || ar),
                                        confidence: ar.confidence,
                                        dataGaps: ar.data_gaps
                                    })
                                    if (!isReferralDismissed(convId)) setShowReferral(true)
                                }
                            }
                        }
                    } catch (e) {
                        console.warn('[Chat] resumeChat failed, fallback to local restore:', e)
                        let msgs = await dbLoadMessages(convId)
                        msgs = filterGreetingOnly(msgs)
                        setMessages(msgs)
                        const hasResults = msgs.some(m => m.role === 'assistant' && (m.content.includes('diagnosis') || m.content.includes('condition')))
                        const restoredStage = hasResults ? 'results' : msgs.length > 0 ? 'chief_complaint' : 'greeting'
                        setStage(restoredStage)
                        // Fetch analysis result directly from Supabase — backend memory may have been lost
                        if (restoredStage === 'results' || hasResults) {
                            const ar = await dbLoadAnalysisResult(convId)
                            if (ar) {
                                console.log('[Chat] Restored analysis_result from DB (resumeChat catch path)')
                                setAnalysisResult({
                                    analysis: normalizeAnalysis(ar.analysis || ar),
                                    confidence: ar.confidence,
                                    dataGaps: ar.data_gaps
                                })
                                if (!isReferralDismissed(convId)) setShowReferral(true)
                            }
                        }
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
                const fetchedMessages = res.data.messages || []
                if (fetchedMessages.length > 0) {
                    setMessages(fetchedMessages)
                } else {
                    let localMsgs = await dbLoadMessages(selectedId)
                    localMsgs = filterGreetingOnly(localMsgs)
                    setMessages(localMsgs)
                }
                setStage(res.data.stage || 'chief_complaint')
                if (res.data.analysis_result) {
                    const ar = res.data.analysis_result
                    setAnalysisResult({
                        analysis: normalizeAnalysis(ar.analysis || ar),
                        confidence: ar.confidence,
                        dataGaps: ar.data_gaps
                    })
                    if (!isReferralDismissed(selectedId)) setShowReferral(true)
                }
            } else {
                let msgs = await dbLoadMessages(selectedId)
                msgs = filterGreetingOnly(msgs)
                setMessages(msgs)
                const hasResults = msgs.some(m => m.role === 'assistant' && (m.content.includes('diagnosis') || m.content.includes('condition')))
                const restoredStage = hasResults ? 'results' : msgs.length > 0 ? 'chief_complaint' : 'greeting'
                setStage(restoredStage)
                // Fetch saved analysis result directly from DB when backend can't provide it
                if (restoredStage === 'results' || hasResults) {
                    const ar = await dbLoadAnalysisResult(selectedId)
                    if (ar) {
                        console.log('[Chat] Restored analysis_result from DB (selectConv no-result path)')
                        setAnalysisResult({
                            analysis: normalizeAnalysis(ar.analysis || ar),
                            confidence: ar.confidence,
                            dataGaps: ar.data_gaps
                        })
                        if (!isReferralDismissed(selectedId)) setShowReferral(true)
                    }
                }
            }
        } catch (e) {
            console.warn('[Chat] handleSelectConv resumeChat failed:', e)
            let msgs = await dbLoadMessages(selectedId)
            msgs = filterGreetingOnly(msgs)
            setMessages(msgs)
            const hasResults = msgs.some(m => m.role === 'assistant' && (m.content.includes('diagnosis') || m.content.includes('condition')))
            const restoredStage = hasResults ? 'results' : msgs.length > 0 ? 'chief_complaint' : 'greeting'
            setStage(restoredStage)
            // Fetch analysis result directly from Supabase — backend memory may be gone
            if (restoredStage === 'results' || hasResults) {
                const ar = await dbLoadAnalysisResult(selectedId)
                if (ar) {
                    console.log('[Chat] Restored analysis_result from DB (selectConv catch path)')
                    setAnalysisResult({
                        analysis: normalizeAnalysis(ar.analysis || ar),
                        confidence: ar.confidence,
                        dataGaps: ar.data_gaps
                    })
                    if (!isReferralDismissed(selectedId)) setShowReferral(true)
                }
            }
        }

        const { data: conv } = await supabase.from('conversations').select('title').eq('conversation_id', selectedId).single()
        setConvTitle(conv?.title || 'Consultation')

        setConvLoading(false)
    }, [convId])

    const handleSend = useCallback(async (overrideText) => {
        const text = (overrideText || input).trim()
        if (!text || loading) return

        // If no active conversation (idle state), boot a new backend session first
        let activeConvId = convId
        if (!activeConvId) {
            setLoading(true)
            try {
                const res = await startChat()
                const newId = res.data?.conversation_id
                const greeting = res.data?.message
                const firstStage = res.data?.stage || 'chief_complaint'
                if (!newId) throw new Error('No conversation ID from backend')
                activeConvId = newId
                backendConvIdRef.current = newId
                setConvId(newId)
                setStage(firstStage)
                // Don't push the greeting — user already has their message typed
                await dbUpsertConversation(user?.id, newId, text.length > 48 ? text.slice(0, 48) + '...' : text)
                setConvTitle(text.length > 48 ? text.slice(0, 48) + '...' : text)
                setRefreshSidebar(n => n + 1)
            } catch (e) {
                console.error('[Chat] Auto-start on idle send failed:', e)
                setLoading(false)
                return
            }
        }

        setInput('')

        const userMsg = { role: 'user', content: text, timestamp: new Date().toISOString() }
        setMessages(prev => [...prev, userMsg])
        setLoading(true)

        if (stage === 'confirming') {
            setShowingAnalysis(true)
            startAnalysisSequence()
        }

        await dbInsertMessage(user?.id, activeConvId, 'user', text)

        const userMsgCount = messages.filter(m => m.role === 'user').length
        if (userMsgCount === 0 && convId) {
            // Only update title if this wasn't an idle-start (idle-start already set title above)
            const title = text.length > 48 ? text.slice(0, 48) + '...' : text
            setConvTitle(title)
            await dbUpsertConversation(user?.id, activeConvId, title)
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

                    // Auto-rename sidebar to professional clinical title based on top diagnosis
                    const clinicalTitle = generateConsultationTitle(normAnalysis)
                    if (clinicalTitle) {
                        setConvTitle(clinicalTitle)
                        await dbUpsertConversation(user?.id, activeConvId, clinicalTitle)
                        setRefreshSidebar(n => n + 1)
                    }
                    
                    const aiMsg = { role: 'assistant', content: reply, timestamp: new Date().toISOString() }
                    setMessages(prev => [...prev, aiMsg])
                    await dbInsertMessage(user?.id, activeConvId, 'assistant', reply)
                    
                    clearInterval(analysisTimerRef.current)
                    setAnalysisStep('done')
                    setTimeout(() => {
                        // Clear any previous dismiss flag — this is a brand-new analysis result
                        clearReferralDismiss(activeConvId)
                        setShowingAnalysis(false)
                        setStage('results')
                        setShowReferral(true)
                    }, 3000)
                } else {
                    const aiMsg = { role: 'assistant', content: reply, timestamp: new Date().toISOString() }
                    setMessages(prev => [...prev, aiMsg])
                    await dbInsertMessage(user?.id, activeConvId, 'assistant', reply)
                }
            } else {
                const aiMsg = { role: 'assistant', content: reply, timestamp: new Date().toISOString() }
                setMessages(prev => [...prev, aiMsg])
                await dbInsertMessage(user?.id, activeConvId, 'assistant', reply)
            }

            await dbTouchConversation(user?.id, activeConvId)
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

    // Idle = no messages yet (fresh chat or just started a new session)
    // convId may already be set (backend session booted) but no messages have been exchanged
    const isIdle = messages.length === 0 && !convLoading
    const chips = STAGE_CHIP_OPTIONS[stage] || []

    return (
        <div className="flex h-screen bg-[#171717] md:bg-[#212121] overflow-hidden relative text-[#ececec]">
            {/* Mobile Sidebar Overlay */}
            {mobileSidebarOpen && (
                <div className="md:hidden fixed inset-0 z-50 flex">
                    <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setMobileSidebarOpen(false)} />
                    <div className="relative w-[260px] h-full shadow-2xl">
                        <Sidebar user={user} currentConvId={convId} refreshTrigger={refreshSidebar} 
                            onNewChat={() => { handleNewChat(); setMobileSidebarOpen(false) }} 
                            onSelectConv={(id) => { handleSelectConv(id); setMobileSidebarOpen(false) }} />
                    </div>
                </div>
            )}
            
            {/* Desktop Sidebar */}
            <div className="hidden md:block h-full shrink-0">
                <Sidebar user={user} currentConvId={convId} refreshTrigger={refreshSidebar}
                    onNewChat={handleNewChat} onSelectConv={handleSelectConv} />
            </div>

            <div className="flex-1 flex flex-col min-w-0 relative z-10">

                {/* Mobile Header (ChatGPT Style) */}
                <div className="md:hidden bg-[#171717] px-4 py-2.5 flex items-center justify-between z-20">
                    <button onClick={() => setMobileSidebarOpen(true)} className="flex items-center justify-center w-10 h-10 rounded-full text-[#ECECEC] bg-[#2F2F2F] hover:bg-[#3A3A3A] transition-colors">
                        <Menu size={20} strokeWidth={2} />
                    </button>
                    
                    <button className="flex items-center gap-1.5 px-4 py-2 bg-transparent hover:bg-[#2F2F2F] rounded-xl transition-colors font-medium text-[16px] text-white">
                        Curezy AI <ChevronDown size={14} className="text-[#888] ml-0.5" />
                    </button>
                    
                    <button onClick={handleNewChat} className="flex items-center justify-center w-10 h-10 rounded-full text-[#ECECEC] bg-[#2F2F2F] hover:bg-[#3A3A3A] transition-colors">
                        <Plus size={20} strokeWidth={2} />
                    </button>
                </div>

                {/* Desktop Header */}
                <div className="hidden md:flex bg-[#212121] border-b border-[#2a2a2a] px-5 py-2 items-center justify-between z-20">
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

                    {isIdle && !convLoading && (
                        /* ── ChatGPT-style idle canvas ── */
                        <div className="flex flex-col items-center justify-center h-full select-none pb-4 md:pb-8">
                            {/* Brand heading */}
                            <div className="mb-8 md:mb-10 text-center">
                                <h2 className="text-[28px] md:text-[32px] font-semibold text-white tracking-tight leading-snug">
                                    What can I help with?
                                </h2>
                            </div>

                            {/* Centered input bar (Desktop only, mobile sticks to bottom) */}
                            <div className="hidden md:block w-full max-w-2xl px-4">
                                <div className="bg-[#2f2f2f] rounded-2xl border border-[#3a3a3a] focus-within:border-[#555] transition-colors shadow-xl">
                                    <div className="flex items-end gap-2 px-3 pt-3 pb-2">
                                        <AttachDropdown backendConvId={backendConvIdRef.current} onUploadDone={handleUploadDone} />
                                        <textarea
                                            value={input}
                                            onChange={e => setInput(e.target.value)}
                                            onKeyDown={handleKeyDown}
                                            placeholder="Ask Curezy AI"
                                            rows={1}
                                            disabled={loading}
                                            className="flex-1 bg-transparent text-[14px] resize-none focus:outline-none text-[#ececec] placeholder-[#888] max-h-36 disabled:opacity-50 leading-relaxed self-center"
                                            style={{ minHeight: '24px' }}
                                            autoFocus
                                        />
                                    </div>
                                    <div className="flex items-center justify-between px-3 pb-2.5">
                                        <ModelSelector selectedModel={selectedModel} onSelect={setSelectedModel} />
                                        <div className="flex items-center gap-1">
                                            <button onClick={toggleRecording} title={isRecording ? 'Stop' : 'Voice input'}
                                                className={`p-1.5 rounded-lg transition-colors ${isRecording ? 'text-red-400 animate-pulse' : 'text-[#666] hover:text-[#aaa]'}`}>
                                                {isRecording ? <MicOff size={18} /> : <Mic size={18} />}
                                            </button>
                                            <button onClick={() => handleSend()} disabled={loading || !input.trim()}
                                                className="bg-white text-[#212121] p-1.5 rounded-lg transition-all disabled:opacity-20 disabled:cursor-not-allowed hover:bg-[#e5e5e5]">
                                                <ArrowUp size={16} strokeWidth={2.5} />
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Symptom suggestion chips */}
                            <div className="grid grid-cols-2 md:flex md:flex-wrap justify-center gap-2 mt-8 md:mt-6 w-full max-w-[600px] mx-auto px-4 md:px-0">
                                {IDLE_SUGGESTIONS.map(s => (
                                    <button
                                        key={s.label}
                                        onClick={() => handleSend(s.text)}
                                        disabled={loading}
                                        className="flex items-center justify-center md:justify-start gap-2.5 w-full md:w-auto px-1 sm:px-4 py-3 md:py-2.5 border border-[#3a3a3a] rounded-full bg-transparent text-[#ececec] hover:bg-[#2f2f2f] transition-all disabled:opacity-40"
                                    >
                                        <s.Icon size={18} className={s.color} />
                                        <span className="font-medium text-[13px] md:text-[13px] truncate">{s.label}</span>
                                    </button>
                                ))}
                            </div>

                            <p className="text-center text-[11px] text-[#555] mt-6 hidden md:block">
                                Curezy AI is not a substitute for professional medical advice
                            </p>
                        </div>
                    )}

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
                        /* Only render the standalone fallback card when the trigger message is NOT in history.
                           When it IS present, MessageBubble renders the AnalysisCard inline — no duplicate needed.
                           dbLoadAnalysisResult() now ensures analysisResult is always populated on restore,
                           so MessageBubble will handle the inline render for all normal restore paths. */
                        !messages.some(m => m.role === 'assistant' && m.content?.includes('## 🩺 Curezy AI Health Assessment')) && (
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

                {/* Input area — shown at bottom always on mobile, and only when active on desktop */}
                <div className={`${isIdle ? 'md:hidden' : ''} px-4 pb-4 pt-2 z-20`}>
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
                            <div className="bg-[#2f2f2f] md:rounded-2xl rounded-[24px] border border-[#3a3a3a] focus-within:border-[#555] transition-colors md:shadow-sm">
                                {/* Top row (or only row on mobile) */}
                                <div className="flex items-center gap-2 px-2 py-1 md:items-end md:px-3 md:pt-3 md:pb-2">
                                    <div className="md:hidden">
                                        <AttachDropdown backendConvId={backendConvIdRef.current} onUploadDone={handleUploadDone} triggerClassName="p-1.5 text-[#888] bg-[#3a3a3a] hover:bg-[#444] rounded-full transition-colors flex items-center justify-center">
                                            <Plus size={18} />
                                        </AttachDropdown>
                                    </div>
                                    <div className="hidden md:block">
                                        <AttachDropdown backendConvId={backendConvIdRef.current} onUploadDone={handleUploadDone} />
                                    </div>
                                    <textarea
                                        value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKeyDown}
                                        placeholder={stage === 'results' ? 'Ask a follow-up question...' : 'Message Curezy AI'}
                                        rows={1} disabled={loading || convLoading}
                                        className="flex-1 bg-transparent text-[15px] md:text-[14px] resize-none focus:outline-none text-[#ececec] placeholder-[#888] max-h-36 disabled:opacity-50 leading-relaxed self-center py-2 md:py-0"
                                        style={{ minHeight: '28px' }}
                                    />
                                    <div className="flex md:hidden items-center pr-1 gap-1">
                                        {input.trim() ? (
                                            <button onClick={() => handleSend()} disabled={loading || convLoading}
                                                className="bg-white text-black p-1.5 rounded-full transition-all hover:bg-[#e5e5e5]">
                                                <ArrowUp size={16} strokeWidth={2.5} />
                                            </button>
                                        ) : (
                                            <button onClick={toggleRecording} className={`p-1.5 rounded-full transition-colors ${isRecording ? 'text-red-400 animate-pulse bg-red-400/10' : 'text-[#888] hover:text-white'}`}>
                                                {isRecording ? <MicOff size={18} /> : <Mic size={18} />}
                                            </button>
                                        )}
                                    </div>
                                </div>
                                {/* Bottom bar: model selector + actions (Desktop only) */}
                                <div className="hidden md:flex items-center justify-between px-3 pb-2.5">
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
                        <p className="text-center text-[11px] text-[#555] mt-2.5 hidden md:block">
                            Curezy AI is not a substitute for professional medical advice
                        </p>
                    </div>
                </div>
            </div>

            {showReferral && (
                <DoctorReferral
                    analysis={analysisResult?.analysis}
                    onClose={() => {
                        // Persist dismiss so popup never reappears for this conversation
                        dismissReferral(convId)
                        setShowReferral(false)
                    }}
                />
            )}
        </div>
    )
}
