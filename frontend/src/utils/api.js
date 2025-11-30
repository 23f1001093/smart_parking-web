async function parseResponse(res) {
  const text = await res.text()
  let data = null
  try { data = text ? JSON.parse(text) : null } catch (e) { /* not JSON */ }
  return { ok: res.ok, status: res.status, data, text, res }
}

function handle401() {
  
  try { localStorage.removeItem('role') } catch (e) {}
  
}

export async function apiGet(path) {
  const res = await fetch(`/api${path}`, { credentials: 'include' })
  const parsed = await parseResponse(res)
  if (parsed.status === 401) handle401()
  if (!parsed.ok) throw new Error(parsed.data?.message || parsed.text || res.statusText)
  return parsed.data
}

export async function apiPost(path, body) {
  const res = await fetch(`/api${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(body)
  })
  const parsed = await parseResponse(res)
  if (parsed.status === 401) handle401()
  if (!parsed.ok) throw new Error(parsed.data?.message || parsed.text || res.statusText)
  return parsed.data
}

export async function apiPut(path, body) {
  const res = await fetch(`/api${path}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(body)
  })
  const parsed = await parseResponse(res)
  if (parsed.status === 401) handle401()
  if (!parsed.ok) throw new Error(parsed.data?.message || parsed.text || res.statusText)
  return parsed.data
}

export async function apiDelete(path) {
  const res = await fetch(`/api${path}`, {
    method: 'DELETE',
    credentials: 'include'
  })
  const parsed = await parseResponse(res)
  if (parsed.status === 401) handle401()
  if (!parsed.ok) throw new Error(parsed.data?.message || parsed.text || res.statusText)
  return parsed.data
}

export default {
  apiGet,
  apiPost,
  apiPut,
  apiDelete
}