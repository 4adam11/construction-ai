// Every backend response follows one envelope:
// { success: boolean, feature: string, mode: "live" | "mock", data: object | null, error: string | null }
// This helper enforces that contract so components only ever see `data` or a thrown Error.

async function request(path, options) {
  let res
  try {
    res = await fetch(`/api${path}`, options)
  } catch {
    throw new Error('Cannot reach the backend. Is the FastAPI server running on port 8000?')
  }
  let body
  try {
    body = await res.json()
  } catch {
    throw new Error(`Server returned an invalid response (HTTP ${res.status}).`)
  }
  if (typeof body !== 'object' || body === null || !('success' in body)) {
    throw new Error('Server response did not match the expected contract.')
  }
  if (!body.success || !body.data) {
    throw new Error(body.error || `Request failed (HTTP ${res.status}).`)
  }
  return { data: body.data, mode: body.mode }
}

export const postJSON = (path, payload) =>
  request(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })

export const postForm = (path, fields) => {
  const form = new FormData()
  Object.entries(fields).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') form.append(k, v)
  })
  return request(path, { method: 'POST', body: form })
}

export const getHealth = async () => {
  const res = await fetch('/api/health')
  if (!res.ok) throw new Error('unhealthy')
  return res.json()
}
