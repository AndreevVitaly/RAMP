export async function calculateRamp(parameters, signal) {
  const response = await fetch('/api/ramp/calculate/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(parameters),
    signal,
  })
  const body = await response.json()
  if (!response.ok) {
    const detail = body.detail || Object.values(body).flat().join(' ') || 'Не удалось выполнить расчёт.'
    throw new Error(detail)
  }
  return body
}

async function parseResponse(response) {
  const raw = response.status === 204 ? '' : await response.text()
  let body
  try { body = raw ? JSON.parse(raw) : null }
  catch { body = null }
  if (!response.ok) {
    const detail = body?.detail || Object.values(body || {}).flat().join(' ') || 'Не удалось выполнить операцию.'
    const error = new Error(detail)
    error.status = response.status
    throw error
  }
  if (response.status !== 204 && body === null) throw new Error('Сервер вернул некорректный ответ.')
  return body
}

function authHeaders(token) {
  const value = `Bearer ${token}`
  return { Authorization: value, 'X-RAMP-Authorization': value }
}

export async function listRampImages(kind) {
  return parseResponse(await fetch(`/api/ramp/images/?kind=${kind}`))
}

export async function uploadRampImage(formData, token) {
  return parseResponse(await fetch('/api/ramp/images/', { method: 'POST', headers: authHeaders(token), body: formData }))
}

export async function updateRampImage(id, fields, token) {
  return parseResponse(await fetch(`/api/ramp/images/${id}/`, { method: 'PATCH', headers: { 'Content-Type': 'application/json', ...authHeaders(token) }, body: JSON.stringify(fields) }))
}

export async function deleteRampImage(id, token) {
  return parseResponse(await fetch(`/api/ramp/images/${id}/`, { method: 'DELETE', headers: authHeaders(token) }))
}

export async function requestEmailCode(fields) {
  return parseResponse(await fetch('/api/ramp/account/request-code/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(fields) }))
}

export async function registerCustomer(fields) {
  return parseResponse(await fetch('/api/ramp/account/register/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(fields) }))
}

export async function loginCustomer(email, password) {
  return parseResponse(await fetch('/api/ramp/account/login/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, password }) }))
}

export async function requestLoginCode(email) {
  return parseResponse(await fetch('/api/ramp/account/login/request-code/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email }) }))
}

export async function verifyEmailCode(email, code) {
  return parseResponse(await fetch('/api/ramp/account/verify-code/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, code }) }))
}

export async function getAccount(token, signal) {
  return parseResponse(await fetch('/api/ramp/account/me/', { headers: authHeaders(token), signal }))
}

export async function setCustomerPassword(token, fields) {
  return parseResponse(await fetch('/api/ramp/account/password/', { method: 'POST', headers: { 'Content-Type': 'application/json', ...authHeaders(token) }, body: JSON.stringify(fields) }))
}

export async function getSavedProjects(token) {
  return parseResponse(await fetch('/api/ramp/account/projects/', { headers: authHeaders(token) }))
}

export async function saveProject(token, fields) {
  return parseResponse(await fetch('/api/ramp/account/projects/', { method: 'POST', headers: { 'Content-Type': 'application/json', ...authHeaders(token) }, body: JSON.stringify(fields) }))
}

export async function sendTechnicalBrief(token, fields) {
  return parseResponse(await fetch('/api/ramp/account/briefs/', { method: 'POST', headers: { 'Content-Type': 'application/json', ...authHeaders(token) }, body: JSON.stringify(fields) }))
}

export async function sendTechnicalBriefPdf(token, fields) {
  return parseResponse(await fetch('/api/ramp/account/briefs/pdf/', { method: 'POST', headers: { 'Content-Type': 'application/json', ...authHeaders(token) }, body: JSON.stringify(fields) }))
}

async function savePdfResponse(response, filename) {
  if (!response.ok) {
    await parseResponse(response)
    return
  }
  const url = URL.createObjectURL(await response.blob())
  const link = document.createElement('a')
  link.href = url; link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  setTimeout(() => URL.revokeObjectURL(url), 60000)
}

export async function downloadTechnicalBriefPdf(token, id) {
  const response = await fetch(`/api/ramp/account/briefs/${id}/pdf/`, { headers: authHeaders(token) })
  return savePdfResponse(response, `ramp-technical-brief-${id}.pdf`)
}

export async function downloadCurrentBriefPdf(token, fields) {
  const response = await fetch('/api/ramp/account/briefs/pdf/download/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders(token) },
    body: JSON.stringify(fields),
  })
  return savePdfResponse(response, 'ramp-technical-brief.pdf')
}

export async function getAdminSettings() {
  return parseResponse(await fetch('/api/ramp/admin/settings/'))
}

export async function loginAdmin(username, password) {
  return parseResponse(await fetch('/api/ramp/admin/login/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password }) }))
}

export async function saveAdminSettings(token, fields) {
  return parseResponse(await fetch('/api/ramp/admin/settings/', { method: 'PUT', headers: { 'Content-Type': 'application/json', ...authHeaders(token) }, body: JSON.stringify(fields) }))
}

export async function getAdminBriefs(token, signal) {
  return parseResponse(await fetch('/api/ramp/admin/briefs/', { headers: authHeaders(token), signal }))
}

export async function getAdminProjects(token) {
  return parseResponse(await fetch('/api/ramp/admin/projects/', { headers: authHeaders(token) }))
}

export async function getDjangoAdminProject(id, signal) {
  return parseResponse(await fetch(`/api/ramp/admin/projects/${id}/preview/`, { signal }))
}

