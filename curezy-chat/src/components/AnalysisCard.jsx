import { CheckCircle, AlertTriangle, XCircle, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'

function ConfidenceBadge({ level, score }) {
    const map = {
        HIGH: { color: 'bg-green-100 text-green-700', icon: CheckCircle, label: 'High Confidence' },
        MEDIUM: { color: 'bg-yellow-100 text-yellow-700', icon: AlertTriangle, label: 'Medium Confidence' },
        LOW: { color: 'bg-orange-100 text-orange-700', icon: AlertTriangle, label: 'Low Confidence' },
        CRITICAL_LOW: { color: 'bg-red-100 text-red-700', icon: XCircle, label: 'Critical — See Doctor' },
    }
    const cfg = map[level] || map.LOW
    return (
        <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${cfg.color}`}>
            <cfg.icon size={12} />
            {cfg.label} ({score}%)
        </span>
    )
}

function ConditionCard({ condition, index }) {
    const [expanded, setExpanded] = useState(index === 0)
    const colors = ['border-l-primary-500', 'border-l-blue-400', 'border-l-purple-400']

    return (
        <div className={`border-l-4 ${colors[index] || 'border-l-gray-300'} bg-gray-50 rounded-r-xl p-3 mb-2`}>
            <div
                className="flex items-center justify-between cursor-pointer"
                onClick={() => setExpanded(!expanded)}
            >
                <div className="flex items-center gap-2">
                    <span className="w-5 h-5 bg-primary-600 text-white rounded-full text-xs flex items-center justify-center font-bold">
                        {index + 1}
                    </span>
                    <span className="font-semibold text-gray-900 text-sm">{condition.condition}</span>
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-500 font-medium">{condition.probability}% likely</span>
                    {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                </div>
            </div>

            {expanded && (
                <div className="mt-2 space-y-2 fade-in">
                    <div className="w-full bg-gray-200 rounded-full h-1.5">
                        <div
                            className="bg-primary-500 h-1.5 rounded-full transition-all"
                            style={{ width: `${condition.confidence}%` }}
                        />
                    </div>
                    <p className="text-xs text-gray-600 italic">{condition.reasoning}</p>
                    {condition.evidence?.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-1">
                            {condition.evidence.map((e, i) => (
                                <span key={i} className="bg-primary-50 text-primary-700 text-xs px-2 py-0.5 rounded-full border border-primary-100">
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

export default function AnalysisCard({ analysis, confidence, dataGaps }) {
    if (!analysis) return null
    const conditions = analysis.top_3_conditions || []

    return (
        <div className="bg-white border border-primary-100 rounded-2xl shadow-sm p-5 my-3 fade-in">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <span className="text-xl">🩺</span>
                    <h3 className="font-bold text-gray-900">AI Health Assessment</h3>
                </div>
                {confidence && (
                    <ConfidenceBadge level={confidence.confidence_level} score={confidence.overall_confidence} />
                )}
            </div>

            {/* Conditions */}
            <div className="mb-4">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Possible Conditions</p>
                {conditions.map((c, i) => <ConditionCard key={i} condition={c} index={i} />)}
            </div>

            {/* Summary */}
            {analysis.reasoning_summary && (
                <div className="bg-primary-50 rounded-xl p-3 mb-4">
                    <p className="text-xs font-semibold text-primary-700 mb-1">Clinical Summary</p>
                    <p className="text-xs text-gray-700 leading-relaxed">{analysis.reasoning_summary}</p>
                </div>
            )}

            {/* Data gaps */}
            {dataGaps?.length > 0 && (
                <div className="border border-yellow-200 bg-yellow-50 rounded-xl p-3 mb-4">
                    <p className="text-xs font-semibold text-yellow-700 mb-2">🔬 Recommended Tests</p>
                    {dataGaps.map((gap, i) => (
                        <p key={i} className="text-xs text-yellow-700 flex items-start gap-1">
                            <span>•</span>{gap}
                        </p>
                    ))}
                </div>
            )}

            {/* Safety flags */}
            {analysis.safety_flags?.length > 0 && (
                <div className="border border-red-200 bg-red-50 rounded-xl p-3 mb-4">
                    {analysis.safety_flags.map((flag, i) => (
                        <p key={i} className="text-xs text-red-700 font-medium flex items-start gap-1">
                            <span>⚠️</span>{flag}
                        </p>
                    ))}
                </div>
            )}

            {/* Disclaimer */}
            <p className="text-xs text-gray-400 text-center border-t border-gray-100 pt-3">
                This is an AI assessment, not a medical diagnosis. Always consult a qualified doctor.
            </p>
        </div>
    )
}