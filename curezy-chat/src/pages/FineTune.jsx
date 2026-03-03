import { useState, useRef, useCallback, useEffect } from 'react'
import { Upload, FileText, Loader, CheckCircle, XCircle, Sparkles, RefreshCcw, ChevronDown, ChevronRight, AlertTriangle } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const PIPELINE_STEPS = [
    { key: 'parsing', emoji: '📄', label: 'Parsing File', pct: [0, 15] },
    { key: 'converting', emoji: '🤖', label: 'AI Conversion to JSONL', pct: [15, 55] },
    { key: 'filtering', emoji: '✅', label: 'Quality Filter', pct: [55, 60] },
    { key: 'training', emoji: '🔥', label: 'Fine-Tuning Models', pct: [60, 82] },
    { key: 'deploying', emoji: '🚀', label: 'Deploying to Ollama', pct: [82, 100] },
]

const ACCEPTED_TYPES = '.pdf,.txt,.csv,.docx,.png,.jpg,.jpeg,.tiff,.bmp'
const MAX_SIZE_MB = 50

function StepItem({ step, currentStage, progress }) {
    const stagePct = step.pct
    const isActive = progress >= stagePct[0] && progress < stagePct[1]
    const isDone = progress >= stagePct[1]
    const isPending = progress < stagePct[0]

    return (
        <div className={`flex items-center gap-3 py-3 px-4 rounded-xl transition-all duration-500 ${isActive ? 'bg-primary-50 border border-primary-200 shadow-sm' :
                isDone ? 'bg-green-50 border border-green-100' :
                    'bg-gray-50 border border-transparent opacity-60'
            }`}>
            <span className="text-xl flex-shrink-0">{step.emoji}</span>
            <div className="flex-1 min-w-0">
                <p className={`text-sm font-medium ${isActive ? 'text-primary-700' : isDone ? 'text-green-700' : 'text-gray-500'}`}>
                    {step.label}
                </p>
                {isActive && (
                    <div className="mt-1.5 h-1.5 bg-primary-100 rounded-full overflow-hidden">
                        <div
                            className="h-full bg-primary-500 rounded-full transition-all duration-700"
                            style={{ width: `${Math.min(100, ((progress - stagePct[0]) / (stagePct[1] - stagePct[0])) * 100)}%` }}
                        />
                    </div>
                )}
            </div>
            <div className="flex-shrink-0">
                {isDone && <CheckCircle size={18} className="text-green-500" />}
                {isActive && <Loader size={18} className="text-primary-500 animate-spin" />}
                {isPending && <div className="w-4 h-4 rounded-full border-2 border-gray-300" />}
            </div>
        </div>
    )
}

function JobHistory({ jobs, onSelect }) {
    if (!jobs.length) return null
    return (
        <div className="mt-8">
            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">Job History</h3>
            <div className="space-y-2">
                {jobs.slice(0, 10).map(job => (
                    <div
                        key={job.job_id}
                        onClick={() => onSelect(job.job_id)}
                        className="flex items-center gap-3 px-4 py-3 rounded-xl bg-white border border-gray-100 hover:border-primary-200 cursor-pointer transition-all"
                    >
                        <span className="text-lg">{
                            job.status === 'completed' ? '✅' :
                                job.status === 'failed' ? '❌' :
                                    job.status === 'running' ? '🔄' : '⏳'
                        }</span>
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-800 truncate">{job.file_name}</p>
                            <p className="text-xs text-gray-400">
                                {new Date(job.created_at).toLocaleString()} · {job.status}
                            </p>
                        </div>
                        {job.summary && (
                            <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-medium flex-shrink-0">
                                {job.summary.filtered_examples} examples
                            </span>
                        )}
                    </div>
                ))}
            </div>
        </div>
    )
}

