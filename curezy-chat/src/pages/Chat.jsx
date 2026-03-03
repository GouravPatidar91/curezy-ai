import { useState, useEffect, useRef, useCallback } from 'react'
import { Send, Settings2, Mic, MicOff, Phone, Plus, X, FileText, Loader2, Check, Image, Upload, Cpu } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { supabase } from '../config/supabase'
import { startChat, sendMessage, uploadReport } from '../api/client'
import Sidebar from '../components/Sidebar'
import MessageBubble from '../components/MessageBubble'
import AnalysisCard from '../components/AnalysisCard'
import DoctorReferral from '../components/DoctorReferral'

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

const STEPS = [
    { id: 'initializing', label: 'Initializing models' },
    { id: 'processing', label: 'Processing your inputs' },
    { id: 'diagnosing', label: 'Starting diagnosis' },
    { id: 'done', label: 'Analysis complete' },
]

function AnalysisBubble({ currentStep }) {
    const idx = STEPS.findIndex(s => s.id === currentStep)
    return (
        <div className="flex items-start gap-3 mb-4">
            <div className="w-8 h-8 rounded-2xl bg-accent-purple flex items-center justify-center text-white text-sm flex-shrink-0">🩺</div>
            <div className="bg-surface border border-white/10 rounded-2xl rounded-bl-none px-5 py-4 shadow-sm max-w-sm">
                <p className="text-sm font-semibold text-white mb-3">🩺 Curezy Medical Council</p>
                <div className="flex justify-center gap-4 mb-4">
                    {['🧠', '🔬', '💊'].map((icon, i) => (
                        <div key={i} className={`w-10 h-10 rounded-xl flex items-center justify-center text-lg transition-all ${currentStep === 'done' ? 'bg-green-50' : 'bg-accent-blue/10 animate-pulse'}`}
                            style={{ animationDelay: `${i * 200}ms` }}>
                            {currentStep === 'done' ? '✅' : icon}
                        </div>
                    ))}
                </div>
                <div className="space-y-2">
                    {STEPS.map((step, i) => {
                        const done = i < idx || currentStep === 'done'
                        const active = i === idx && currentStep !== 'done'
                        return (
                            <div key={step.id} className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-medium transition-all ${done ? 'bg-green-500/20 text-green-300' : active ? 'bg-accent-blue/10 text-accent-blue' : 'text-gray-500'}`}>
                                <span className={`w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0 ${done ? 'bg-green-500 text-white' : active ? 'bg-accent-blue text-white' : 'bg-white/20'}`}>
                                    {done ? <Check size={9} /> : active ? <Loader2 size={9} className="animate-spin" /> : null}
                                </span>
                                {step.label}
                                {done && <span className="ml-auto text-green-500">✓</span>}
                                {active && <span className="ml-auto animate-pulse">…</span>}
                            </div>
                        )
                    })}
                </div>
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
            const nextStage = res.data?.stage || stage

            setStage(nextStage)

            if (nextStage === 'analyzing' || res.data?.analysis) {
                setShowingAnalysis(true)
                startAnalysisSequence()
                const aiMsg = { role: 'assistant', content: reply, timestamp: new Date().toISOString() }
                setMessages(prev => [...prev, aiMsg])
                await dbInsertMessage(user?.id, convId, 'assistant', reply)   // ← stable convId

                if (res.data?.analysis) {
                    setAnalysisResult({ analysis: res.data.analysis, confidence: res.data.confidence, dataGaps: res.data.data_gaps })
                    clearInterval(analysisTimerRef.current)
                    setAnalysisStep('done')
                    setTimeout(() => { setShowingAnalysis(false); setStage('results'); setShowReferral(true) }, 1500)
                }
            } else {
                const aiMsg = { role: 'assistant', content: reply, timestamp: new Date().toISOString() }
                setMessages(prev => [...prev, aiMsg])
                await dbInsertMessage(user?.id, convId, 'assistant', reply)   // ← stable convId
            }

            await dbTouchConversation(user?.id, convId)                        // ← stable convId
            setRefreshSidebar(n => n + 1)
        } catch (err) {
            console.error('[Chat] response handling error:', err)
            setMessages(prev => [...prev, { role: 'assistant', content: 'Something went wrong. Please try again.', timestamp: new Date().toISOString() }])
        }
        setLoading(false)
    }, [input, loading, convId, stage, messages, user?.id, startAnalysisSequence, bootBackendSession])

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
                        <MessageBubble key={`${msg.role}-${i}-${msg.timestamp}`} message={msg} />
                    ))}

                    {showingAnalysis && !convLoading && <AnalysisBubble currentStep={analysisStep} />}

                    {analysisResult && stage === 'results' && !convLoading && (
                        <AnalysisCard
                            analysis={analysisResult.analysis}
                            confidence={analysisResult.confidence}
                            dataGaps={analysisResult.dataGaps}
                        />
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