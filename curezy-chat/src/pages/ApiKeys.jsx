import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Key, Plus, Trash2, Copy, CheckCircle, ArrowLeft, Eye, EyeOff } from 'lucide-react'
import { generateApiKey, listApiKeys, revokeApiKey } from '../api/client'
import { useAuth } from '../context/AuthContext'

export default function ApiKeys() {
    const { user } = useAuth()
    const [keys, setKeys] = useState([])
    const [loading, setLoading] = useState(true)
    const [generating, setGenerating] = useState(false)
    const [name, setName] = useState('')
    const [client, setClient] = useState('')
    const [newKey, setNewKey] = useState(null)
    const [copied, setCopied] = useState(false)
    const [error, setError] = useState('')
    const navigate = useNavigate()

    useEffect(() => { loadKeys() }, [])

    const loadKeys = async () => {
        setLoading(true)
        try {
            const res = await listApiKeys()
            setKeys(res.data.keys || [])
        } catch (err) {
            setError('Failed to load keys')
        }
        setLoading(false)
    }

    const handleGenerate = async () => {
        if (!name.trim()) { setError('Key name is required'); return }
        setGenerating(true)
        setError('')
        try {
            const res = await generateApiKey(name, client || 'My App')
            const data = res.data

            // Backend returns: {success, key: {key_id, api_key, client, ...}}
            // OR: {success, api_key: "string"}
            let keyString = ''
            if (typeof data?.api_key === 'string') {
                keyString = data.api_key
            } else if (typeof data?.key?.api_key === 'string') {
                keyString = data.key.api_key
            }

            if (!keyString) {
                // Last resort — find any string value starting with curezy_live_
                const str = JSON.stringify(data)
                const match = str.match(/curezy_live_[a-f0-9]+/)
                keyString = match ? match[0] : ''
            }

            if (!keyString) {
                setError('Key was created but could not be displayed. Check your keys list.')
                await loadKeys()
                setGenerating(false)
                return
            }

            setNewKey(keyString)
            setName('')
            setClient('')
            await loadKeys()
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to generate key')
        }
        setGenerating(false)
    }
    const handleRevoke = async (keyId) => {
        if (!window.confirm('Revoke this API key? This cannot be undone.')) return
        try {
            await revokeApiKey(keyId)
            loadKeys()
        } catch (err) {
            setError('Failed to revoke key')
        }
    }

    const copyKey = () => {
        navigator.clipboard.writeText(newKey)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <div className="bg-white border-b border-gray-100 px-6 py-4 flex items-center gap-4">
                <button onClick={() => navigate('/chat')} className="text-gray-400 hover:text-gray-600">
                    <ArrowLeft size={20} />
                </button>
                <div className="flex items-center gap-2">
                    <Key size={20} className="text-primary-600" />
                    <h1 className="font-bold text-gray-900">API Keys</h1>
                </div>
            </div>

            <div className="max-w-2xl mx-auto px-6 py-8 space-y-6">

                {/* Info banner */}
                <div className="bg-primary-50 border border-primary-100 rounded-2xl p-4">
                    <p className="text-sm text-primary-700">
                        <strong>API keys</strong> allow external applications to access Curezy AI on your behalf.
                        Keep them secret — treat them like passwords.
                    </p>
                </div>

                {/* Generate new key */}
                <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                    <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                        <Plus size={18} className="text-primary-600" />
                        Generate New Key
                    </h2>

                    {error && (
                        <div className="bg-red-50 text-red-700 text-sm px-4 py-2 rounded-xl mb-4">{error}</div>
                    )}

                    {newKey && (
                        <div className="bg-green-50 border border-green-200 rounded-xl p-4 mb-4">
                            <p className="text-xs font-semibold text-green-700 mb-2">
                                ✅ Key generated! Copy it now — it won't be shown again.
                            </p>
                            <div className="flex items-center gap-2 bg-white rounded-lg px-3 py-2 border border-green-200">
                                <code className="flex-1 text-xs text-gray-800 break-all">{newKey}</code>
                                <button onClick={copyKey} className="text-green-600 hover:text-green-700 flex-shrink-0">
                                    {copied ? <CheckCircle size={16} /> : <Copy size={16} />}
                                </button>
                            </div>
                        </div>
                    )}

                    <div className="space-y-3">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Key Name *</label>
                            <input
                                value={name}
                                onChange={e => setName(e.target.value)}
                                placeholder="e.g. My Hospital App"
                                className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-400"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Client Description</label>
                            <input
                                value={client}
                                onChange={e => setClient(e.target.value)}
                                placeholder="e.g. Curezy Web App"
                                className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-400"
                            />
                        </div>
                        <button
                            onClick={handleGenerate}
                            disabled={generating}
                            className="w-full bg-primary-600 hover:bg-primary-700 text-white py-2.5 rounded-xl text-sm font-medium transition-all disabled:opacity-50"
                        >
                            {generating ? 'Generating...' : 'Generate API Key'}
                        </button>
                    </div>
                </div>

                {/* Existing keys */}
                <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                    <h2 className="font-semibold text-gray-900 mb-4">Your API Keys</h2>

                    {loading ? (
                        <div className="text-center py-8 text-gray-400 text-sm">Loading keys...</div>
                    ) : keys.length === 0 ? (
                        <div className="text-center py-8">
                            <Key size={32} className="text-gray-200 mx-auto mb-2" />
                            <p className="text-gray-400 text-sm">No API keys yet</p>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {keys.map(key => (
                                <div key={key.key_id} className="flex items-center gap-3 p-4 bg-gray-50 rounded-xl">
                                    <div className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center flex-shrink-0">
                                        <Key size={14} className="text-primary-600" />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium text-gray-900">{key.name}</p>
                                        <p className="text-xs text-gray-400">
                                            {key.client} · {key.total_calls} calls · Created {new Date(key.created_at).toLocaleDateString()}
                                        </p>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <span className={`text-xs px-2 py-1 rounded-full font-medium ${key.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                                            {key.is_active ? 'Active' : 'Revoked'}
                                        </span>
                                        {key.is_active && (
                                            <button
                                                onClick={() => handleRevoke(key.key_id)}
                                                className="text-gray-400 hover:text-red-500 transition-colors"
                                            >
                                                <Trash2 size={14} />
                                            </button>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}