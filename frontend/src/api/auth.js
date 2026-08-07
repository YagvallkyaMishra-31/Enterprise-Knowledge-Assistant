const BASE = '/api/auth'

export async function loginUser(email, password) {
  const res = await fetch(`${BASE}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    let msg = err.message || err.error || `Login failed (${res.status})`
    if (err.details && typeof err.details === 'object') {
      const details = Object.entries(err.details).map(([k, v]) => `${k}: ${v}`).join(', ')
      msg += ` - ${details}`
    }
    throw new Error(msg)
  }
  return res.json()
}

export async function registerUser(email, password, fullName) {
  const res = await fetch(`${BASE}/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, fullName }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    let msg = err.message || err.error || `Registration failed (${res.status})`
    if (err.details && typeof err.details === 'object') {
      const details = Object.entries(err.details).map(([k, v]) => `${k}: ${v}`).join(', ')
      msg += ` - ${details}`
    }
    throw new Error(msg)
  }
  return res.json()
}
