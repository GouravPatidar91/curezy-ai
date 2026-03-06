import { useState, useEffect, useCallback } from 'react'
import { Plus, Trash2, Key, LogOut, ChevronLeft, ChevronRight, User, Loader, Settings, Ellipsis } from 'lucide-react'
import { supabase } from '../config/supabase'
import { useNavigate } from 'react-router-dom'

// ── Date grouping helper ──────────────────────────────────────
function groupConversationsByDate(conversations) {
    const now = new Date()
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    const yesterday = new Date(today); yesterday.setDate(today.getDate() - 1)
    const sevenDaysAgo = new Date(today); sevenDaysAgo.setDate(today.getDate() - 7)
    const thirtyDaysAgo = new Date(today); thirtyDaysAgo.setDate(today.getDate() - 30)

    const groups = [
        { label: 'Today', items: [] },
        { label: 'Yesterday', items: [] },
        { label: 'Previous 7 Days', items: [] },
        { label: 'Previous 30 Days', items: [] },
        { label: 'Older', items: [] },
    ]

    conversations.forEach(conv => {
        const d = new Date(conv.updated_at || conv.created_at)
        if (d >= today) groups[0].items.push(conv)
        else if (d >= yesterday) groups[1].items.push(conv)
        else if (d >= sevenDaysAgo) groups[2].items.push(conv)
        else if (d >= thirtyDaysAgo) groups[3].items.push(conv)
        else groups[4].items.push(conv)
    })

    return groups.filter(g => g.items.length > 0)
}

