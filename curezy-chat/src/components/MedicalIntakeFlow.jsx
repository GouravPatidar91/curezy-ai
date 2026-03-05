import { useState, useRef, useCallback } from 'react'
import { Upload, X, ChevronRight, Check, Loader2, FileText, Image as ImageIcon, AlertCircle, Mic, MicOff } from 'lucide-react'
import { stageSubmit, skipStage, uploadReport } from '../api/client'

// ── Shared UI primitives ──────────────────────────────────────────────

function StageHeader({ title, subtitle, step }) {
    return (
        <div className="mb-6 text-center">
            {step && (
                <span className="inline-block text-xs font-semibold text-primary-500 bg-primary-50 px-3 py-1 rounded-full mb-3">
                    {step}
                </span>
            )}
            <h2 className="text-xl font-bold text-gray-900 mb-1">{title}</h2>
            {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
        </div>
    )
}

function ContinueBtn({ onClick, disabled, label = 'Continue', loading }) {
    return (
        <button
            onClick={onClick}
            disabled={disabled || loading}
            className="w-full mt-6 flex items-center justify-center gap-2 bg-primary-600 hover:bg-primary-700 active:bg-primary-800 text-white py-3 rounded-2xl font-semibold text-sm transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-sm"
        >
            {loading ? <Loader2 size={18} className="animate-spin" /> : null}
            {label}
            {!loading && <ChevronRight size={16} />}
        </button>
    )
}

function Chip({ label, selected, onClick, multi = true }) {
    return (
        <button
            onClick={onClick}
            className={`px-3.5 py-2 rounded-xl text-sm font-medium border transition-all select-none ${selected
                ? 'bg-primary-600 text-white border-primary-600 shadow-sm'
                : 'bg-white text-gray-700 border-gray-200 hover:border-primary-400 hover:text-primary-600'
                }`}
        >
            {multi && selected ? <span className="mr-1">✓</span> : null}
            {label}
        </button>
    )
}

// ── Stage 1: Chief Complaint ──────────────────────────────────────────

function Stage1ChiefComplaint({ convId, onNext, setLoading, selectedModel }) {
    const [value, setValue] = useState('')
    const [recording, setRecording] = useState(false)
    const recRef = useRef(null)

    const toggleVoice = () => {
        if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) return
        if (recording) { recRef.current?.stop(); setRecording(false); return }
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition
        const r = new SR(); r.lang = 'en-IN'; r.continuous = false; r.interimResults = false
        r.onresult = e => setValue(p => p ? p + ' ' + e.results[0][0].transcript : e.results[0][0].transcript)
        r.onend = () => setRecording(false)
        r.start(); recRef.current = r; setRecording(true)
    }

    const submit = async () => {
        if (!value.trim()) return
        setLoading(true)
        try { await stageSubmit(convId, 'chief_complaint', { chief_complaint: value.trim() }, selectedModel) }
        catch (e) { console.error(e) }
        onNext(value.trim())
    }

    return (
        <div className="animate-fadeIn">
            <StageHeader
                step="Stage 1 of 8"
                title="What brings you in today?"
                subtitle="Describe your main symptom or concern in your own words"
            />
            <div className="relative">
                <textarea
                    value={value}
                    onChange={e => setValue(e.target.value)}
                    placeholder="e.g. I've had a sharp pain in my chest for 3 days, it gets worse when I breathe deeply…"
                    rows={4}
                    className="w-full bg-gray-50 border border-gray-200 rounded-2xl px-4 py-3 text-sm text-gray-800 resize-none focus:outline-none focus:border-primary-400 focus:ring-2 focus:ring-primary-50 transition-all"
                />
                <button
                    onClick={toggleVoice}
                    className={`absolute bottom-3 right-3 p-2 rounded-xl transition-all ${recording ? 'bg-red-50 text-red-500 animate-pulse' : 'text-gray-400 hover:text-primary-600'}`}
                >
                    {recording ? <MicOff size={16} /> : <Mic size={16} />}
                </button>
            </div>
            <ContinueBtn onClick={submit} disabled={value.trim().length < 5} />
        </div>
    )
}

