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

/* ── Citation Block (USP #2 visual proof) ── */
function CitationBlock({ sources }) {
  if (!sources || (Array.isArray(sources) && sources.length === 0)) return null

  const items = Array.isArray(sources) ? sources : []
  if (items.length === 0) return null

  return (
    <div className="mt-3 border border-teal-200 bg-teal-50 rounded-md p-3">
      <div className="flex items-center gap-1.5 text-xs font-semibold text-teal-800 uppercase tracking-wider mb-2">
        <BookOpen size={13} />
        Sources from your documents
      </div>
      <ul className="space-y-1.5">
        {items.map((src, i) => (
          <li key={i} className="text-xs text-teal-900 flex items-start gap-1.5">
            <ChevronRight size={12} className="mt-0.5 shrink-0 text-teal-500" />
            <span>
              {src.documentName && <span className="font-medium">{src.documentName}</span>}
              {src.chunkText && <span className="text-teal-700 ml-1">— {src.chunkText.slice(0, 150)}{src.chunkText.length > 150 ? '...' : ''}</span>}
              {!src.chunkText && !src.documentName && <span className="text-teal-700">{JSON.stringify(src).slice(0, 150)}</span>}
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}

/* ── Honest Fallback Indicator ── */
function FallbackIndicator() {
  return (
    <div className="mt-3 border border-amber-200 bg-amber-50 rounded-md p-3 flex items-start gap-2">
      <ShieldAlert size={16} className="text-amber-600 mt-0.5 shrink-0" />
      <div>
        <p className="text-xs font-semibold text-amber-800">No matching documents found</p>
        <p className="text-xs text-amber-700 mt-0.5">The system could not find relevant information in your uploaded documents to answer this question. This is an honest admission, not an error.</p>
      </div>
    </div>
  )
}

/* ── Single Message Bubble ── */
function MessageBubble({ role, text, sources, isStreaming }) {
  const isUser = role === 'user'
  const hasSources = sources && Array.isArray(sources) && sources.length > 0
  const isFallback = !isUser && !isStreaming && sources && Array.isArray(sources) && sources.length === 0

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-[75%] ${isUser ? 'bg-teal-700 text-white rounded-l-lg rounded-tr-lg' : 'bg-white border border-stone-200 text-stone-800 rounded-r-lg rounded-tl-lg'} px-4 py-3 text-sm leading-relaxed`}>
        <p className={`whitespace-pre-wrap ${isStreaming ? 'typing-caret' : ''}`}>{text || (isStreaming ? '' : '...')}</p>
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

  // Load sessions
  useEffect(() => {
    listSessions(token)
      .then(setSessions)
      .catch(err => setError(err.message))
      .finally(() => setLoadingSessions(false))
  }, [token])

  // Load messages when session changes
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
    <div className="h-screen flex bg-stone-100">
      {/* ── Sidebar ── */}
      <aside className="w-64 shrink-0 bg-white border-r border-stone-200 flex flex-col">
        <div className="px-4 py-3 border-b border-stone-200">
          <h1 className="text-sm font-bold text-stone-900">Knowledge Assistant</h1>
        </div>

        <div className="px-3 pt-3">
          <button
            onClick={handleNewSession}
            disabled={creatingSess}
            className="w-full flex items-center justify-center gap-1.5 bg-teal-700 hover:bg-teal-800 disabled:opacity-50 text-white font-medium py-2 px-3 rounded-md text-sm transition-colors"
          >
            {creatingSess ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />}
            New conversation
          </button>
        </div>

        <nav className="flex-1 overflow-auto custom-scrollbar px-2 py-2 space-y-0.5">
          {loadingSessions ? (
            <div className="space-y-2 px-1 pt-2">{[1, 2, 3].map(i => <div key={i} className="skeleton h-8 w-full" />)}</div>
          ) : sessions.length === 0 ? (
            <p className="text-xs text-stone-400 px-2 pt-4 text-center">No conversations yet. Start one above.</p>
          ) : (
            sessions.map(s => (
              <button
                key={s.id}
                onClick={() => navigate(`/chat/${s.id}`)}
                className={`w-full text-left flex items-center gap-2 px-2.5 py-2 rounded-md text-sm transition-colors ${s.id === sessionId ? 'bg-teal-50 text-teal-800 font-medium' : 'text-stone-600 hover:bg-stone-50'}`}
              >
                <MessageSquare size={14} className="shrink-0 opacity-50" />
                <span className="truncate">{s.title}</span>
              </button>
            ))
          )}
        </nav>

        <div className="border-t border-stone-200 px-3 py-2 space-y-1">
          <button
            onClick={() => navigate('/documents')}
            className="w-full flex items-center gap-2 text-sm text-stone-600 hover:text-teal-700 px-2 py-1.5 rounded transition-colors"
          >
            <FileText size={14} /> Documents
          </button>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-2 text-sm text-stone-500 hover:text-red-600 px-2 py-1.5 rounded transition-colors"
          >
            <LogOut size={14} /> Sign out
          </button>
        </div>
      </aside>

      {/* ── Main Chat Area ── */}
      <main className="flex-1 flex flex-col min-w-0">
        {!sessionId ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <MessageSquare size={40} className="mx-auto mb-3 text-stone-300" />
              <p className="text-sm font-medium text-stone-500">Select a conversation or start a new one</p>
              <p className="text-xs text-stone-400 mt-1">Your uploaded documents will be used as the knowledge base for answers.</p>
            </div>
          </div>
        ) : (
          <>
            {/* Messages */}
            <div className="flex-1 overflow-auto custom-scrollbar px-6 py-6">
              {loadingMessages ? (
                <div className="space-y-3">{[1, 2, 3, 4].map(i => <div key={i} className="skeleton h-16 w-3/4" style={{ marginLeft: i % 2 === 0 ? 'auto' : 0 }} />)}</div>
              ) : messages.length === 0 && !streaming ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <BookOpen size={36} className="mx-auto mb-3 text-stone-300" />
                    <p className="text-sm font-medium text-stone-500">Ask a question about your documents</p>
                    <p className="text-xs text-stone-400 mt-1">The assistant will answer strictly from your uploaded files, citing its sources.</p>
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
                <div className="flex items-start gap-2 bg-red-50 border border-red-200 text-red-700 text-sm px-3 py-2 rounded-md">
                  <AlertCircle size={14} className="mt-0.5 shrink-0" />
                  <span>{error}</span>
                </div>
              </div>
            )}

            {/* Input */}
            <form onSubmit={handleSend} className="px-6 pb-4 pt-2">
              <div className="flex items-center gap-2 bg-white border border-stone-300 rounded-lg px-3 py-2 focus-within:ring-2 focus-within:ring-teal-600 focus-within:border-transparent transition-shadow">
                <input
                  ref={inputRef}
                  type="text"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  placeholder={streaming ? 'Waiting for response...' : 'Ask a question about your documents...'}
                  disabled={streaming}
                  className="flex-1 bg-transparent text-sm text-stone-800 placeholder-stone-400 outline-none disabled:opacity-50"
                />
                <button
                  type="submit"
                  disabled={!input.trim() || streaming}
                  className="bg-teal-700 hover:bg-teal-800 disabled:opacity-30 disabled:cursor-not-allowed text-white p-1.5 rounded-md transition-colors"
                >
                  {streaming ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
                </button>
              </div>
            </form>
          </>
        )}
      </main>
    </div>
  )
}
