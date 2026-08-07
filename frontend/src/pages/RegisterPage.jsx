import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { registerUser } from '../api/auth'
import { UserPlus, AlertCircle, Loader2 } from 'lucide-react'

export default function RegisterPage() {
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const data = await registerUser(email, password, fullName)
      login(data.accessToken, { email, fullName })
      navigate('/documents')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-start bg-stone-100 px-6 lg:px-20">
      <div className="w-full max-w-sm">
        <h1 className="text-3xl font-bold text-stone-900 mb-1">Create Account</h1>
        <p className="text-stone-500 mb-8 text-sm">Set up your account to start uploading documents and asking questions.</p>

        {error && (
          <div className="flex items-start gap-2 bg-red-50 border border-red-200 text-red-700 text-sm px-3 py-2.5 rounded-md mb-4">
            <AlertCircle size={16} className="mt-0.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="reg-name" className="block text-sm font-medium text-stone-700 mb-1">Full Name</label>
            <input
              id="reg-name"
              type="text"
              required
              value={fullName}
              onChange={e => setFullName(e.target.value)}
              className="w-full px-3 py-2 border border-stone-300 rounded-md text-sm bg-white text-stone-900 focus:outline-none focus:ring-2 focus:ring-teal-600 focus:border-transparent"
              placeholder="Jane Doe"
            />
          </div>
          <div>
            <label htmlFor="reg-email" className="block text-sm font-medium text-stone-700 mb-1">Email</label>
            <input
              id="reg-email"
              type="email"
              required
              value={email}
              onChange={e => setEmail(e.target.value)}
              className="w-full px-3 py-2 border border-stone-300 rounded-md text-sm bg-white text-stone-900 focus:outline-none focus:ring-2 focus:ring-teal-600 focus:border-transparent"
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label htmlFor="reg-password" className="block text-sm font-medium text-stone-700 mb-1">Password</label>
            <input
              id="reg-password"
              type="password"
              required
              minLength={8}
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="w-full px-3 py-2 border border-stone-300 rounded-md text-sm bg-white text-stone-900 focus:outline-none focus:ring-2 focus:ring-teal-600 focus:border-transparent"
              placeholder="Min 8 characters"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 bg-teal-700 hover:bg-teal-800 disabled:opacity-50 text-white font-medium py-2.5 px-4 rounded-md text-sm transition-colors"
          >
            {loading ? <Loader2 size={16} className="animate-spin" /> : <UserPlus size={16} />}
            {loading ? 'Creating account...' : 'Create account'}
          </button>
        </form>

        <p className="mt-6 text-sm text-stone-500">
          Already have an account?{' '}
          <Link to="/login" className="text-teal-700 hover:text-teal-800 font-medium">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
