import axios from 'axios'
import { supabase } from '../config/supabase'

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000'

// Standard API instance — 3-minute timeout for most calls
const api = axios.create({ baseURL: API_URL, timeout: 180_000 })

// Long-timeout instance — 8 minutes for council/RunPod analysis
const analysisApi = axios.create({ baseURL: API_URL, timeout: 480_000 })

// Attach Supabase JWT to every request
const attachAuth = async (config) => {
    const { data: { session } } = await supabase.auth.getSession()
    if (session?.access_token) {
        config.headers.Authorization = `Bearer ${session.access_token}`
    }
    return config
}
api.interceptors.request.use(attachAuth)
analysisApi.interceptors.request.use(attachAuth)

// ── Auth
export const loginUser = (email, password) => supabase.auth.signInWithPassword({ email, password })
export const signupUser = (email, password, fullName) =>
    supabase.auth.signUp({ email, password, options: { data: { full_name: fullName } } })
export const logoutUser = () => supabase.auth.signOut()
export const getSession = () => supabase.auth.getSession()

// ── Chat
export const startChat = () => api.post('/chat/start')
// sendMessage uses the long-timeout instance because it may trigger council analysis (60-120s+)
export const sendMessage = (convId, msg, selectedModel = null) =>
    analysisApi.post('/chat/message', { conversation_id: convId, message: msg, selected_model: selectedModel })

export const stageSubmit = (convId, stage, data, selectedModel = null) =>
    api.post('/chat/stage-submit', { conversation_id: convId, stage, data, selected_model: selectedModel })
export const skipStage = (convId, stage, selectedModel = null) =>
    api.post('/chat/skip-stage', { conversation_id: convId, stage, data: {}, selected_model: selectedModel })
export const uploadReport = (convId, file) => {
    const form = new FormData()
    form.append('conversation_id', convId)
    form.append('file', file)
    return api.post('/chat/upload-report', form, { headers: { 'Content-Type': 'multipart/form-data' } })
}
export const getChatHistory = (convId) => api.get(`/chat/${convId}/history`)

// ── Analysis
export const analyzePatient = (data) => api.post('/analyze', data)
export const analyzeXray = (formData) => api.post('/analyze/xray', formData, { headers: { 'Content-Type': 'multipart/form-data' } })

// ── API Keys
export const generateApiKey = (name, client) => api.post('/admin/apikey/generate', { name, client })
export const listApiKeys = () => api.get('/admin/apikey/list')
export const revokeApiKey = (keyId) => api.delete(`/admin/apikey/${keyId}/revoke`)

// ── Conversations (Supabase direct)
export const saveConversation = async (convId, userId, title) => {
    return supabase.from('conversations').upsert({
        conversation_id: convId,
        user_id: userId,
        title,
        updated_at: new Date().toISOString()
    })
}

export const getUserConversations = async (userId) => {
    return supabase
        .from('conversations')
        .select('*')
        .eq('user_id', userId)
        .order('updated_at', { ascending: false })
}

export const saveMessage = async (convId, userId, role, content) => {
    return supabase.from('chat_messages').insert({
        conversation_id: convId,
        user_id: userId,
        role,
        content,
        created_at: new Date().toISOString()
    })
}

export const getConversationMessages = async (convId) => {
    return supabase
        .from('chat_messages')
        .select('*')
        .eq('conversation_id', convId)
        .order('created_at', { ascending: true })
}

export const deleteConversation = async (convId) => {
    return supabase.from('conversations').delete().eq('conversation_id', convId)
}