import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { listDocuments, uploadDocument, deleteDocument } from '../api/documents'
import {
  Upload, Trash2, FileText, CheckCircle2, Clock, AlertCircle,
  Loader2, LogOut, MessageSquare, XCircle
} from 'lucide-react'

const STATUS_CONFIG = {
  READY: { label: 'Ready', icon: CheckCircle2, color: 'text-emerald-700 bg-emerald-50 border-emerald-200' },
  PENDING: { label: 'Pending', icon: Clock, color: 'text-amber-700 bg-amber-50 border-amber-200' },
  PROCESSING: { label: 'Processing', icon: Loader2, color: 'text-blue-700 bg-blue-50 border-blue-200', spin: true },
  FAILED: { label: 'Failed', icon: XCircle, color: 'text-red-700 bg-red-50 border-red-200' },
}

function StatusBadge({ status }) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.PENDING
  const Icon = cfg.icon
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded border ${cfg.color}`}>
      <Icon size={12} className={cfg.spin ? 'animate-spin' : ''} />
      {cfg.label}
    </span>
  )
}

function formatSize(bytes) {
  if (!bytes) return '—'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1048576).toFixed(1)} MB`
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

export default function DocumentsPage() {
  const { token, logout } = useAuth()
  const navigate = useNavigate()
  const [docs, setDocs] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)
  const [deleteId, setDeleteId] = useState(null)
  const fileRef = useRef(null)
  const pollRef = useRef(null)

  const fetchDocs = useCallback(async () => {
    try {
      const data = await listDocuments(token)
      setDocs(data)
      setError(null)
      return data
    } catch (err) {
      setError(err.message)
      return []
    }
  }, [token])

  useEffect(() => {
    fetchDocs().finally(() => setLoading(false))
  }, [fetchDocs])

  // Poll only while any doc is PENDING or PROCESSING
  useEffect(() => {
    const hasPending = docs.some(d => d.uploadStatus === 'PENDING' || d.uploadStatus === 'PROCESSING')
    if (hasPending) {
      pollRef.current = setInterval(() => fetchDocs(), 4000)
    } else {
      clearInterval(pollRef.current)
    }
    return () => clearInterval(pollRef.current)
  }, [docs, fetchDocs])

  async function handleUpload(e) {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    setError(null)
    try {
      await uploadDocument(token, file)
      await fetchDocs()
    } catch (err) {
      setError(err.message)
    } finally {
      setUploading(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  async function handleDelete(id) {
    setDeleteId(id)
    try {
      await deleteDocument(token, id)
      setDocs(prev => prev.filter(d => d.id !== id))
    } catch (err) {
      setError(err.message)
    } finally {
      setDeleteId(null)
    }
  }

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div className="h-screen flex flex-col bg-stone-100">
      {/* Top bar */}
      <header className="flex items-center justify-between px-6 py-3 bg-white border-b border-stone-200">
        <h1 className="text-lg font-bold text-stone-900">Knowledge Assistant</h1>
        <nav className="flex items-center gap-3">
          <button
            onClick={() => navigate('/chat')}
            className="flex items-center gap-1.5 text-sm text-stone-600 hover:text-teal-700 font-medium transition-colors"
          >
            <MessageSquare size={16} />
            Chat
          </button>
          <button
            onClick={handleLogout}
            className="flex items-center gap-1.5 text-sm text-stone-500 hover:text-red-600 transition-colors"
          >
            <LogOut size={16} />
            Sign out
          </button>
        </nav>
      </header>

      {/* Main content */}
      <main className="flex-1 overflow-auto px-6 py-6 max-w-4xl">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="text-xl font-bold text-stone-900">Documents</h2>
            <p className="text-sm text-stone-500 mt-0.5">Upload text or PDF files to build your knowledge base.</p>
          </div>
          <label className={`flex items-center gap-2 bg-teal-700 hover:bg-teal-800 text-white font-medium py-2 px-4 rounded-md text-sm cursor-pointer transition-colors ${uploading ? 'opacity-50 pointer-events-none' : ''}`}>
            {uploading ? <Loader2 size={16} className="animate-spin" /> : <Upload size={16} />}
            {uploading ? 'Uploading...' : 'Upload file'}
            <input ref={fileRef} type="file" accept=".pdf,.txt,.md" onChange={handleUpload} className="hidden" />
          </label>
        </div>

        {error && (
          <div className="flex items-start gap-2 bg-red-50 border border-red-200 text-red-700 text-sm px-3 py-2.5 rounded-md mb-4">
            <AlertCircle size={16} className="mt-0.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {loading ? (
          <div className="space-y-2">
            {[1, 2, 3].map(i => <div key={i} className="skeleton h-12 w-full" />)}
          </div>
        ) : docs.length === 0 ? (
          <div className="text-center py-16 text-stone-400">
            <FileText size={40} className="mx-auto mb-3 opacity-40" />
            <p className="text-sm font-medium text-stone-500">No documents uploaded yet</p>
            <p className="text-xs text-stone-400 mt-1">Upload a .pdf, .txt, or .md file to get started. Once processed, you can ask questions about its contents.</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs font-medium text-stone-400 uppercase tracking-wider border-b border-stone-200">
                <th className="pb-2 pr-4">Filename</th>
                <th className="pb-2 pr-4">Size</th>
                <th className="pb-2 pr-4">Status</th>
                <th className="pb-2 pr-4">Uploaded</th>
                <th className="pb-2 w-10"></th>
              </tr>
            </thead>
            <tbody>
              {docs.map(doc => (
                <tr key={doc.id} className="border-b border-stone-100 hover:bg-stone-50 transition-colors">
                  <td className="py-2.5 pr-4 flex items-center gap-2">
                    <FileText size={16} className="text-stone-400 shrink-0" />
                    <span className="text-stone-800 font-medium truncate max-w-xs">{doc.filename}</span>
                  </td>
                  <td className="py-2.5 pr-4 text-stone-500">{formatSize(doc.fileSizeBytes)}</td>
                  <td className="py-2.5 pr-4"><StatusBadge status={doc.uploadStatus} /></td>
                  <td className="py-2.5 pr-4 text-stone-500">{formatDate(doc.createdAt)}</td>
                  <td className="py-2.5">
                    <button
                      onClick={() => handleDelete(doc.id)}
                      disabled={deleteId === doc.id}
                      className="text-stone-400 hover:text-red-600 disabled:opacity-30 transition-colors"
                      title="Delete document"
                    >
                      {deleteId === doc.id ? <Loader2 size={15} className="animate-spin" /> : <Trash2 size={15} />}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </main>
    </div>
  )
}