export default function Sidebar({ user, currentConvId, refreshTrigger, onNewChat, onSelectConv }) {
    const [conversations, setConversations] = useState([])
    const [collapsed, setCollapsed] = useState(false)
    const [loading, setLoading] = useState(false)
    const [showUserMenu, setShowUserMenu] = useState(false)
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

    const grouped = groupConversationsByDate(conversations)

    return (
        <div
            className={`relative flex flex-col h-full bg-[#171717] border-r border-[#2f2f2f] transition-all duration-300 z-20 ${collapsed ? 'w-16' : 'w-[260px]'}`}
            style={{ minWidth: collapsed ? 64 : 260 }}
        >
            {/* Collapse button */}
            <button
                onClick={() => setCollapsed(c => !c)}
                className="absolute -right-3 top-6 w-6 h-6 bg-[#2f2f2f] border border-[#424242] rounded-full flex items-center justify-center shadow-sm z-30 hover:bg-[#3a3a3a] transition-colors text-[#b4b4b4]"
            >
                {collapsed ? <ChevronRight size={12} /> : <ChevronLeft size={12} />}
            </button>

            {/* Logo + New Chat */}
            <div className={`p-3 ${collapsed ? 'flex flex-col items-center gap-3' : ''}`}>
                <div className={`flex items-center gap-2.5 mb-3 ${collapsed ? 'justify-center' : 'px-1'}`}>
                    <img
                        src="/curezy logo.png"
                        alt="Curezy"
                        className="w-7 h-7 rounded-lg object-contain flex-shrink-0"
                    />
                    {!collapsed && (
                        <span className="font-semibold text-white text-[13px] tracking-tight">Curezy AI</span>
                    )}
                </div>
                <button
                    onClick={onNewChat}
                    className={`border border-[#363636] text-[#ececec] rounded-lg flex items-center gap-2 transition-colors text-[13px] hover:bg-[#2f2f2f] font-medium ${collapsed ? 'p-2.5 justify-center' : 'w-full px-3 py-2.5'}`}
                >
                    <Plus size={16} className="flex-shrink-0" />
                    {!collapsed && 'New Chat'}
                </button>
            </div>

            {/* Conversations list */}
            {!collapsed && (
                <div className="flex-1 overflow-y-auto py-1 px-1.5">
                    {loading ? (
                        <div className="flex items-center justify-center py-8 gap-2 text-[#676767]">
                            <Loader size={14} className="animate-spin" />
                            <span className="text-xs">Loading...</span>
                        </div>
                    ) : conversations.length === 0 ? (
                        <div className="text-center py-10 px-4">
                            <p className="text-sm text-[#555]">No conversations yet</p>
                            <p className="text-xs text-[#444] mt-1">Start a new chat to begin</p>
                        </div>
                    ) : (
                        grouped.map(group => (
                            <div key={group.label}>
                                <p className="text-[11px] font-medium text-[#666] uppercase tracking-wider px-3 pt-4 pb-1.5">
                                    {group.label}
                                </p>
                                {group.items.map(conv => (
                                    <div
                                        key={conv.conversation_id}
                                        onClick={() => onSelectConv(conv.conversation_id)}
                                        className={`group relative flex items-center px-3 py-2 rounded-lg cursor-pointer transition-colors duration-100 mb-px ${
                                            currentConvId === conv.conversation_id
                                                ? 'bg-[#2f2f2f]'
                                                : 'hover:bg-[#1e1e1e]'
                                        }`}
                                    >
                                        <p className={`text-[13px] truncate leading-tight flex-1 min-w-0 ${
                                            currentConvId === conv.conversation_id ? 'text-[#ececec]' : 'text-[#aaa]'
                                        }`}>
                                            {conv.title || 'New Conversation'}
                                        </p>
                                        <button
                                            onClick={(e) => handleDelete(e, conv.conversation_id)}
                                            className="opacity-0 group-hover:opacity-100 p-1 rounded-md hover:bg-[#3a3a3a] text-[#666] hover:text-red-400 transition-all flex-shrink-0 ml-1"
                                        >
                                            <Trash2 size={12} />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        ))
                    )}
                </div>
            )}

            {/* Bottom section - Profile + Menu */}
            <div className={`border-t border-[#2f2f2f] ${collapsed ? 'flex flex-col items-center p-2' : 'p-2'}`}>
                {/* Profile row - clickable to toggle menu */}
                <button
                    onClick={() => !collapsed && setShowUserMenu(m => !m)}
                    className={`w-full flex items-center gap-2.5 px-2.5 py-2.5 rounded-lg hover:bg-[#2f2f2f] transition-colors ${collapsed ? 'justify-center' : ''}`}
                >
                    <div className="w-8 h-8 bg-[#2f2f2f] rounded-full flex items-center justify-center flex-shrink-0">
                        <User size={14} className="text-[#999]" />
                    </div>
                    {!collapsed && (
                        <>
                            <div className="flex-1 min-w-0 text-left">
                                <p className="text-[13px] font-medium text-[#ececec] truncate leading-tight">
                                    {user?.user_metadata?.full_name || user?.email?.split('@')[0] || 'User'}
                                </p>
                            </div>
                            <Ellipsis size={16} className="text-[#666] flex-shrink-0" />
                        </>
                    )}
                </button>

                {/* Dropdown menu (shown above profile) */}
                {showUserMenu && !collapsed && (
                    <div className="mb-1 bg-[#2a2a2a] border border-[#3a3a3a] rounded-lg overflow-hidden shadow-xl">
                        <div className="px-3 py-2.5 border-b border-[#333]">
                            <p className="text-[12px] text-[#999] truncate">{user?.email}</p>
                        </div>
                        <button
                            onClick={() => { navigate('/apikeys'); setShowUserMenu(false) }}
                            className="flex items-center gap-2.5 px-3 py-2.5 hover:bg-[#333] transition-colors w-full text-left text-[13px] text-[#ccc] hover:text-white"
                        >
                            <Key size={14} />
                            API Keys
                        </button>
                        <button
                            onClick={handleLogout}
                            className="flex items-center gap-2.5 px-3 py-2.5 hover:bg-[#333] transition-colors w-full text-left text-[13px] text-red-400 hover:text-red-300 border-t border-[#333]"
                        >
                            <LogOut size={14} />
                            Log out
                        </button>
                    </div>
                )}
            </div>
        </div>
    )
}
