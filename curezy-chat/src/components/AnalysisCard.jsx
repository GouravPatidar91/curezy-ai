import { CheckCircle, AlertTriangle, XCircle, ChevronDown, ChevronUp, Activity, ShieldCheck, Info } from 'lucide-react'
import { useState } from 'react'

function ConfidenceBadge({ level, score }) {
    const map = {
        HIGH: { color: 'text-green-400 bg-green-500/10 border-green-500/20', icon: CheckCircle, label: 'High Confidence' },
        MEDIUM: { color: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20', icon: AlertTriangle, label: 'Medium Confidence' },
        LOW: { color: 'text-orange-400 bg-orange-500/10 border-orange-500/20', icon: AlertTriangle, label: 'Low Confidence' },
        CRITICAL_LOW: { color: 'text-red-400 bg-red-500/10 border-red-500/20', icon: XCircle, label: 'Critical — Consult Doctor' },
    }
    const cfg = map[level] || map.LOW
    return (
        <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border ${cfg.color} shadow-[0_0_15px_rgba(0,0,0,0.2)]`}>
            <cfg.icon size={11} />
            {cfg.label} • {score}%
        </span>
    )
}

function ConditionCard({ condition, index }) {
    const [expanded, setExpanded] = useState(index === 0)
    const gradients = [
        'from-accent-blue/40 to-accent-purple/40',
        'from-indigo-500/30 to-blue-500/30',
        'from-purple-500/30 to-pink-500/30'
    ]
    const ranks = ['🥇', '🥈', '🥉']

    return (
        <div className="bg-white/[0.03] border border-white/10 rounded-2xl mb-3 overflow-hidden transition-all hover:bg-white/[0.05] group">
            <div
                className="flex items-center justify-between p-4 cursor-pointer"
                onClick={() => setExpanded(!expanded)}
            >
                <div className="flex items-center gap-3">
                    <span className="text-lg grayscale group-hover:grayscale-0 transition-all">{ranks[index] || '📋'}</span>
                    <span className="font-bold text-white text-sm tracking-tight">{condition.condition}</span>
                </div>
                <div className="flex items-center gap-4">
                    <div className="text-right flex flex-col items-end">
                        <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest leading-none mb-1">Likelihood</span>
                        <span className="text-sm font-black text-white leading-none">{condition.probability}%</span>
                    </div>
                    <div className={`p-1.5 rounded-lg bg-white/5 text-gray-400 transition-transform duration-300 ${expanded ? 'rotate-180' : ''}`}>
                        <ChevronDown size={14} />
                    </div>
                </div>
            </div>

            {expanded && (
                <div className="px-4 pb-4 space-y-4 animate-in fade-in slide-in-from-top-2 duration-300">
                    <div className="w-full bg-white/5 rounded-full h-1.5 overflow-hidden">
                        <div
                            className={`h-full rounded-full bg-gradient-to-r ${gradients[index] || 'from-gray-500 to-gray-400'} transition-all duration-1000 ease-out`}
                            style={{ width: `${condition.probability}%` }}
                        />
                    </div>

                    <div className="bg-black/20 rounded-xl p-3 border border-white/5">
                        <p className="text-xs text-gray-400 leading-relaxed italic">"{condition.reasoning}"</p>
                    </div>

                    {condition.evidence?.length > 0 && (
                        <div className="flex flex-wrap gap-1.5">
                            {condition.evidence.map((e, i) => (
                                <span key={i} className="bg-white/5 text-gray-300 text-[10px] px-2.5 py-1 rounded-lg border border-white/10 font-medium">
                                    {e}
                                </span>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}

export default function AnalysisCard({ analysis, confidence, dataGaps, modelLabel }) {
    if (!analysis) return null
    const conditions = analysis.top_3_conditions || []

    return (
        <div className="glass border border-white/10 rounded-3xl p-6 my-6 shadow-2xl relative overflow-hidden group/card max-w-2xl mx-auto">
            {/* Ambient background glow */}
            <div className="absolute -top-24 -right-24 w-48 h-48 bg-accent-purple/10 blur-[80px] rounded-full pointer-events-none" />

            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-accent-blue to-accent-purple rounded-2xl flex items-center justify-center shadow-lg shadow-accent-purple/20">
                        <Activity size={20} className="text-white" />
                    </div>
                    <div>
                        <h3 className="font-black text-white text-lg tracking-tight uppercase">{modelLabel || 'AURANET'} Output</h3>
                        <p className="text-[10px] text-gray-500 font-bold tracking-widest uppercase">Clinical Intelligence Report</p>
                    </div>
                </div>
                {confidence && (
                    <ConfidenceBadge level={confidence.confidence_level} score={confidence.overall_confidence} />
                )}
            </div>

            {/* Possible Conditions */}
            <div className="mb-8">
                <div className="flex items-center gap-2 mb-4">
                    <div className="w-1 h-4 bg-accent-blue rounded-full" />
                    <h4 className="text-xs font-black text-gray-400 uppercase tracking-widest">Differential Diagnoses</h4>
                </div>
                {conditions.map((c, i) => <ConditionCard key={i} condition={c} index={i} />)}
            </div>

            {/* Reasoning Summary */}
            {analysis.reasoning_summary && (
                <div className="mb-8">
                    <div className="flex items-center gap-2 mb-4">
                        <div className="w-1 h-4 bg-accent-purple rounded-full" />
                        <h4 className="text-xs font-black text-gray-400 uppercase tracking-widest">Clinical Insight</h4>
                    </div>
                    <div className="bg-white/5 border border-white/10 rounded-2xl p-4">
                        <p className="text-sm text-gray-300 leading-relaxed font-medium">{analysis.reasoning_summary}</p>
                    </div>
                </div>
            )}

            {/* Next Steps (Cleaned Gaps) */}
            {dataGaps?.length > 0 && (
                <div className="mb-8">
                    <div className="flex items-center gap-2 mb-4">
                        <div className="w-1 h-4 bg-indigo-500 rounded-full" />
                        <h4 className="text-xs font-black text-gray-400 uppercase tracking-widest">Next Clinical Steps</h4>
                    </div>
                    <div className="grid grid-cols-1 gap-2">
                        {dataGaps.map((gap, i) => {
                            // Strip "upload" or accuracy mentioning text for a cleaner look
                            const cleanGap = gap.split(' to increase ')[0].replace(/upload /gi, '')
                            return (
                                <div key={i} className="flex items-center gap-3 bg-white/5 border border-white/5 rounded-xl px-4 py-3 text-sm text-gray-300 hover:border-white/20 transition-all">
                                    <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.5)]" />
                                    <span className="font-medium capitalize">{cleanGap}</span>
                                </div>
                            )
                        })}
                    </div>
                </div>
            )}

            {/* Safety Flags */}
            {analysis.safety_flags?.length > 0 && (
                <div className="mb-8">
                    <div className="bg-red-500/10 border border-red-500/20 rounded-2xl p-4">
                        {analysis.safety_flags.map((flag, i) => (
                            <p key={i} className="text-xs text-red-400 font-bold flex items-start gap-2 mb-1.5 last:mb-0">
                                <span className="mt-0.5">⚠️</span> {flag}
                            </p>
                        ))}
                    </div>
                </div>
            )}

            {/* Disclaimer & Footer */}
            <div className="pt-6 border-t border-white/5 flex flex-col items-center gap-4">
                <div className="flex items-center gap-4 text-gray-600">
                    <div className="flex items-center gap-1">
                        <ShieldCheck size={12} />
                        <span className="text-[10px] font-bold uppercase tracking-tighter">Verified Logic</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <Info size={12} />
                        <span className="text-[10px] font-bold uppercase tracking-tighter">Protocol 1.0.0</span>
                    </div>
                </div>
                <p className="text-[10px] text-gray-500 text-center leading-relaxed font-medium bg-black/20 px-4 py-2 rounded-xl border border-white/5 italic">
                    Note: This report is generated by AI for informational purposes only. It is not a clinical diagnosis or medical prescription. Always consult a qualified medical professional for final treatment.
                </p>
            </div>
        </div>
    )
}