// ── Stage 2: Symptom Detail ───────────────────────────────────────────

const LOCATIONS = ['Head', 'Neck', 'Chest', 'Abdomen', 'Back', 'Left Arm', 'Right Arm', 'Left Leg', 'Right Leg', 'Whole Body']
const CHARACTERS = ['Sharp', 'Dull', 'Burning', 'Throbbing', 'Stabbing', 'Cramping', 'Pressure', 'Aching']

function Stage2SymptomDetail({ convId, onNext, setLoading, selectedModel }) {
    const [location, setLocation] = useState(null)
    const [character, setCharacter] = useState([])
    const [severity, setSeverity] = useState(5)

    const toggleChar = c => setCharacter(prev => prev.includes(c) ? prev.filter(x => x !== c) : [...prev, c])

    const submit = async () => {
        const data = { location, character: character.join(', '), severity }
        setLoading(true)
        try { await stageSubmit(convId, 'symptom_detail', data, selectedModel) } catch (e) { console.error(e) }
        onNext(data)
    }

    const severityColor = severity <= 3 ? 'text-green-600' : severity <= 6 ? 'text-yellow-600' : 'text-red-600'

    return (
        <div className="animate-fadeIn">
            <StageHeader step="Stage 2 of 8" title="Tell us more about the symptom" />

            <div className="mb-5">
                <label className="block text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wide">Location</label>
                <div className="flex flex-wrap gap-2">
                    {LOCATIONS.map(l => (
                        <Chip key={l} label={l} selected={location === l} multi={false} onClick={() => setLocation(l === location ? null : l)} />
                    ))}
                </div>
            </div>

            <div className="mb-5">
                <label className="block text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wide">Character (select all that apply)</label>
                <div className="flex flex-wrap gap-2">
                    {CHARACTERS.map(c => (
                        <Chip key={c} label={c} selected={character.includes(c)} onClick={() => toggleChar(c)} />
                    ))}
                </div>
            </div>

            <div className="mb-2">
                <label className="block text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wide">
                    Severity — <span className={`text-base font-bold ${severityColor}`}>{severity}/10</span>
                </label>
                <input
                    type="range" min={1} max={10} value={severity}
                    onChange={e => setSeverity(Number(e.target.value))}
                    className="w-full accent-primary-600"
                />
                <div className="flex justify-between text-xs text-gray-400 mt-1">
                    <span>Mild (1)</span><span>Moderate (5)</span><span>Severe (10)</span>
                </div>
            </div>

            <ContinueBtn onClick={submit} disabled={!location} />
        </div>
    )
}

// ── Stage 3: Associated Symptoms ─────────────────────────────────────

const ASSOCIATED_OPTS = [
    'Fever', 'Nausea', 'Vomiting', 'Fatigue', 'Dizziness', 'Headache',
    'Shortness of breath', 'Loss of appetite', 'Night sweats', 'Weight loss',
    'Cough', 'Diarrhea', 'Constipation', 'Swelling', 'Rash', 'None of these'
]

function Stage3Associated({ convId, onNext, setLoading, selectedModel }) {
    const [selected, setSelected] = useState([])
    const toggle = opt => {
        if (opt === 'None of these') { setSelected(['None of these']); return }
        setSelected(prev => {
            const without = prev.filter(x => x !== 'None of these')
            return without.includes(opt) ? without.filter(x => x !== opt) : [...without, opt]
        })
    }

    const submit = async () => {
        setLoading(true)
        try { await stageSubmit(convId, 'associated_symptoms', { associated: selected }, selectedModel) } catch (e) { console.error(e) }
        onNext(selected)
    }

    return (
        <div className="animate-fadeIn">
            <StageHeader step="Stage 3 of 8" title="Any associated symptoms?" subtitle="Select everything you're experiencing alongside your main complaint" />
            <div className="flex flex-wrap gap-2 mb-2">
                {ASSOCIATED_OPTS.map(opt => (
                    <Chip key={opt} label={opt} selected={selected.includes(opt)} onClick={() => toggle(opt)} />
                ))}
            </div>
            <ContinueBtn onClick={submit} disabled={selected.length === 0} />
        </div>
    )
}

