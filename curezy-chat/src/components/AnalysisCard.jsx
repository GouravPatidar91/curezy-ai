import { CheckCircle, AlertTriangle, XCircle, ChevronDown } from 'lucide-react'
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
        <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-medium border ${cfg.color}`}>
            <cfg.icon size={11} />
            {cfg.label} {score}%
        </span>
    )
}

function ConditionCard({ condition, index }) {
    const [expanded, setExpanded] = useState(index === 0)

    return (
        <div className="bg-[#2f2f2f]/50 border border-[#424242] rounded-xl mb-2 overflow-hidden transition-colors hover:bg-[#2f2f2f]">
            <div
                className="flex items-center justify-between p-4 cursor-pointer"
                onClick={() => setExpanded(!expanded)}
            >
                <div className="flex items-center gap-3">
                    <div className="w-6 h-6 rounded-full bg-[#2f2f2f] border border-[#424242] text-[#b4b4b4] text-xs flex items-center justify-center font-medium">
                        {index + 1}
                    </div>
                    <span className="font-semibold text-white text-sm">{condition.condition}</span>
                </div>
                <div className="flex items-center gap-4">
                    <div className="text-right">
                        <span className="text-[10px] text-[#676767] block leading-none mb-0.5">Likelihood</span>
                        <span className="text-sm font-semibold text-white leading-none">{condition.probability}%</span>
                    </div>
                    <div className={`p-1 rounded-md text-[#676767] transition-transform duration-300 ${expanded ? 'rotate-180' : ''}`}>
                        <ChevronDown size={14} />
                    </div>
                </div>
            </div>

            {expanded && (
                <div className="px-4 pb-4 space-y-3">
                    {/* Progress bar */}
                    <div className="w-full bg-[#212121] rounded-full h-1.5 overflow-hidden">
                        <div
                            className="h-full rounded-full bg-accent-green transition-all duration-1000 ease-out"
                            style={{ width: `${condition.probability}%` }}
                        />
                    </div>

                    {/* Reasoning */}
                    <div className="border-l-2 border-[#424242] pl-3">
                        <p className="text-xs text-[#b4b4b4] leading-relaxed italic">"{condition.reasoning}"</p>
                    </div>

                    {/* Evidence */}
                    {condition.evidence?.length > 0 && (
                        <div className="flex flex-wrap gap-1.5">
                            {condition.evidence.map((e, i) => (
                                <span key={i} className="bg-[#2f2f2f] text-[#b4b4b4] text-[11px] px-2 py-1 rounded-md border border-[#424242]">
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
        <div className="bg-[#1a1a1a] border border-[#333] rounded-2xl p-6 my-6 max-w-2xl mx-auto">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
                <div className="flex items-center gap-3">
                    <img src="/curezy logo.png" alt="Curezy" className="w-8 h-8 rounded-lg object-contain bg-[#2f2f2f] p-1 flex-shrink-0" />
                    <div>
                        <h3 className="font-semibold text-white text-[15px]">{modelLabel || 'AURANET (Thinking)'} Output</h3>
                        <p className="text-[11px] text-[#666]">Clinical Intelligence Report</p>
                    </div>
                </div>
                {confidence && (
                    <ConfidenceBadge level={confidence.confidence_level} score={confidence.overall_confidence} />
                )}
            </div>

            {/* Differential Diagnoses */}
            <div className="mb-6">
                <h4 className="text-xs font-medium text-[#676767] uppercase tracking-wide mb-3">Differential Diagnoses</h4>
                {conditions.map((c, i) => <ConditionCard key={i} condition={c} index={i} />)}
            </div>

            {/* Reasoning Summary */}
            {analysis.reasoning_summary && (
                <div className="mb-6">
                    <h4 className="text-xs font-medium text-[#676767] uppercase tracking-wide mb-3">Clinical Insight</h4>
                    <div className="bg-[#2f2f2f]/50 border border-[#424242] rounded-xl p-4">
                        <p className="text-sm text-[#d1d1d1] leading-relaxed">{analysis.reasoning_summary}</p>
                    </div>
                </div>
            )}

            {/* Next Steps */}
            {dataGaps?.length > 0 && (
                <div className="mb-6">
                    <h4 className="text-xs font-medium text-[#676767] uppercase tracking-wide mb-3">Next Clinical Steps</h4>
                    <div className="grid grid-cols-1 gap-2">
                        {dataGaps.map((gap, i) => {
                            const cleanGap = gap.split(' to increase ')[0].replace(/upload /gi, '')
                            return (
                                <div key={i} className="flex items-center gap-3 bg-[#2f2f2f]/50 border border-[#424242] rounded-xl px-4 py-3 text-sm text-[#d1d1d1]">
                                    <div className="w-1.5 h-1.5 rounded-full bg-accent-green flex-shrink-0" />
                                    <span className="capitalize">{cleanGap}</span>
                                </div>
                            )
                        })}
                    </div>
                </div>
            )}

            {/* Safety Flags */}
            {analysis.safety_flags?.length > 0 && (
                <div className="mb-6">
                    <div className="bg-red-500/5 border border-red-500/20 rounded-xl p-4">
                        {analysis.safety_flags.map((flag, i) => (
                            <p key={i} className="text-xs text-red-400 font-medium flex items-start gap-2 mb-1.5 last:mb-0">
                                <AlertTriangle size={12} className="mt-0.5 flex-shrink-0" /> {flag}
                            </p>
                        ))}
                    </div>
                </div>
            )}

            {/* Disclaimer */}
            <p className="text-[11px] text-[#676767] italic text-center pt-4 border-t border-[#2f2f2f] leading-relaxed">
                This report is generated by AI for informational purposes only. It is not a clinical diagnosis or medical prescription. Always consult a qualified medical professional.
            </p>
        </div>
    )
}
