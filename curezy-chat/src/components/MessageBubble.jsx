import ReactMarkdown from 'react-markdown'
import { motion } from 'framer-motion'

export default function MessageBubble({ message }) {
    const isUser = message.role === 'user'

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
            <div className={`
        max-w-[78%] rounded-2xl px-4 py-3 shadow-md text-sm leading-relaxed backdrop-blur-md
        ${isUser
                    ? 'bg-gradient-to-br from-accent-blue to-accent-purple text-white rounded-br-none shadow-[0_0_15px_rgba(123,44,191,0.3)]'
                    : 'glass border border-white/10 text-white rounded-bl-none z-10'
                }
      `}>
                {isUser ? (
                    <p className="whitespace-pre-wrap">{message.content}</p>
                ) : (
                    <div className="markdown">
                        <ReactMarkdown>{message.content}</ReactMarkdown>
                    </div>
                )}

                <p className={`text-xs mt-1.5 ${isUser ? 'text-gray-300' : 'text-gray-500'}`}>
                    {new Date(message.timestamp || message.created_at || Date.now()).toLocaleTimeString([], {
                        hour: '2-digit', minute: '2-digit'
                    })}
                </p>
            </div>
        </motion.div>
    )
}