// ── Stage 4: Timeline ─────────────────────────────────────────────────

const ONSET_OPTS = ['Sudden (minutes)', 'Gradual (hours)', 'Slowly over days', 'Weeks / chronic']
const PATTERN_OPTS = ['Constant', 'Comes and goes', 'Getting worse', 'Getting better', 'Worse at night']
const DURATION_UNITS = ['Hours', 'Days', 'Weeks', 'Months']

function Stage4Timeline({ convId, onNext, setLoading, selectedModel }) {
    const [durationValue, setDurationValue] = useState('')
    const [durationUnit, setDurationUnit] = useState('Days')
    const [onset, setOnset] = useState(null)
    const [pattern, setPattern] = useState(null)

    const submit = async () => {
        const data = {
            duration: `${durationValue} ${durationUnit}`,
            duration_value: durationValue,
            duration_unit: durationUnit,
            onset,
            pattern
        }
        setLoading(true)
        try { await stageSubmit(convId, 'timeline', data, selectedModel) } catch (e) { console.error(e) }
        onNext(data)
    }

    return (
        <div className="animate-fadeIn">
            <StageHeader step="Stage 4 of 8" title="When did this start?" />

            <div className="mb-5">
                <label className="block text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wide">Duration</label>
                <div className="flex gap-2">
                    <input
                        type="number" min={1} value={durationValue}
                        onChange={e => setDurationValue(e.target.value)}
                        placeholder="e.g. 3"
                        className="flex-1 bg-gray-50 border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-primary-400"
                    />
                    <select
                        value={durationUnit} onChange={e => setDurationUnit(e.target.value)}
                        className="bg-gray-50 border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-primary-400"
                    >
                        {DURATION_UNITS.map(u => <option key={u}>{u}</option>)}
                    </select>
                </div>
            </div>

            <div className="mb-5">
                <label className="block text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wide">Onset</label>
                <div className="flex flex-wrap gap-2">
                    {ONSET_OPTS.map(o => <Chip key={o} label={o} selected={onset === o} multi={false} onClick={() => setOnset(o === onset ? null : o)} />)}
                </div>
            </div>

            <div className="mb-2">
                <label className="block text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wide">Pattern</label>
                <div className="flex flex-wrap gap-2">
                    {PATTERN_OPTS.map(p => <Chip key={p} label={p} selected={pattern === p} multi={false} onClick={() => setPattern(p === pattern ? null : p)} />)}
                </div>
            </div>

            <ContinueBtn onClick={submit} disabled={!durationValue || !onset} />
        </div>
    )
}

// ── Stage 5: Medical History ─────────────────────────────────────────

const HISTORY_OPTS = [
    'Diabetes', 'Hypertension', 'Asthma', 'Heart disease', 'Thyroid disorder',
    'Kidney disease', 'Liver disease', 'Cancer', 'Arthritis', 'Epilepsy',
    'Depression / Anxiety', 'COPD', 'None'
]

function Stage5History({ convId, onNext, setLoading, selectedModel }) {
    const [selected, setSelected] = useState([])
    const [other, setOther] = useState('')
    const toggle = opt => {
        if (opt === 'None') { setSelected(['None']); return }
        setSelected(prev => {
            const without = prev.filter(x => x !== 'None')
            return without.includes(opt) ? without.filter(x => x !== opt) : [...without, opt]
        })
    }

    const submit = async () => {
        const combined = [...selected.filter(x => x !== 'None'), other].filter(Boolean).join(', ') || 'None'
        setLoading(true)
        try { await stageSubmit(convId, 'history', { history: combined }, selectedModel) } catch (e) { console.error(e) }
        onNext(combined)
    }

    return (
        <div className="animate-fadeIn">
            <StageHeader step="Stage 5 of 8" title="Medical history" subtitle="Select any known conditions" />
            <div className="flex flex-wrap gap-2 mb-4">
                {HISTORY_OPTS.map(opt => <Chip key={opt} label={opt} selected={selected.includes(opt)} onClick={() => toggle(opt)} />)}
            </div>
            {!selected.includes('None') && (
                <input
                    value={other} onChange={e => setOther(e.target.value)}
                    placeholder="Other conditions (optional)…"
                    className="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-primary-400 mb-2"
                />
            )}
            <ContinueBtn onClick={submit} disabled={selected.length === 0} />
        </div>
    )
}