export default function FineTune() {
    const { user } = useAuth()
    const [file, setFile] = useState(null)
    const [dragOver, setDragOver] = useState(false)
    const [uploading, setUploading] = useState(false)
    const [jobId, setJobId] = useState(null)
    const [job, setJob] = useState(null)
    const [jobs, setJobs] = useState([])
    const [error, setError] = useState(null)
    const fileRef = useRef()
    const pollRef = useRef()

    // Load job history on mount
    useEffect(() => {
        fetchJobs()
    }, [])

    // Poll active job
    useEffect(() => {
        if (!jobId) return
        pollRef.current = setInterval(() => pollJob(jobId), 2000)
        return () => clearInterval(pollRef.current)
    }, [jobId])

    // Stop polling when done
    useEffect(() => {
        if (job?.status === 'completed' || job?.status === 'failed') {
            clearInterval(pollRef.current)
            fetchJobs()
        }
    }, [job?.status])

    const fetchJobs = async () => {
        try {
            const res = await fetch(`${API_BASE}/finetune/jobs`)
            const data = await res.json()
            if (data.success) setJobs(data.jobs || [])
        } catch (_) { }
    }

    const pollJob = async (id) => {
        try {
            const res = await fetch(`${API_BASE}/finetune/status/${id}`)
            const data = await res.json()
            if (data.success) setJob(data.job)
        } catch (_) { }
    }

    const handleFile = (f) => {
        if (!f) return
        if (f.size > MAX_SIZE_MB * 1024 * 1024) {
            setError(`File too large. Max ${MAX_SIZE_MB}MB.`)
            return
        }
        setFile(f)
        setError(null)
    }

    const handleDrop = useCallback((e) => {
        e.preventDefault()
        setDragOver(false)
        const f = e.dataTransfer.files[0]
        if (f) handleFile(f)
    }, [])

    const handleUpload = async () => {
        if (!file) return
        setUploading(true)
        setError(null)
        setJob(null)
        setJobId(null)

        try {
            const form = new FormData()
            form.append('file', file)

            const res = await fetch(`${API_BASE}/finetune/upload`, {
                method: 'POST',
                body: form
            })
            const data = await res.json()

            if (!res.ok || !data.success) {
                throw new Error(data.detail || data.message || 'Upload failed')
            }

            setJobId(data.job_id)
            setJob({ job_id: data.job_id, status: 'queued', stage: 'queued', progress: 0, stage_message: 'Starting pipeline...' })
        } catch (err) {
            setError(err.message)
        } finally {
            setUploading(false)
        }
    }

    const handleRollback = async () => {
        if (!window.confirm('Roll back to original (non-fine-tuned) models?')) return
        try {
            const res = await fetch(`${API_BASE}/finetune/rollback`, { method: 'POST' })
            const data = await res.json()
            alert(data.success ? '✅ Rolled back to original models!' : '⚠️ No backup found.')
        } catch (e) {
            alert('Rollback failed: ' + e.message)
        }
    }

    const progress = job?.progress || 0
    const isRunning = job?.status === 'running' || job?.status === 'queued'

    return (
        <div className="flex-1 overflow-y-auto bg-gray-50 p-6 md:p-10">
            <div className="max-w-2xl mx-auto">

                {/* Header */}
                <div className="mb-8">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-indigo-600 rounded-2xl flex items-center justify-center shadow-md">
                            <Sparkles size={20} className="text-white" />
                        </div>
                        <div>
                            <h1 className="text-xl font-bold text-gray-900">Fine-Tune Models</h1>
                            <p className="text-sm text-gray-400">Upload your dataset to train Curezy's 3 AI doctors</p>
                        </div>
                    </div>
                </div>

                {/* Upload Card */}
                {!jobId && (
                    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
                        <div className="p-6">
                            <h2 className="font-semibold text-gray-800 mb-1 text-sm">Upload Dataset</h2>
                            <p className="text-xs text-gray-400 mb-4">PDF, TXT, CSV, DOCX, or Image (max {MAX_SIZE_MB}MB)</p>

                            {/* Drop Zone */}
                            <div
                                onDrop={handleDrop}
                                onDragOver={e => { e.preventDefault(); setDragOver(true) }}
                                onDragLeave={() => setDragOver(false)}
                                onClick={() => fileRef.current?.click()}
                                className={`relative border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all duration-200 ${dragOver
                                        ? 'border-primary-400 bg-primary-50 scale-[1.01]'
                                        : file
                                            ? 'border-green-300 bg-green-50'
                                            : 'border-gray-200 hover:border-primary-300 hover:bg-gray-50'
                                    }`}
                            >
                                <input
                                    ref={fileRef}
                                    type="file"
                                    accept={ACCEPTED_TYPES}
                                    className="hidden"
                                    onChange={e => handleFile(e.target.files[0])}
                                />
                                {file ? (
                                    <>
                                        <div className="w-12 h-12 bg-green-100 rounded-2xl flex items-center justify-center mx-auto mb-3">
                                            <FileText size={24} className="text-green-600" />
                                        </div>
                                        <p className="font-semibold text-gray-800 text-sm">{file.name}</p>
                                        <p className="text-xs text-gray-400 mt-1">{(file.size / 1024 / 1024).toFixed(2)} MB · Click to change</p>
                                    </>
                                ) : (
                                    <>
                                        <div className="w-12 h-12 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-3">
                                            <Upload size={24} className="text-gray-400" />
                                        </div>
                                        <p className="text-sm font-medium text-gray-600">Drop file here or <span className="text-primary-600 underline">browse</span></p>
                                        <p className="text-xs text-gray-400 mt-1">PDF · TXT · CSV · DOCX · Image</p>
                                    </>
                                )}
                            </div>

                            {error && (
                                <div className="mt-3 flex items-center gap-2 text-red-600 bg-red-50 border border-red-100 rounded-xl px-4 py-2.5">
                                    <AlertTriangle size={15} className="flex-shrink-0" />
                                    <span className="text-sm">{error}</span>
                                </div>
                            )}

                            {/* Pipeline Preview */}
                            <div className="mt-5 bg-gray-50 rounded-xl p-4 space-y-1.5">
                                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Pipeline Steps</p>
                                {PIPELINE_STEPS.map(s => (
                                    <div key={s.key} className="flex items-center gap-2 text-xs text-gray-500">
                                        <span>{s.emoji}</span>
                                        <span>{s.label}</span>
                                    </div>
                                ))}
                            </div>

                            <button
                                onClick={handleUpload}
                                disabled={!file || uploading}
                                className="mt-5 w-full bg-gradient-to-r from-primary-600 to-indigo-600 hover:from-primary-700 hover:to-indigo-700 text-white py-3 rounded-xl font-semibold text-sm shadow-md transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                            >
                                {uploading ? <><Loader size={16} className="animate-spin" /> Starting Pipeline...</> : <><Sparkles size={16} /> Start Fine-Tuning</>}
                            </button>
                        </div>
                    </div>
                )}

                {/* Pipeline Status */}
                {job && (
                    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
                        <div className="p-6">
                            <div className="flex items-center justify-between mb-5">
                                <div>
                                    <h2 className="font-semibold text-gray-800 text-sm">Pipeline Status</h2>
                                    <p className="text-xs text-gray-400 mt-0.5">{job.file_name}</p>
                                </div>
                                <div className={`px-3 py-1 rounded-full text-xs font-semibold ${job.status === 'completed' ? 'bg-green-100 text-green-700' :
                                        job.status === 'failed' ? 'bg-red-100 text-red-700' :
                                            'bg-primary-100 text-primary-700'
                                    }`}>
                                    {job.status === 'completed' ? '✅ Complete' :
                                        job.status === 'failed' ? '❌ Failed' :
                                            `${progress}%`}
                                </div>
                            </div>

                            {/* Overall progress bar */}
                            <div className="h-2 bg-gray-100 rounded-full overflow-hidden mb-5">
                                <div
                                    className={`h-full rounded-full transition-all duration-700 ${job.status === 'completed' ? 'bg-green-500' :
                                            job.status === 'failed' ? 'bg-red-400' :
                                                'bg-gradient-to-r from-primary-500 to-indigo-500'
                                        }`}
                                    style={{ width: `${progress}%` }}
                                />
                            </div>

                            {/* Steps */}
                            <div className="space-y-2 mb-4">
                                {PIPELINE_STEPS.map(step => (
                                    <StepItem key={step.key} step={step} currentStage={job.stage} progress={progress} />
                                ))}
                            </div>

                            {/* Stage message */}
                            {job.stage_message && (
                                <p className="text-xs text-gray-500 mt-3 italic px-1">{job.stage_message}</p>
                            )}

                            {/* Error */}
                            {job.status === 'failed' && job.error && (
                                <div className="mt-3 bg-red-50 border border-red-100 rounded-xl px-4 py-3">
                                    <p className="text-xs font-semibold text-red-700 mb-0.5">Error</p>
                                    <p className="text-xs text-red-600">{job.error}</p>
                                </div>
                            )}

                            {/* Summary */}
                            {job.status === 'completed' && job.summary && (
                                <div className="mt-4 bg-green-50 border border-green-100 rounded-xl p-4 space-y-2">
                                    <p className="text-xs font-semibold text-green-800">🎉 Fine-Tuning Complete!</p>
                                    <div className="grid grid-cols-2 gap-2 text-xs text-green-700">
                                        <span>📄 {job.summary.characters_parsed?.toLocaleString()} chars parsed</span>
                                        <span>📊 {job.summary.filtered_examples} training examples</span>
                                        <span>🔥 {job.summary.models_trained?.length} models trained</span>
                                        <span>🚀 {job.summary.models_deployed?.length} models deployed</span>
                                    </div>
                                    {job.summary.models_deployed?.length > 0 && (
                                        <div className="mt-2">
                                            <p className="text-xs text-green-700 font-medium">Active models:</p>
                                            {job.summary.models_deployed.map(m => (
                                                <span key={m} className="inline-block bg-white border border-green-200 text-green-700 text-xs px-2 py-0.5 rounded-full mr-1 mt-1 font-mono">{m}</span>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Actions */}
                            <div className="flex gap-2 mt-5">
                                <button
                                    onClick={() => { setJobId(null); setJob(null); setFile(null) }}
                                    className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-primary-600 px-3 py-2 rounded-lg hover:bg-gray-50 transition-all border border-gray-200"
                                >
                                    <RefreshCcw size={14} /> New Upload
                                </button>
                                {job.status === 'completed' && (
                                    <button
                                        onClick={handleRollback}
                                        className="flex items-center gap-1.5 text-sm text-red-500 hover:text-red-700 px-3 py-2 rounded-lg hover:bg-red-50 transition-all border border-red-100"
                                    >
                                        Rollback Models
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* Job History */}
                <JobHistory jobs={jobs} onSelect={(id) => {
                    setJobId(id)
                    pollJob(id)
                }} />
            </div>
        </div>
    )
}
