import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { listSessions, createSession, getSessionMessages, askQuestionStream, parseSSEStream } from '../api/chat'
import {
  Plus, Send, FileText, LogOut, MessageSquare, AlertCircle,
  Loader2, BookOpen, ShieldAlert, ChevronRight
} from 'lucide-react'

function formatTime(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
}

/* Format session title: strip ugly ISO timestamps into something human */
function formatSessionTitle(title) {
  if (!title) return 'Untitled'
  // If title looks like "New Chat 2026-08-07T09:01:25...", clean it up
  const isoMatch = title.match(/^New Chat\s+(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})/)
  if (isoMatch) {
    const d = new Date(`${isoMatch[1]}T${isoMatch[2]}:00`)
    return `Chat · ${d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })} ${d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}`
  }
  return title.length > 30 ? title.slice(0, 30) + '…' : title
}

/* ── Citation Block ── */
function CitationBlock({ sources }) {
  if (!sources || (Array.isArray(sources) && sources.length === 0)) return null
  const items = Array.isArray(sources) ? sources : []
  if (items.length === 0) return null

  return (
    <div className="mt-3 border border-[#d1e7dd] bg-[#f0faf6] rounded-lg p-3">
      <div className="flex items-center gap-1.5 text-[11px] font-semibold text-[#0f766e] uppercase tracking-wider mb-2">
        <BookOpen size={12} />
        Sources
      </div>
      <ul className="space-y-1.5">
        {items.map((src, i) => (
          <li key={i} className="text-[12px] text-[#374151] flex items-start gap-1.5">
            <ChevronRight size={11} className="mt-0.5 shrink-0 text-[#0f766e] opacity-60" />
            <span>
              {src.documentName && <span className="font-medium">{src.documentName}</span>}
              {src.chunkText && <span className="text-[#6b7280] ml-1">— {src.chunkText.slice(0, 150)}{src.chunkText.length > 150 ? '…' : ''}</span>}
              {!src.chunkText && !src.documentName && <span className="text-[#6b7280]">{JSON.stringify(src).slice(0, 150)}</span>}
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}

/* ── Honest Fallback ── */
function FallbackIndicator() {
  return (
    <div className="mt-3 border border-[#fde68a] bg-[#fffbeb] rounded-lg p-3 flex items-start gap-2">
      <ShieldAlert size={14} className="text-[#d97706] mt-0.5 shrink-0" />
      <div>
        <p className="text-[12px] font-semibold text-[#92400e]">No matching documents found</p>
        <p className="text-[12px] text-[#a16207] mt-0.5">The system could not find relevant information in your uploaded documents to answer this question.</p>
      </div>
    </div>
  )
}

/* ── Message Bubble ── */
function MessageBubble({ role, text, sources, isStreaming }) {
  const isUser = role === 'user'
  const hasSources = sources && Array.isArray(sources) && sources.length > 0
  const isFallback = !isUser && !isStreaming && sources && Array.isArray(sources) && sources.length === 0

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-[70%] ${
        isUser
          ? 'bg-[#0f766e] text-white rounded-2xl rounded-br-md'
          : 'bg-white border border-[#e5e5e5] text-[#1a1a1a] rounded-2xl rounded-bl-md shadow-sm'
      } px-4 py-3 text-[14px] leading-relaxed`}>
        <p className={`whitespace-pre-wrap ${isStreaming ? 'typing-caret' : ''}`}>{text || (isStreaming ? '' : '…')}</p>
        {hasSources && <CitationBlock sources={sources} />}
        {isFallback && <FallbackIndicator />}
      </div>
    </div>
  )
}

/* ── Main Chat Page ── */
export default function ChatPage() {
  const { token, logout } = useAuth()
  const { sessionId } = useParams()
  const navigate = useNavigate()

  const [sessions, setSessions] = useState([])
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [streamText, setStreamText] = useState('')
  const [streamSources, setStreamSources] = useState(null)
  const [loadingSessions, setLoadingSessions] = useState(true)
  const [loadingMessages, setLoadingMessages] = useState(false)
  const [error, setError] = useState(null)
  const [creatingSess, setCreatingSess] = useState(false)

  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    listSessions(token)
      .then(setSessions)
      .catch(err => setError(err.message))
      .finally(() => setLoadingSessions(false))
  }, [token])

  useEffect(() => {
    if (!sessionId) {
      setMessages([])
      return
    }
    setLoadingMessages(true)
    setError(null)
    getSessionMessages(token, sessionId)
      .then(data => {
        const mapped = []
        for (const qa of data) {
          mapped.push({ role: 'user', text: qa.question })
          mapped.push({ role: 'assistant', text: qa.answer, sources: qa.sources })
        }
        setMessages(mapped)
      })
      .catch(err => setError(err.message))
      .finally(() => {
        setLoadingMessages(false)
        setTimeout(scrollToBottom, 100)
      })
  }, [sessionId, token, scrollToBottom])

  useEffect(() => { scrollToBottom() }, [messages, streamText, scrollToBottom])

  async function handleNewSession() {
    setCreatingSess(true)
    try {
      const sess = await createSession(token)
      setSessions(prev => [sess, ...prev])
      navigate(`/chat/${sess.id}`)
    } catch (err) {
      setError(err.message)
    } finally {
      setCreatingSess(false)
    }
  }

  async function handleSend(e) {
    e.preventDefault()
    if (!input.trim() || !sessionId || streaming) return

    const question = input.trim()
    setInput('')
    setError(null)
    setMessages(prev => [...prev, { role: 'user', text: question }])
    setStreaming(true)
    setStreamText('')
    setStreamSources(null)

    try {
      const body = await askQuestionStream(token, sessionId, question)
      let fullText = ''
      let sources = null

      for await (const { event, data } of parseSSEStream(body)) {
        if (event === 'token') {
          fullText += data.text || ''
          setStreamText(fullText)
        } else if (event === 'sources') {
          sources = data.sources || []
          setStreamSources(sources)
        } else if (event === 'done') {
          break
        } else if (event === 'error') {
          setError(data.message || 'An error occurred during generation.')
          break
        }
      }

      setMessages(prev => [...prev, { role: 'assistant', text: fullText, sources: sources || [] }])
    } catch (err) {
      setError(err.message)
    } finally {
      setStreaming(false)
      setStreamText('')
      setStreamSources(null)
      inputRef.current?.focus()
    }
  }

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div className="h-screen flex bg-[#f7f7f8]">
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

        {/* New chat button */}
        <div className="px-3 pt-3">
          <button
            onClick={handleNewSession}
            disabled={creatingSess}
            className="w-full flex items-center justify-center gap-1.5 btn-primary text-[13px] h-[36px]"
          >
            {creatingSess ? <Loader2 size={13} className="animate-spin" /> : <Plus size={13} />}
            New conversation
          </button>
        </div>

        {/* Session list */}
        <nav className="flex-1 overflow-auto custom-scrollbar px-2 py-2 space-y-0.5">
          {loadingSessions ? (
            <div className="space-y-2 px-1 pt-2">{[1, 2, 3].map(i => <div key={i} className="skeleton h-8 w-full" />)}</div>
          ) : sessions.length === 0 ? (
            <p className="text-[12px] text-[#aaa] px-2 pt-4 text-center">No conversations yet</p>
          ) : (
            sessions.map(s => (
              <button
                key={s.id}
                onClick={() => navigate(`/chat/${s.id}`)}
                className={`w-full text-left flex items-center gap-2 px-2.5 py-2 rounded-lg text-[13px] transition-colors ${
                  s.id === sessionId
                    ? 'bg-[#f0fdfa] text-[#0f766e] font-medium'
                    : 'text-[#525252] hover:bg-[#fafafa]'
                }`}
              >
                <MessageSquare size={13} className="shrink-0 opacity-40" />
                <span className="truncate">{formatSessionTitle(s.title)}</span>
              </button>
            ))
          )}
        </nav>

        {/* Sidebar footer */}
        <div className="border-t border-[#e5e5e5] px-3 py-2 space-y-0.5">
          <button
            onClick={() => navigate('/documents')}
            className="w-full text-left flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-[13px] text-[#525252] hover:bg-[#fafafa] transition-colors"
          >
            <FileText size={14} className="opacity-60 shrink-0" />
            <span className="font-medium">Documents</span>
          </button>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-2.5 text-[13px] text-[#737373] hover:text-[#dc2626] px-2.5 py-2 rounded-lg hover:bg-red-50 transition-colors"
          >
            <LogOut size={13} className="shrink-0" />
            <span className="font-medium">Sign out</span>
          </button>
        </div>
      </aside>

      {/* ── Main Chat Area ── */}
      <main className="flex-1 flex flex-col min-w-0">
        {!sessionId ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center max-w-sm">
              <div className="w-12 h-12 rounded-xl bg-white border border-[#e5e5e5] shadow-sm flex items-center justify-center mx-auto mb-4">
                <MessageSquare size={20} className="text-[#ccc]" />
              </div>
              <p className="text-[14px] font-medium text-[#525252] mb-1.5">Start a conversation</p>
              <p className="text-[13px] text-[#999] leading-relaxed">
                Create a new conversation to start asking questions. The assistant will answer using only your uploaded documents, citing its sources.
              </p>
            </div>
          </div>
        ) : (
          <>
            {/* Messages */}
            <div className="flex-1 overflow-auto custom-scrollbar px-6 py-6">
              {loadingMessages ? (
                <div className="space-y-3">{[1, 2, 3, 4].map(i => <div key={i} className="skeleton h-14 w-3/4" style={{ marginLeft: i % 2 === 0 ? 'auto' : 0 }} />)}</div>
              ) : messages.length === 0 && !streaming ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center max-w-sm">
                    <div className="w-12 h-12 rounded-xl bg-white border border-[#e5e5e5] flex items-center justify-center mx-auto mb-4 shadow-sm">
                      <BookOpen size={20} className="text-[#ccc]" />
                    </div>
                    <p className="text-[14px] font-medium text-[#525252] mb-1">Ask a question</p>
                    <p className="text-[13px] text-[#999]">The assistant will answer strictly from your uploaded documents, citing its sources.</p>
                  </div>
                </div>
              ) : (
                <>
                  {messages.map((msg, i) => (
                    <MessageBubble key={i} role={msg.role} text={msg.text} sources={msg.sources} />
                  ))}
                  {streaming && (
                    <MessageBubble role="assistant" text={streamText} sources={streamSources} isStreaming />
                  )}
                  <div ref={messagesEndRef} />
                </>
              )}
            </div>

            {/* Error */}
            {error && (
              <div className="px-6 pb-2">
                <div className="flex items-start gap-2 bg-[#fef2f2] border border-[#fecaca] text-[#b91c1c] text-[13px] px-3 py-2 rounded-lg">
                  <AlertCircle size={13} className="mt-0.5 shrink-0" />
                  <span>{error}</span>
                </div>
              </div>
            )}

            {/* Input */}
            <form onSubmit={handleSend} className="px-6 pb-5 pt-2">
              <div className="flex items-center gap-2 bg-white border border-[#d9d9d9] rounded-xl px-4 py-2.5 focus-within:border-[#0f766e] focus-within:shadow-[0_0_0_3px_rgba(15,118,110,0.08)] transition-all">
                <input
                  ref={inputRef}
                  type="text"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  placeholder={streaming ? 'Waiting for response…' : 'Ask a question about your documents…'}
                  disabled={streaming}
                  className="flex-1 bg-transparent text-[14px] text-[#1a1a1a] placeholder-[#b0b0b0] outline-none disabled:opacity-50"
                />
                <button
                  type="submit"
                  disabled={!input.trim() || streaming}
                  className="w-8 h-8 flex items-center justify-center bg-[#0f766e] hover:bg-[#115e59] disabled:opacity-25 disabled:hover:bg-[#0f766e] text-white rounded-lg transition-colors shrink-0"
                >
                  {streaming ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
                </button>
              </div>
            </form>
          </>
        )}
      </main>
    </div>
  )
}