// ── Stage 6: Medications ──────────────────────────────────────────────

function Stage6Medications({ convId, onNext, setLoading, selectedModel }) {
    const [meds, setMeds] = useState([])
    const [input, setInput] = useState('')

    const addMed = () => {
        const trimmed = input.trim()
        if (trimmed && !meds.includes(trimmed)) setMeds(prev => [...prev, trimmed])
        setInput('')
    }
    const removeMed = m => setMeds(prev => prev.filter(x => x !== m))

    const handleKey = e => { if (e.key === 'Enter') { e.preventDefault(); addMed() } }

    const handle = async (skip = false) => {
        setLoading(true)
        if (skip) {
            try { await skipStage(convId, 'medications', selectedModel) } catch (e) { console.error(e) }
            onNext([], true)
        } else {
            if (input.trim()) addMed()
            const allMeds = [...meds, input.trim()].filter(Boolean)
            try { await stageSubmit(convId, 'medications', { medications: allMeds }, selectedModel) } catch (e) { console.error(e) }
            onNext(allMeds, false)
        }
    }

    return (
        <div className="animate-fadeIn">
            <StageHeader step="Stage 6 of 8" title="Current medications" subtitle="List any medications or supplements you're taking" />

            <div className="flex gap-2 mb-3">
                <input
                    value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKey}
                    placeholder="Type medication name, press Enter…"
                    className="flex-1 bg-gray-50 border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-primary-400"
                />
                <button onClick={addMed} disabled={!input.trim()}
                    className="bg-primary-600 text-white px-4 py-2.5 rounded-xl text-sm font-medium disabled:opacity-40 hover:bg-primary-700 transition-colors">
                    Add
                </button>
            </div>

            {meds.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-4">
                    {meds.map(m => (
                        <span key={m} className="flex items-center gap-1.5 bg-blue-50 text-blue-700 border border-blue-200 px-3 py-1.5 rounded-full text-sm font-medium">
                            💊 {m}
                            <button onClick={() => removeMed(m)} className="hover:text-red-500 transition-colors"><X size={12} /></button>
                        </span>
                    ))}
                </div>
            )}

            <ContinueBtn onClick={() => handle(false)} disabled={meds.length === 0 && !input.trim()} label="Continue" />
            <button onClick={() => handle(true)} className="w-full mt-2 text-sm text-gray-400 hover:text-gray-600 transition-colors py-2">
                I take no medications →
            </button>
        </div>
    )
}

// ── Stage 7: Doctor Reports ───────────────────────────────────────────

