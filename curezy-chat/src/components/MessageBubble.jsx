import ReactMarkdown from 'react-markdown'
import { motion } from 'framer-motion'
import { AlertCircle, RefreshCcw } from 'lucide-react'

export default function MessageBubble({ message, onRetry }) {
    const isUser = message.role === 'user'
    const isFailed = message.isFailed
    const isInfo = message.isInfo

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 15 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ duration: 0.3, ease: 'easeOut' }}
            className={`flex items-end gap-3 mb-6 ${isUser ? 'flex-row-reverse' : ''}`}
        >
            {/* Avatar */}
            <div className={`
        w-8 h-8 rounded-2xl flex items-center justify-center text-xs font-bold flex-shrink-0 shadow-neon
        ${isUser ? 'bg-white/20 text-gray-400' : 'bg-accent-purple text-white'}
      `}>
                {isUser ? 'You' : '🩺'}
            </div>

            {/* Bubble */}
            <div className="flex flex-col max-w-[78%]">
                <div className={`
          rounded-2xl px-4 py-3 shadow-md text-sm leading-relaxed backdrop-blur-md relative
          ${isUser
                        ? isFailed
                            ? 'bg-red-500/20 border border-red-500/50 text-white rounded-br-none shadow-[0_0_15px_rgba(239,68,68,0.2)]'
                            : 'bg-gradient-to-br from-accent-blue to-accent-purple text-white rounded-br-none shadow-[0_0_15px_rgba(123,44,191,0.3)]'
                        : isInfo
                            ? 'bg-accent-blue/5 border border-accent-blue/10 text-accent-blue italic rounded-bl-none z-10'
                            : 'glass border border-white/10 text-white rounded-bl-none z-10'
                    }
        `}>
                    {isFailed && (
                        <div className="absolute -left-6 top-1/2 -translate-y-1/2 text-red-500 animate-pulse">
                            <AlertCircle size={18} />
                        </div>
                    )}

                    {isUser ? (
                        <p className="whitespace-pre-wrap">{message.content}</p>
                    ) : (
                        <div className="markdown">
                            <ReactMarkdown>{message.content}</ReactMarkdown>
                        </div>
                    )}

                    <div className="flex items-center justify-between mt-1.5">
                        <p className={`text-[10px] ${isUser ? (isFailed ? 'text-red-300' : 'text-gray-300') : 'text-gray-500'}`}>
                            {new Date(message.timestamp || message.created_at || Date.now()).toLocaleTimeString([], {
                                hour: '2-digit', minute: '2-digit'
                            })}
                        </p>
                    </div>
                </div>

                {isFailed && onRetry && (
                    <button
                        onClick={() => onRetry(message.content)}
                        className="self-end mt-1.5 flex items-center gap-1.5 text-xs text-red-400 hover:text-red-300 transition-colors font-medium bg-red-500/10 px-2.5 py-1 rounded-md border border-red-500/20"
                    >
                        <RefreshCcw size={10} /> Message failed - Click to retry
                    </button>
                )}
            </div>
        </motion.div>
    )
}