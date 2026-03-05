import { createContext, useContext, useEffect, useState } from 'react'
import { supabase } from '../config/supabase'

const AuthContext = createContext({})

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null)
    const [isApproved, setIsApproved] = useState(false)
    const [loading, setLoading] = useState(true)

    const checkAccess = async (userId, email) => {
        if (!email) return
        try {
            const { data, error } = await supabase
                .from('early_access')
                .select('is_approved')
                .eq('email', email)
                .maybeSingle()

            if (!error && data) {
                setIsApproved(!!data.is_approved)
                return !!data.is_approved
            } else {
                setIsApproved(false)
                return false
            }
        } catch (err) {
            console.error('[AuthContext] Access check error:', err)
            setIsApproved(false)
            return false
        }
    }

    useEffect(() => {
        let subscription = null;

        const setupAuth = async () => {
            const { data: { session } } = await supabase.auth.getSession()
            const u = session?.user ?? null
            setUser(u)

            if (u) {
                await checkAccess(u.id, u.email)

                // Real-time subscription for this specific user's email
                subscription = supabase
                    .channel('early-access-changes')
                    .on(
                        'postgres_changes',
                        {
                            event: 'UPDATE',
                            schema: 'public',
                            table: 'early_access',
                            filter: `email=eq.${u.email}`
                        },
                        (payload) => {
                            console.log('[AuthContext] Access status updated real-time:', payload.new.is_approved)
                            setIsApproved(!!payload.new.is_approved)
                        }
                    )
                    .subscribe()
            }
            setLoading(false)
        }

        setupAuth()

        const { data: { subscription: authListener } } = supabase.auth.onAuthStateChange((_e, session) => {
            const u = session?.user ?? null
            setUser(u)
            if (u) checkAccess(u.id, u.email)
            else setIsApproved(false)
        })

        return () => {
            authListener.unsubscribe()
            if (subscription) supabase.removeChannel(subscription)
        }
    }, [])

    return (
        <AuthContext.Provider value={{ user, isApproved, loading, checkAccess }}>
            {!loading && children}
        </AuthContext.Provider>
    )
}

export const useAuth = () => useContext(AuthContext)