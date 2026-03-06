import ReactMarkdown from 'react-markdown'
import { motion } from 'framer-motion'
import { AlertCircle, RefreshCcw } from 'lucide-react'
import AnalysisCard from './AnalysisCard'
import FeedbackBar from './FeedbackBar'

const normalizeAnalysis = (raw) => {
    if (!raw) return null
    if (raw.analysis) return raw.analysis
    return raw
}

export default function MessageBubble({
    message,
    onRetry,
    analysisResult,
    selectedModel,
    modelOptions,
    sessionId,
    user
}) {
    const isUser = message.role === 'user'
    const isFailed = message.isFailed
    const isInfo = message.isInfo

    const isAnalysisTrigger = !isUser && message.content?.includes('## 🩺 Curezy AI Health Assessment')

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className={`flex items-start gap-3 mb-6 ${isUser ? 'flex-row-reverse' : ''}`}
        >
            {/* Avatar */}
            {isUser ? (
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#444] to-[#222] flex items-center justify-center text-[10px] font-bold text-white flex-shrink-0 mt-0.5 uppercase border border-[#555] shadow-lg">
                    {user?.user_metadata?.full_name?.[0] || user?.email?.[0] || 'U'}
                </div>
            ) : (
                <div className="w-8 h-8 rounded-full bg-[#1a1a1a] border border-[#2a2a2a] p-1 shadow-lg flex-shrink-0 mt-0.5">
                    <img
                        src="/curezy logo.png"
                        alt="Curezy"
                        className="w-full h-full object-contain"
                    />
                </div>
            )}

            {/* Content */}
            <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} max-w-[85%] sm:max-w-[75%]`}>
                {/* Role label */}
                <div className={`flex items-center gap-2 mb-1 px-1 ${isUser ? 'flex-row-reverse' : ''}`}>
                    <p className="text-[11px] font-bold text-[#666] uppercase tracking-wider">
                        {isUser ? 'Patient' : 'Curezy Council'}
                    </p>
                    <span className="text-[9px] text-[#444]">
                        {new Date(message.timestamp || message.created_at || Date.now()).toLocaleTimeString([], {
                            hour: '2-digit', minute: '2-digit'
                        })}
                    </span>
                </div>

                <div className={`
                    text-[14px] leading-relaxed
                    ${isUser
                        ? isFailed
                            ? 'bg-red-500/10 border border-red-500/20 text-[#ececec] rounded-2xl px-4 py-3'
                            : 'bg-[#2a2a2a] border border-[#3a3a3a] text-[#ececec] rounded-2xl px-4 py-3 shadow-sm'
                        : isInfo
                            ? 'text-[#888] italic text-[13px] py-2'
                            : 'text-[#d1d1d1] w-full'
                    }
                `}>
                    {isFailed && (
                        <div className="flex items-center gap-1.5 text-red-400 text-xs mb-1.5 font-medium">
                            <AlertCircle size={12} />
                            <span>Message failed</span>
                        </div>
                    )}

                    {isUser ? (
                        <p className="whitespace-pre-wrap">{message.content}</p>
                    ) : (
                        <div className="markdown prose prose-invert prose-sm max-w-none">
                            <ReactMarkdown>{message.content}</ReactMarkdown>
                        </div>
                    )}

                    {isAnalysisTrigger && analysisResult && (
                        <div className="mt-4 -mx-1">
                            <AnalysisCard
                                analysis={normalizeAnalysis(analysisResult.analysis || analysisResult)}
                                confidence={analysisResult.confidence}
                                dataGaps={analysisResult.dataGaps}
                                modelLabel={modelOptions?.find(m => m.key === selectedModel)?.label}
                            />
                            <FeedbackBar
                                sessionId={sessionId}
                                patientId={user?.id}
                                topDiagnosis={
                                    analysisResult?.analysis?.top_3_conditions?.[0]?.condition
                                    || analysisResult?.analysis?.conditions?.[0]?.condition
                                    || null
                                }
                            />
                        </div>
                    )}
                </div>

                <p className="text-[10px] text-[#555] mt-1.5 px-0.5">
                    {new Date(message.timestamp || message.created_at || Date.now()).toLocaleTimeString([], {
                        hour: '2-digit', minute: '2-digit'
                    })}
                </p>

                {isFailed && onRetry && (
                    <button
                        onClick={() => onRetry(message.content)}
                        className="mt-1 flex items-center gap-1 text-xs text-red-400 hover:text-red-300 transition-colors"
                    >
                        <RefreshCcw size={10} /> Retry
                    </button>
                )}
            </div>
        </motion.div>
    )
}
