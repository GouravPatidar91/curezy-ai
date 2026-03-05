import { motion } from 'framer-motion'
import { ShieldAlert, LogOut, Sparkles, RefreshCw, Loader2 } from 'lucide-react'
import { supabase } from '../config/supabase'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useState } from 'react'

export default function PendingAccess() {
    const navigate = useNavigate()
    const { user, checkAccess } = useAuth()
    const [isRefreshing, setIsRefreshing] = useState(false)

    const handleLogout = async () => {
        await supabase.auth.signOut()
        navigate('/')
    }

    const handleRefresh = async () => {
        if (!user) return
        setIsRefreshing(true)
        try {
            const approved = await checkAccess(user.id, user.email)
            if (approved) {
                navigate('/chat')
            }
        } finally {
            setIsRefreshing(false)
        }
    }

    return (
        <div className="min-h-screen bg-[#050510] text-white flex flex-col items-center justify-center p-6 relative overflow-hidden">
            {/* Background elements */}
            <div className="fixed inset-0 z-0 pointer-events-none opacity-20" style={{ backgroundImage: 'radial-gradient(circle, #ffffff 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
            <div className="absolute top-[60vh] left-1/2 -translate-x-1/2 w-[150vw] h-[100vh] bg-gradient-to-b from-[#4D4DFF]/10 to-transparent border-t border-white/10 rounded-[100%] blur-sm opacity-70" />

            <motion.div
                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                className="relative z-10 w-full max-w-md bg-[#050510]/90 border border-white/10 rounded-3xl p-8 overflow-hidden backdrop-blur-xl shadow-[0_0_50px_rgba(0,0,0,0.8)] text-center"
            >
                <div className="w-16 h-16 rounded-full bg-gradient-to-tr from-accent-purple to-white flex items-center justify-center mx-auto mb-6 shadow-[0_0_20px_rgba(123,44,191,0.4)]">
                    <ShieldAlert className="text-black w-8 h-8" />
                </div>

                <h2 className="text-3xl font-bold text-white mb-4 tracking-tight">Access Restricted</h2>

                <div className="bg-white/5 border border-white/10 rounded-2xl p-4 mb-6 text-sm text-gray-300 leading-relaxed">
                    <p className="mb-3">
                        Curezy AI is currently in <span className="text-accent-blue font-bold">Invite-Only Beta</span>.
                    </p>
                    <p>
                        Your account is pending review by our medical board. You will receive an email once your access has been granted.
                    </p>
                </div>

                <div className="flex flex-col gap-3">
                    <motion.div
                        className="flex items-center justify-center gap-2 text-xs text-gray-500 mb-2"
                        animate={{ opacity: [0.4, 1, 0.4] }}
                        transition={{ duration: 2, repeat: Infinity }}
                    >
                        <Sparkles size={12} className="text-accent-purple" />
                        Awaiting administrator approval
                    </motion.div>

                    <button
                        onClick={handleRefresh}
                        disabled={isRefreshing}
                        className="flex items-center justify-center gap-2 w-full py-3.5 rounded-xl bg-accent-blue/10 border border-accent-blue/20 hover:bg-accent-blue/20 transition-all font-bold text-sm text-accent-blue disabled:opacity-50"
                    >
                        {isRefreshing ? (
                            <Loader2 size={16} className="animate-spin" />
                        ) : (
                            <RefreshCw size={16} />
                        )}
                        Refresh Status
                    </button>

                    <button
                        onClick={handleLogout}
                        className="flex items-center justify-center gap-2 w-full py-3.5 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors font-semibold text-sm text-gray-300"
                    >
                        <LogOut size={16} /> Sign out & Return Home
                    </button>
                </div>
            </motion.div>

            <p className="mt-8 text-xs text-gray-600 font-medium relative z-10">
                © 2026 Curezy AI Lab
            </p>
        </div>
    )
}
