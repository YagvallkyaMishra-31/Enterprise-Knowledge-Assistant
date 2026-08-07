import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { listDocuments, uploadDocument, deleteDocument } from '../api/documents'
import {
  Upload, Trash2, FileText, CheckCircle2, Clock, AlertCircle,
  Loader2, LogOut, MessageSquare, XCircle, BookOpen, Plus
} from 'lucide-react'

const STATUS_CONFIG = {
  READY: { label: 'Ready', icon: CheckCircle2, bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200' },
  PENDING: { label: 'Queued', icon: Clock, bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200' },
  PROCESSING: { label: 'Processing', icon: Loader2, bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200', spin: true },
  FAILED: { label: 'Failed', icon: XCircle, bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' },
}

function StatusBadge({ status }) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.PENDING
  const Icon = cfg.icon
  return (
    <span className={`inline-flex items-center gap-1.5 text-[12px] font-medium px-2 py-[3px] rounded-md border ${cfg.bg} ${cfg.text} ${cfg.border}`}>
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
    <div className="h-screen flex bg-[#fbfbfb]">
      {/* ── Sidebar ── */}
      <aside className="w-[260px] shrink-0 bg-white border-r border-[#e5e5e5] flex flex-col">
        {/* Sidebar header */}
        <div className="h-[52px] shrink-0 flex items-center gap-2.5 px-4 border-b border-[#e5e5e5]">
          <div className="w-7 h-7 rounded-md bg-[#0f766e] flex items-center justify-center">
            <BookOpen size={14} className="text-white" strokeWidth={2.2} />
          </div>
          <span className="text-[13px] font-semibold text-[#1a1a1a] tracking-tight">
            Knowledge Assistant
          </span>
        </div>

        {/* Main Nav */}
        <nav className="flex-1 px-3 py-3 space-y-0.5">
          <button
            onClick={() => navigate('/chat')}
            className="w-full text-left flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-[13px] text-[#525252] hover:bg-[#fafafa] transition-colors"
          >
            <MessageSquare size={14} className="opacity-60 shrink-0" />
            <span className="font-medium">Chat</span>
          </button>
          <button
            onClick={() => navigate('/documents')}
            className="w-full text-left flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-[13px] text-[#0f766e] bg-[#f0fdfa] transition-colors"
          >
            <FileText size={14} className="opacity-80 shrink-0" />
            <span className="font-medium">Documents</span>
          </button>
        </nav>

        {/* Sidebar footer */}
        <div className="border-t border-[#e5e5e5] px-3 py-2 space-y-0.5">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-2 text-[13px] text-[#737373] hover:text-[#dc2626] px-2 py-1.5 rounded-md hover:bg-red-50 transition-colors"
          >
            <LogOut size={13} /> Sign out
          </button>
        </div>
      </aside>

      {/* ── Main ── */}
      <main className="flex-1 overflow-auto p-8">
        <div className="max-w-4xl mx-auto">
          {/* Page header */}
          <div className="flex items-end justify-between mb-6">
            <div>
              <h2 className="text-[20px] font-semibold text-[#1a1a1a] tracking-tight">Documents</h2>
              <p className="text-[13px] text-[#737373] mt-1">Upload text or PDF files to build your searchable knowledge base.</p>
            </div>
            <label className={`btn-primary text-[13px] cursor-pointer ${uploading ? 'opacity-50 pointer-events-none' : ''}`}>
              {uploading ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />}
              {uploading ? 'Uploading…' : 'Upload file'}
              <input ref={fileRef} type="file" accept=".pdf,.txt,.md" onChange={handleUpload} className="hidden" />
            </label>
          </div>

          {error && (
            <div className="flex items-start gap-2 bg-[#fef2f2] border border-[#fecaca] text-[#b91c1c] text-[13px] px-3.5 py-2.5 rounded-lg mb-4">
              <AlertCircle size={14} className="mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Content card */}
          <div className="bg-white rounded-xl border border-[#e5e5e5] overflow-hidden">
            {loading ? (
              <div className="p-6 space-y-3">
                {[1, 2, 3].map(i => <div key={i} className="skeleton h-10 w-full" />)}
              </div>
            ) : docs.length === 0 ? (
              <div className="py-16 text-center">
                <div className="w-12 h-12 rounded-xl bg-white border border-[#e5e5e5] shadow-sm flex items-center justify-center mx-auto mb-4">
                  <FileText size={20} className="text-[#ccc]" />
                </div>
                <p className="text-[14px] font-medium text-[#525252] mb-1.5">No documents yet</p>
                <p className="text-[13px] text-[#999] max-w-sm mx-auto leading-relaxed">
                  Upload a .pdf, .txt, or .md file to start building your knowledge base. You can then ask questions about their content.
                </p>
              </div>
            ) : (
              <table className="w-full text-[13px]">
                <thead>
                  <tr className="text-left text-[11px] font-medium text-[#999] uppercase tracking-wider border-b border-[#f0f0f0]">
                    <th className="px-5 py-3">Name</th>
                    <th className="px-5 py-3">Size</th>
                    <th className="px-5 py-3">Status</th>
                    <th className="px-5 py-3">Uploaded</th>
                    <th className="px-5 py-3 w-10"></th>
                  </tr>
                </thead>
                <tbody>
                  {docs.map((doc, i) => (
                    <tr key={doc.id} className={`border-b border-[#f5f5f5] last:border-0 hover:bg-[#fafafa] transition-colors ${i % 2 === 0 ? '' : 'bg-[#fcfcfc]'}`}>
                      <td className="px-5 py-3 flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded-md bg-[#f7f7f8] flex items-center justify-center shrink-0">
                          <FileText size={13} className="text-[#999]" />
                        </div>
                        <span className="text-[#1a1a1a] font-medium truncate max-w-xs">{doc.filename}</span>
                      </td>
                      <td className="px-5 py-3 text-[#737373]">{formatSize(doc.fileSizeBytes)}</td>
                      <td className="px-5 py-3"><StatusBadge status={doc.uploadStatus} /></td>
                      <td className="px-5 py-3 text-[#737373]">{formatDate(doc.createdAt)}</td>
                      <td className="px-5 py-3">
                        <button
                          onClick={() => handleDelete(doc.id)}
                          disabled={deleteId === doc.id}
                          className="text-[#ccc] hover:text-[#dc2626] disabled:opacity-30 transition-colors p-1 rounded"
                          title="Delete document"
                        >
                          {deleteId === doc.id ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
