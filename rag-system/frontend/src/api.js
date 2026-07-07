// API client — same-origin /api/*; nginx already enforced basic auth,
// the browser keeps sending the Authorization header automatically.
async function request(path, options = {}) {
  const res = await fetch(path, options)
  if (!res.ok) {
    let detail = res.statusText
    try { detail = (await res.json()).detail || detail } catch { /* noop */ }
    throw new Error(`${res.status}: ${JSON.stringify(detail)}`)
  }
  return res
}

export async function apiJson(path, options = {}) {
  const res = await request(path, options)
  return res.json()
}

export function post(path, body) {
  return apiJson(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

export function put(path, body) {
  return apiJson(path, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

export function del(path) {
  return apiJson(path, { method: 'DELETE' })
}

export async function uploadFile(file, visibilityLevel) {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('visibility_level', visibilityLevel)
  return apiJson('/api/upload', { method: 'POST', body: fd })
}

export async function downloadExport(historyId, format) {
  const res = await request(`/api/export/${historyId}?format=${format}`)
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  const ext = { markdown: 'md', word: 'docx', excel: 'xlsx' }[format]
  a.href = url
  a.download = `rag_result_${historyId}.${ext}`
  a.click()
  URL.revokeObjectURL(url)
}
