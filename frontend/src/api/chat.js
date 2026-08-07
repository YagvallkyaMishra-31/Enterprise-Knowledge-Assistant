const BASE = '/api/chat/sessions'

function authHeaders(token) {
  return {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  }
}

export async function listSessions(token) {
  const res = await fetch(BASE, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error(`Failed to list sessions (${res.status})`)
  return res.json()
}

export async function createSession(token, title) {
  const res = await fetch(BASE, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify({ title: title || null }),
  })
  if (!res.ok) throw new Error(`Failed to create session (${res.status})`)
  return res.json()
}

export async function getSessionMessages(token, sessionId) {
  const res = await fetch(`${BASE}/${sessionId}/messages`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error(`Failed to load messages (${res.status})`)
  return res.json()
}

/**
 * Sends a question and returns a ReadableStream reader for SSE consumption.
 * Uses fetch + ReadableStream because EventSource doesn't support custom headers (JWT).
 */
export async function askQuestionStream(token, sessionId, question) {
  const res = await fetch(`${BASE}/${sessionId}/ask`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify({ question }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.message || `Ask failed (${res.status})`)
  }
  return res.body
}

/**
 * Parses an SSE text stream into typed events.
 * Handles the Spring Boot SseEmitter format:
 *   event: token\ndata: {"type":"token","text":"..."}\n\n
 */
export async function* parseSSEStream(body) {
  const reader = body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop()

      let currentEvent = null
      for (const line of lines) {
        if (line.startsWith('event:')) {
          currentEvent = line.slice(6).trim()
        } else if (line.startsWith('data:')) {
          const data = line.slice(5).trim()
          if (data) {
            try {
              const parsed = JSON.parse(data)
              yield { event: currentEvent || parsed.type, data: parsed }
            } catch {
              yield { event: currentEvent || 'unknown', data: { raw: data } }
            }
          }
          currentEvent = null
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}
