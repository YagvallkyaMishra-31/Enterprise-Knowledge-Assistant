import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { registerUser } from '../api/auth'
import { ArrowRight, AlertCircle, Loader2, BookOpen, Check, Lock, Cpu } from 'lucide-react'

export default function RegisterPage() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await registerUser(email, password, name)
      navigate('/login')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex w-full bg-[#f7f7f8]">

      {/* ── LEFT: Form ── */}
      <div className="w-full lg:w-[480px] shrink-0 bg-white flex flex-col justify-center px-10 sm:px-14 py-14 border-r border-[#ebebeb]">
        <div className="w-full max-w-[340px] mx-auto">

          {/* Logomark */}
          <div className="mb-12 flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-[#0f766e] flex items-center justify-center">
              <BookOpen size={18} className="text-white" strokeWidth={2.2} />
            </div>
            <span className="text-[15px] font-semibold text-[#1a1a1a] tracking-tight">
              Knowledge Assistant
            </span>
          </div>

          <h1 className="text-[26px] font-semibold text-[#1a1a1a] tracking-tight leading-tight mb-2">
            Create your account
          </h1>
          <p className="text-[14px] text-[#737373] leading-relaxed mb-8">
            Set up access to start uploading documents and chatting with your knowledge base.
          </p>

          {error && (
            <div className="flex items-start gap-2.5 bg-[#fef2f2] border border-[#fecaca] text-[#b91c1c] text-[13px] px-3.5 py-3 rounded-lg mb-6">
              <AlertCircle size={15} className="mt-0.5 shrink-0" />
              <span className="font-medium leading-snug">{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="reg-name" className="block text-[13px] font-medium text-[#525252] mb-2">
                Full name
              </label>
              <input
                id="reg-name"
                type="text"
                required
                value={name}
                onChange={e => setName(e.target.value)}
                className="input-base"
                placeholder="Jane Doe"
              />
            </div>
            <div>
              <label htmlFor="reg-email" className="block text-[13px] font-medium text-[#525252] mb-2">
                Work email
              </label>
              <input
                id="reg-email"
                type="email"
                required
                value={email}
                onChange={e => setEmail(e.target.value)}
                className="input-base"
                placeholder="you@company.com"
              />
            </div>
            <div>
              <label htmlFor="reg-password" className="block text-[13px] font-medium text-[#525252] mb-2">
                Password
              </label>
              <input
                id="reg-password"
                type="password"
                required
                minLength={8}
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="input-base"
                placeholder="Minimum 8 characters"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full mt-1"
            >
              {loading ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                <>
                  Create account
                  <ArrowRight size={15} className="opacity-70" />
                </>
              )}
            </button>
          </form>

          <p className="mt-10 text-[13px] text-[#737373] text-center">
            Already have an account?{' '}
            <Link to="/login" className="text-[#0f766e] font-medium hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </div>

      {/* ── RIGHT: Brand context ── */}
      <div className="hidden lg:flex flex-1 flex-col justify-center px-14 lg:px-20 xl:px-28 relative overflow-hidden bg-[#111111]">

        <div className="relative z-10 max-w-[480px]">
          <h2 className="text-[38px] xl:text-[44px] font-bold text-white leading-[1.15] tracking-tight mb-4">
            Your documents,<br/>one conversation away.
          </h2>
          <p className="text-[16px] text-[#a3a3a3] leading-relaxed mb-12 max-w-[420px]">
            Upload internal docs, research papers, or any text corpus — then ask questions and get cited, accurate answers in seconds.
          </p>

          <div className="space-y-6">
            {[
              { icon: Check, title: 'Cited answers', desc: 'Every response references specific passages from your documents.' },
              { icon: Lock, title: 'Fully self-hosted', desc: 'Your data stays on your infrastructure. Nothing leaves the network.' },
              { icon: Cpu, title: 'Local LLM inference', desc: 'Powered by Ollama — no API keys, no cloud dependencies.' },
            ].map(({ icon: Icon, title, desc }) => (
              <div key={title} className="flex items-start gap-3.5">
                <div className="mt-0.5 w-7 h-7 rounded-md bg-white/[0.06] border border-white/[0.08] flex items-center justify-center shrink-0">
                  <Icon size={14} className="text-[#2dd4bf]" />
                </div>
                <div>
                  <h3 className="text-[14px] font-medium text-white mb-0.5">{title}</h3>
                  <p className="text-[13px] text-[#888] leading-relaxed">{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
