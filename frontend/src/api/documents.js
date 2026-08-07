const BASE = '/api/documents'

function authHeaders(token) {
  return { Authorization: `Bearer ${token}` }
}

export async function listDocuments(token) {
  const res = await fetch(BASE, { headers: authHeaders(token) })
  if (!res.ok) throw new Error(`Failed to list documents (${res.status})`)
  return res.json()
}

export async function uploadDocument(token, file) {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(BASE, {
    method: 'POST',
    headers: authHeaders(token),
    body: form,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.message || `Upload failed (${res.status})`)
  }
  return res.json()
}

export async function deleteDocument(token, id) {
  const res = await fetch(`${BASE}/${id}`, {
    method: 'DELETE',
    headers: authHeaders(token),
  })
  if (!res.ok) throw new Error(`Delete failed (${res.status})`)
}