function Stage7Reports({ convId, onNext, setLoading, onUploadResult, selectedModel }) {
    const [file, setFile] = useState(null)
    const [dragging, setDragging] = useState(false)
    const [uploading, setUploading] = useState(false)
    const [result, setResult] = useState(null)
    const inputRef = useRef(null)

    const handleFile = f => {
        const allowed = ['.pdf', '.txt', '.docx', '.jpg', '.jpeg', '.png']
        const ext = '.' + f.name.split('.').pop().toLowerCase()
        if (!allowed.includes(ext)) { alert('Only PDF, TXT, DOCX, JPG, PNG files are accepted.'); return }
        setFile(f)
    }

    const uploadFile = async () => {
        if (!file) return
        setUploading(true)
        try {
            const res = await uploadReport(convId, file)
            setResult(res.data)
            onUploadResult && onUploadResult(res.data)
        } catch (e) {
            console.error(e)
            setResult({ success: false, message: 'Upload failed. Please try again.' })
        }
        setUploading(false)
    }

    const proceed = async (skip = false) => {
        setLoading(true)
        if (skip) {
            try { await skipStage(convId, 'reports', selectedModel) } catch (e) { console.error(e) }
            onNext(null, true)
        } else {
            onNext(result, false)
        }
    }

    return (
        <div className="animate-fadeIn">
            <StageHeader step="Stage 7 of 8" title="Doctor reports & lab results"
                subtitle="Upload any reports, prescriptions, or lab results. Our AI will extract the medical information automatically." />

            {!result ? (
                <>
                    <div
                        onDragOver={e => { e.preventDefault(); setDragging(true) }}
                        onDragLeave={() => setDragging(false)}
                        onDrop={e => { e.preventDefault(); setDragging(false); const f = e.dataTransfer.files[0]; if (f) handleFile(f) }}
                        onClick={() => inputRef.current?.click()}
                        className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${dragging ? 'border-primary-400 bg-primary-50' : 'border-gray-200 hover:border-primary-300 hover:bg-gray-50'}`}
                    >
                        <input ref={inputRef} type="file" accept=".pdf,.txt,.docx,.jpg,.jpeg,.png" className="hidden"
                            onChange={e => { const f = e.target.files[0]; if (f) handleFile(f) }} />
                        <div className="w-12 h-12 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-3">
                            <Upload size={24} className="text-gray-400" />
                        </div>
                        <p className="text-sm font-medium text-gray-600 mb-1">Drop file here or click to browse</p>
                        <p className="text-xs text-gray-400">PDF, TXT, DOCX, JPG, PNG</p>
                    </div>

                    {file && (
                        <div className="mt-3 flex items-center justify-between bg-blue-50 border border-blue-100 rounded-xl px-4 py-3">
                            <div className="flex items-center gap-2 text-sm text-blue-700">
                                <FileText size={16} />
                                <span className="font-medium truncate max-w-[200px]">{file.name}</span>
                            </div>
                            <button onClick={uploadFile} disabled={uploading}
                                className="flex items-center gap-1.5 bg-primary-600 hover:bg-primary-700 text-white px-3 py-1.5 rounded-lg text-xs font-medium disabled:opacity-50 transition-colors">
                                {uploading ? <Loader2 size={13} className="animate-spin" /> : null}
                                {uploading ? 'Uploading…' : 'Upload & Extract'}
                            </button>
                        </div>
                    )}
                </>
            ) : (
                <div className={`rounded-2xl border p-4 mb-2 ${result.success !== false ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                    {result.success !== false ? (
                        <>
                            <div className="flex items-center gap-2 text-green-700 font-semibold text-sm mb-3">
                                <Check size={16} /> {result.type === 'document' ? 'Report extracted successfully' : 'Image analyzed successfully'}
                            </div>
                            {result.parsed_fields && Object.keys(result.parsed_fields).length > 0 && (
                                <div className="grid grid-cols-2 gap-2">
                                    {Object.entries(result.parsed_fields).slice(0, 8).map(([k, v]) => (
                                        <div key={k} className="bg-white rounded-xl px-3 py-2 border border-green-100">
                                            <p className="text-xs text-gray-400 capitalize">{k.replace(/_/g, ' ')}</p>
                                            <p className="text-sm font-medium text-gray-800 truncate">{String(v)}</p>
                                        </div>
                                    ))}
                                </div>
                            )}
                            {result.image_findings?.findings && (
                                <div className="bg-white rounded-xl px-3 py-2 border border-green-100 mt-2">
                                    <p className="text-xs text-gray-400 mb-1">AI Findings</p>
                                    <p className="text-sm text-gray-800">{result.image_findings.findings}</p>
                                </div>
                            )}
                        </>
                    ) : (
                        <div className="flex items-center gap-2 text-red-600 text-sm">
                            <AlertCircle size={16} /> {result.message}
                        </div>
                    )}
                </div>
            )}

            {result && <ContinueBtn onClick={() => proceed(false)} label="Continue to next step" />}
            {!result && (
                <button onClick={() => proceed(true)} className="w-full mt-3 text-sm text-gray-400 hover:text-gray-600 transition-colors py-2">
                    I don't have any reports →
                </button>
            )}
        </div>
    )
}

// ── Stage 8: Smart Imaging ────────────────────────────────────────────

const SCAN_LABELS = {
    chest_xray: 'Chest X-Ray', mri_spine: 'MRI Spine', ct_head: 'CT Head',
    xray_musculoskeletal: 'Bone X-Ray', ct_abdomen: 'CT Abdomen', mammogram: 'Mammogram', medical_image: 'Medical Scan',
}

function Stage8Imaging({ convId, onNext, setLoading, imagingTypes, onUploadResult, selectedModel }) {
    const [file, setFile] = useState(null)
    const [uploading, setUploading] = useState(false)
    const [result, setResult] = useState(null)
    const [dragging, setDragging] = useState(false)
    const inputRef = useRef(null)
    const scanLabel = SCAN_LABELS[imagingTypes?.[0]] || 'Medical Scan'

    const handleFile = f => setFile(f)

    const uploadFile = async () => {
        if (!file) return
        setUploading(true)
        try {
            const res = await uploadReport(convId, file)
            setResult(res.data)
            onUploadResult && onUploadResult(res.data)
        } catch (e) {
            setResult({ success: false, message: 'Upload failed.' })
        }
        setUploading(false)
    }

    const proceed = async (skip = false) => {
        setLoading(true)
        if (skip) {
            try { await skipStage(convId, 'imaging', selectedModel) } catch (e) { console.error(e) }
            onNext(null, true)
        } else {
            onNext(result, false)
        }
    }

    return (
        <div className="animate-fadeIn">
            <div className="bg-amber-50 border border-amber-200 rounded-2xl px-4 py-3 mb-5 flex items-start gap-3">
                <AlertCircle size={18} className="text-amber-600 flex-shrink-0 mt-0.5" />
                <div>
                    <p className="text-sm font-semibold text-amber-800">Imaging recommended</p>
                    <p className="text-xs text-amber-600 mt-0.5">Based on your symptoms, our AI suggests a <strong>{scanLabel}</strong> would help with diagnosis.</p>
                </div>
            </div>

            <StageHeader step="Stage 8 of 8 (optional)" title={`Upload your ${scanLabel}`}
                subtitle="If you have a scan available, upload it for AI analysis. This is optional." />

            {!result ? (
                <>
                    <div
                        onDragOver={e => { e.preventDefault(); setDragging(true) }}
                        onDragLeave={() => setDragging(false)}
                        onDrop={e => { e.preventDefault(); setDragging(false); const f = e.dataTransfer.files[0]; if (f) handleFile(f) }}
                        onClick={() => inputRef.current?.click()}
                        className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${dragging ? 'border-primary-400 bg-primary-50' : 'border-gray-200 hover:border-primary-300 hover:bg-gray-50'}`}
                    >
                        <input ref={inputRef} type="file" accept=".jpg,.jpeg,.png,.dcm,.bmp,.tiff" className="hidden"
                            onChange={e => { const f = e.target.files[0]; if (f) handleFile(f) }} />
                        <div className="w-12 h-12 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-3">
                            <ImageIcon size={24} className="text-gray-400" />
                        </div>
                        <p className="text-sm font-medium text-gray-600 mb-1">Drop {scanLabel} image here</p>
                        <p className="text-xs text-gray-400">JPG, PNG, DICOM</p>
                    </div>

                    {file && (
                        <div className="mt-3 flex items-center justify-between bg-blue-50 border border-blue-100 rounded-xl px-4 py-3">
                            <div className="flex items-center gap-2 text-sm text-blue-700">
                                <ImageIcon size={16} />
                                <span className="font-medium truncate max-w-[200px]">{file.name}</span>
                            </div>
                            <button onClick={uploadFile} disabled={uploading}
                                className="flex items-center gap-1.5 bg-primary-600 hover:bg-primary-700 text-white px-3 py-1.5 rounded-lg text-xs font-medium disabled:opacity-50 transition-colors">
                                {uploading ? <Loader2 size={13} className="animate-spin" /> : null}
                                {uploading ? 'Analyzing…' : 'Upload & Analyze'}
                            </button>
                        </div>
                    )}
                </>
            ) : (
                <div className={`rounded-2xl border p-4 mb-2 ${result.success !== false ? 'bg-green-50 border-green-200' : 'bg-yellow-50 border-yellow-200'}`}>
                    {result.success !== false ? (
                        <>
                            <div className="flex items-center gap-2 text-green-700 font-semibold text-sm mb-2">
                                <Check size={16} /> {scanLabel} analyzed
                            </div>
                            {result.image_findings?.findings && (
                                <p className="text-sm text-gray-800">{result.image_findings.findings}</p>
                            )}
                        </>
                    ) : (
                        <div className="flex items-center gap-2 text-yellow-700 text-sm">
                            <AlertCircle size={16} /> Image saved. Will be included in analysis.
                        </div>
                    )}
                </div>
            )}

            {result && <ContinueBtn onClick={() => proceed(false)} label="Proceed to Analysis" />}
            {!result && (
                <button onClick={() => proceed(true)} className="w-full mt-3 text-sm text-gray-400 hover:text-gray-600 transition-colors py-2">
                    I don't have the scan — proceed anyway →
                </button>
            )}
        </div>
    )
}

// ── Stage 9: Council Analysis Progress ───────────────────────────────

const ANALYSIS_STEPS = [
    { id: 'initializing', label: 'Initializing models', icon: '⚙️' },
    { id: 'processing', label: 'Processing your inputs', icon: '📋' },
    { id: 'diagnosing', label: 'Starting diagnosis', icon: '🔬' },
    { id: 'done', label: 'Analysis complete', icon: '✅' },
]

function Stage9Analyzing({ currentStep }) {
    const stepIdx = ANALYSIS_STEPS.findIndex(s => s.id === currentStep)

    return (
        <div className="animate-fadeIn text-center py-4">
            <div className="w-16 h-16 bg-primary-50 rounded-3xl flex items-center justify-center mx-auto mb-5">
                <span className="text-3xl">🩺</span>
            </div>
            <h2 className="text-xl font-bold text-gray-900 mb-1">Curezy Medical Council</h2>
            <p className="text-sm text-gray-400 mb-6">3 AI doctors are analyzing your case in parallel</p>

            {/* Doctor avatars */}
            <div className="flex justify-center gap-6 mb-8">
                {['Dr. Gemma', 'Dr. OpenBio', 'Dr. Mistral'].map((doc, i) => (
                    <div key={doc} className="flex flex-col items-center gap-2">
                        <div className={`w-14 h-14 rounded-2xl flex items-center justify-center text-2xl transition-all duration-500 ${currentStep === 'done'
                            ? 'bg-green-50 ring-2 ring-green-400'
                            : 'bg-primary-50 ring-2 ring-primary-200 animate-pulse'
                            }`} style={{ animationDelay: `${i * 200}ms` }}>
                            {currentStep === 'done' ? '✅' : ['🧠', '🔬', '💊'][i]}
                        </div>
                        <span className="text-xs text-gray-500 font-medium">{doc}</span>
                    </div>
                ))}
            </div>

            {/* Steps */}
            <div className="text-left space-y-3 max-w-xs mx-auto">
                {ANALYSIS_STEPS.map((step, i) => {
                    const done = i < stepIdx || currentStep === 'done'
                    const active = i === stepIdx && currentStep !== 'done'
                    return (
                        <div key={step.id} className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-500 ${done ? 'bg-green-50' : active ? 'bg-primary-50' : 'bg-gray-50 opacity-50'
                            }`}>
                            <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold ${done ? 'bg-green-500 text-white' : active ? 'bg-primary-600 text-white' : 'bg-gray-200 text-gray-400'
                                }`}>
                                {done ? <Check size={12} /> : active ? <Loader2 size={12} className="animate-spin" /> : i + 1}
                            </div>
                            <span className={`text-sm font-medium ${done ? 'text-green-700' : active ? 'text-primary-700' : 'text-gray-400'}`}>
                                {step.label}
                            </span>
                            {done && <span className="ml-auto text-xs text-green-500 font-medium">Done</span>}
                            {active && <span className="ml-auto text-xs text-primary-500 font-medium animate-pulse">Running…</span>}
                        </div>
                    )
                })}
            </div>
        </div>
    )
}

// ── Master orchestrator ───────────────────────────────────────────────

const STAGE_ORDER = [
    'chief_complaint', 'symptom_detail', 'associated_symptoms',
    'timeline', 'history', 'medications', 'reports', 'imaging', 'analyzing'
]

export default function MedicalIntakeFlow({
    convId,
    initialStage = 'chief_complaint',
    imagingNeeded = false,
    imagingTypes = [],
    analysisStep = 'initializing',
    onAnalysisTriggered,
    onStageChange,
}) {
    const [localStage, setLocalStage] = useState(initialStage)
    const [loading, setLoading] = useState(false)

    const advanceTo = useCallback((nextStage) => {
        setLoading(false)
        setLocalStage(nextStage)
        onStageChange && onStageChange(nextStage)
    }, [onStageChange])

    const handleStageResponse = useCallback((res) => {
        if (!res) return
        const next = res.stage || res.data?.stage
        if (!next) return
        if (next === 'analyzing' || next === 'results') {
            onAnalysisTriggered && onAnalysisTriggered(res)
            advanceTo('analyzing')
        } else {
            advanceTo(next)
        }
    }, [advanceTo, onAnalysisTriggered])

    // Generic Next handler: submit yields res from API, advance accordingly
    const makeNext = (stage) => async (data, skipped) => {
        // The submit API call is already done by each stage component
        // We just move to the next logical stage
        const idx = STAGE_ORDER.indexOf(stage)
        let next = STAGE_ORDER[idx + 1] || 'analyzing'

        // Skip imaging if not needed
        if (next === 'imaging' && !imagingNeeded) next = 'analyzing'

        if (next === 'analyzing') {
            onAnalysisTriggered && onAnalysisTriggered()
        }

        // If a stage was skipped, call skipStage with selectedModel
        if (skipped) {
            try {
                await skipStage(convId, stage, selectedModel) // Pass selectedModel
            } catch (e) {
                console.error(`Error skipping stage ${stage}:`, e)
            }
        }
        advanceTo(next)
    }

    const sharedProps = { convId, setLoading, selectedModel } // Pass selectedModel to sharedProps

    return (
        <div className="w-full">
            {localStage === 'chief_complaint' && (
                <Stage1ChiefComplaint {...sharedProps} onNext={makeNext('chief_complaint')} />
            )}
            {localStage === 'symptom_detail' && (
                <Stage2SymptomDetail {...sharedProps} onNext={makeNext('symptom_detail')} />
            )}
            {localStage === 'associated_symptoms' && (
                <Stage3Associated {...sharedProps} onNext={makeNext('associated_symptoms')} />
            )}
            {localStage === 'timeline' && (
                <Stage4Timeline {...sharedProps} onNext={makeNext('timeline')} />
            )}
            {localStage === 'history' && (
                <Stage5History {...sharedProps} onNext={makeNext('history')} />
            )}
            {localStage === 'medications' && (
                <Stage6Medications {...sharedProps} onNext={makeNext('medications')} />
            )}
            {localStage === 'reports' && (
                <Stage7Reports {...sharedProps} onNext={makeNext('reports')} />
            )}
            {localStage === 'imaging' && (
                <Stage8Imaging {...sharedProps} onNext={makeNext('imaging')} imagingTypes={imagingTypes} />
            )}
            {localStage === 'analyzing' && (
                <Stage9Analyzing currentStep={analysisStep} />
            )}
        </div>
    )
}
