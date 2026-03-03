import { useState, useRef } from 'react'
import { Upload, X, FileText, Image, CheckCircle } from 'lucide-react'
import { analyzeXray } from '../api/client'

export default function FileUpload({ convId, onClose }) {
    const [dragging, setDragging] = useState(false)
    const [files, setFiles] = useState([])
    const [uploading, setUploading] = useState(false)
    const [results, setResults] = useState({})
    const inputRef = useRef(null)

    const handleDrop = (e) => {
        e.preventDefault()
        setDragging(false)
        const dropped = Array.from(e.dataTransfer.files)
        addFiles(dropped)
    }

    const addFiles = (newFiles) => {
        const valid = newFiles.filter(f =>
            f.type.startsWith('image/') || f.type === 'application/pdf'
        )
        setFiles(prev => [...prev, ...valid])
    }

    const removeFile = (index) => {
        setFiles(prev => prev.filter((_, i) => i !== index))
    }

    const handleUpload = async () => {
        if (files.length === 0) return
        setUploading(true)

        for (const file of files) {
            try {
                if (file.type.startsWith('image/')) {
                    const formData = new FormData()
                    formData.append('file', file)
                    formData.append('patient_id', convId)
                    const res = await analyzeXray(formData)
                    setResults(prev => ({ ...prev, [file.name]: res.data }))
                }
            } catch (err) {
                setResults(prev => ({ ...prev, [file.name]: { error: 'Analysis failed' } }))
            }
        }
        setUploading(false)
    }

    const getFileIcon = (file) => {
        if (file.type.startsWith('image/')) return <Image size={16} className="text-primary-600" />
        return <FileText size={16} className="text-blue-600" />
    }

    return (
        <div className="bg-white border border-gray-200 rounded-2xl p-4 shadow-sm">
            <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-gray-900">Upload Files</h3>
                <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
                    <X size={16} />
                </button>
            </div>

            {/* Drop zone */}
            <div
                onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
                onDragLeave={() => setDragging(false)}
                onDrop={handleDrop}
                onClick={() => inputRef.current?.click()}
                className={`
          border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all
          ${dragging ? 'border-primary-500 bg-primary-50' : 'border-gray-200 hover:border-primary-400 hover:bg-gray-50'}
        `}
            >
                <Upload size={24} className="text-gray-400 mx-auto mb-2" />
                <p className="text-sm text-gray-600 font-medium">Drop files here or click to browse</p>
                <p className="text-xs text-gray-400 mt-1">X-rays, lab reports (Images, PDF)</p>
                <input
                    ref={inputRef}
                    type="file"
                    multiple
                    accept="image/*,.pdf"
                    className="hidden"
                    onChange={e => addFiles(Array.from(e.target.files))}
                />
            </div>

            {/* File list */}
            {files.length > 0 && (
                <div className="mt-3 space-y-2">
                    {files.map((file, i) => (
                        <div key={i} className="flex items-center gap-3 bg-gray-50 rounded-xl px-3 py-2">
                            {getFileIcon(file)}
                            <div className="flex-1 min-w-0">
                                <p className="text-xs font-medium text-gray-900 truncate">{file.name}</p>
                                <p className="text-xs text-gray-400">{(file.size / 1024).toFixed(1)} KB</p>
                            </div>
                            {results[file.name] ? (
                                <CheckCircle size={16} className="text-primary-600 flex-shrink-0" />
                            ) : (
                                <button onClick={() => removeFile(i)} className="text-gray-400 hover:text-red-500">
                                    <X size={14} />
                                </button>
                            )}
                        </div>
                    ))}

                    <button
                        onClick={handleUpload}
                        disabled={uploading}
                        className="w-full bg-primary-600 hover:bg-primary-700 text-white py-2 rounded-xl text-sm font-medium transition-all disabled:opacity-50"
                    >
                        {uploading ? 'Analyzing...' : `Analyze ${files.length} file${files.length > 1 ? 's' : ''}`}
                    </button>
                </div>
            )}
        </div>
    )
}