import { useState, useEffect, useCallback } from 'react'
import { Plus, MessageSquare, Trash2, Key, LogOut, ChevronLeft, ChevronRight, User, Loader, Sparkles, BarChart2 } from 'lucide-react'
import { supabase } from '../config/supabase'
import { useNavigate } from 'react-router-dom'

export default function Sidebar({ user, currentConvId, refreshTrigger, onNewChat, onSelectConv }) {
    const [conversations, setConversations] = useState([])
    const [collapsed, setCollapsed] = useState(false)
    const [loading, setLoading] = useState(false)
    const navigate = useNavigate()

    const loadConversations = useCallback(async () => {
        if (!user?.id) return
        setLoading(true)
        try {
            const { data, error } = await supabase
                .from('conversations')
                .select('conversation_id, title, updated_at, created_at')
                .eq('user_id', user.id)
                .order('updated_at', { ascending: false })
                .limit(50)

            if (error) {
                console.error('[Sidebar] Load error:', error.message, error.hint)
            } else {
                setConversations(data || [])
            }
        } catch (err) {
            console.error('[Sidebar] Unexpected error:', err)
        }
        setLoading(false)
    }, [user?.id])

    // Reload whenever refreshTrigger changes or convId changes
    useEffect(() => {
        loadConversations()
    }, [loadConversations, refreshTrigger])

    const handleDelete = async (e, id) => {
        e.stopPropagation()
        if (!window.confirm('Delete this conversation?')) return
        try {
            await supabase.from('chat_messages').delete().eq('conversation_id', id)
            await supabase.from('conversations').delete().eq('conversation_id', id)
            setConversations(prev => prev.filter(c => c.conversation_id !== id))
            if (id === currentConvId) onNewChat()
        } catch (err) {
            console.error('[Sidebar] Delete error:', err)
        }
    }

    const handleLogout = async () => {
        await supabase.auth.signOut()
        navigate('/')
    }

    const formatTime = (ts) => {
        if (!ts) return ''
        const d = new Date(ts)
        const now = new Date()
        const diff = now - d
        if (diff < 60000) return 'just now'
        if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
        if (diff < 86400000) return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        if (diff < 604800000) return d.toLocaleDateString([], { weekday: 'short' })
        return d.toLocaleDateString([], { month: 'short', day: 'numeric' })
    }

    return (
        <div className={`relative flex flex-col h-full glass border-r border-white/10 shadow-lg transition-all duration-300 z-20 ${collapsed ? 'w-16' : 'w-72'}`} style={{ minWidth: collapsed ? 64 : 288 }}>

            {/* Collapse button */}
            <button
                onClick={() => setCollapsed(c => !c)}
                className="absolute -right-3 top-6 w-6 h-6 bg-surface-light backdrop-blur border border-white/10 rounded-full flex items-center justify-center shadow z-30 hover:bg-accent-blue/10 transition-colors text-accent-blue"
            >
                {collapsed ? <ChevronRight size={12} /> : <ChevronLeft size={12} />}
            </button>

            {/* Logo + New Chat */}
            <div className={`p-4 border-b border-white/10 ${collapsed ? 'flex flex-col items-center gap-3' : ''}`}>
                <div className={`flex items-center gap-3 mb-3 ${collapsed ? 'justify-center' : ''}`}>
                    <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl flex items-center justify-center flex-shrink-0 shadow-sm">
                        <span className="text-white text-sm">🩺</span>
                    </div>
                    {!collapsed && (
                        <div className="min-w-0">
                            <h1 className="font-bold text-white text-sm leading-tight">Curezy AI</h1>
                            <p className="text-xs text-gray-500">Medical Council</p>
                        </div>
                    )}
                </div>
                <button
                    onClick={onNewChat}
                    className={`bg-accent-purple hover:bg-accent-blue active:bg-accent-purple/80 text-white rounded-xl flex items-center gap-2 transition-all font-medium text-sm shadow-md shadow-[0_0_15px_rgba(123,44,191,0.3)] ${collapsed ? 'p-2' : 'w-full px-4 py-2.5'}`}
                >
                    <Plus size={16} className="flex-shrink-0" />
                    {!collapsed && 'New Chat'}
                </button>
            </div>

            {/* Conversations list */}
            {!collapsed && (
                <div className="flex-1 overflow-y-auto py-3 px-2">
                    {loading ? (
                        <div className="flex items-center justify-center py-8 gap-2 text-gray-500">
                            <Loader size={14} className="animate-spin" />
                            <span className="text-xs">Loading...</span>
                        </div>
                    ) : conversations.length === 0 ? (
                        <div className="text-center py-10 px-4">
                            <MessageSquare size={28} className="text-gray-200 mx-auto mb-3" />
                            <p className="text-sm text-gray-500 font-medium">No conversations yet</p>
                            <p className="text-xs text-gray-300 mt-1">Click "New Chat" to get started</p>
                        </div>
                    ) : (
                        <>
                            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider px-3 mb-2">History</p>
                            {conversations.map(conv => (
                                <div
                                    key={conv.conversation_id}
                                    onClick={() => onSelectConv(conv.conversation_id)}
                                    className={`group relative flex items-start gap-2.5 px-3 py-2.5 rounded-xl cursor-pointer transition-all duration-150 mb-0.5 ${currentConvId === conv.conversation_id
                                        ? 'bg-accent-purple/20 border border-accent-purple/20 shadow-sm'
                                        : 'hover:bg-surface/50 border border-transparent'
                                        }`}
                                >
                                    <MessageSquare
                                        size={14}
                                        className={`mt-0.5 flex-shrink-0 ${currentConvId === conv.conversation_id ? 'text-accent-blue' : 'text-gray-500'}`}
                                    />
                                    <div className="flex-1 min-w-0">
                                        <p className={`text-sm truncate leading-tight font-semibold ${currentConvId === conv.conversation_id ? 'text-accent-purple' : 'text-gray-200'}`}>
                                            {conv.title || 'New Conversation'}
                                        </p>
                                        <p className="text-xs text-gray-500 mt-0.5">{formatTime(conv.updated_at || conv.created_at)}</p>
                                    </div>
                                    <button
                                        onClick={(e) => handleDelete(e, conv.conversation_id)}
                                        className="absolute right-2 top-2 opacity-0 group-hover:opacity-100 p-1 rounded-md hover:bg-red-50 hover:text-red-500 text-gray-500 transition-all"
                                    >
                                        <Trash2 size={11} />
                                    </button>
                                </div>
                            ))}
                        </>
                    )}
                </div>
            )}

            {/* Bottom nav */}
            <div className={`p-3 border-t border-white/10 space-y-1 ${collapsed ? 'flex flex-col items-center' : ''}`}>
                {!collapsed && (
                    <>
                        <button
                            onClick={() => navigate('/apikeys')}
                            className="flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-white/5 text-gray-500 hover:text-accent-blue transition-all w-full text-sm"
                        >
                            <Key size={15} />
                            API Keys
                        </button>
                    </>
                )}
                <div className={`flex items-center gap-2.5 px-3 py-2 rounded-xl bg-surface/50 border border-white/10 shadow-sm ${collapsed ? 'justify-center' : ''}`}>
                    <div className="w-7 h-7 bg-accent-blue/20 rounded-full flex items-center justify-center flex-shrink-0">
                        <User size={13} className="text-accent-blue" />
                    </div>
                    {!collapsed && (
                        <div className="flex-1 min-w-0">
                            <p className="text-xs font-semibold text-white truncate leading-tight">
                                {user?.user_metadata?.full_name || user?.email?.split('@')[0] || 'User'}
                            </p>
                            <p className="text-xs text-gray-500 truncate">{user?.email}</p>
                        </div>
                    )}
                    <button onClick={handleLogout} title="Logout" className="p-1 rounded-md text-gray-500 hover:text-red-500 hover:bg-red-50 transition-all flex-shrink-0">
                        <LogOut size={14} />
                    </button>
                </div>
            </div>
        </div>
    )
}