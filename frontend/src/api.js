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
  const body = response.status === 204 ? null : await response.json()
  if (!response.ok) {
    const detail = body?.detail || Object.values(body || {}).flat().join(' ') || 'Не удалось выполнить операцию.'
    throw new Error(detail)
  }
  return body
}

export async function listRampImages(kind) {
  return parseResponse(await fetch(`/api/ramp/images/?kind=${kind}`))
}

export async function uploadRampImage(formData, token) {
  return parseResponse(await fetch('/api/ramp/images/', { method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: formData }))
}

export async function updateRampImage(id, fields, token) {
  return parseResponse(await fetch(`/api/ramp/images/${id}/`, { method: 'PATCH', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify(fields) }))
}

export async function deleteRampImage(id, token) {
  return parseResponse(await fetch(`/api/ramp/images/${id}/`, { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } }))
}

export async function requestEmailCode(fields) {
  return parseResponse(await fetch('/api/ramp/account/request-code/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(fields) }))
}

export async function requestLoginCode(email) {
  return parseResponse(await fetch('/api/ramp/account/login/request-code/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email }) }))
}

export async function verifyEmailCode(email, code) {
  return parseResponse(await fetch('/api/ramp/account/verify-code/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, code }) }))
}

export async function getAccount(token) {
  return parseResponse(await fetch('/api/ramp/account/me/', { headers: { Authorization: `Bearer ${token}` } }))
}

export async function getSavedProjects(token) {
  return parseResponse(await fetch('/api/ramp/account/projects/', { headers: { Authorization: `Bearer ${token}` } }))
}

export async function saveProject(token, fields) {
  return parseResponse(await fetch('/api/ramp/account/projects/', { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify(fields) }))
}

export async function sendTechnicalBrief(token, fields) {
  return parseResponse(await fetch('/api/ramp/account/briefs/', { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify(fields) }))
}

export async function sendTechnicalBriefPdf(token, fields) {
  return parseResponse(await fetch('/api/ramp/account/briefs/pdf/', { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify(fields) }))
}

export async function downloadTechnicalBriefPdf(token, id) {
  const response = await fetch(`/api/ramp/account/briefs/${id}/pdf/`, { headers: { Authorization: `Bearer ${token}` } })
  if (!response.ok) throw new Error('Не удалось скачать PDF.')
  const url = URL.createObjectURL(await response.blob())
  const link = document.createElement('a')
  link.href = url; link.download = `ramp-technical-brief-${id}.pdf`; link.click()
  setTimeout(() => URL.revokeObjectURL(url), 60000)
}

export async function getAdminSettings() {
  return parseResponse(await fetch('/api/ramp/admin/settings/'))
}

export async function loginAdmin(username, password) {
  return parseResponse(await fetch('/api/ramp/admin/login/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password }) }))
}

export async function saveAdminSettings(token, fields) {
  return parseResponse(await fetch('/api/ramp/admin/settings/', { method: 'PUT', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify(fields) }))
}

export async function getAdminBriefs(token) {
  return parseResponse(await fetch('/api/ramp/admin/briefs/', { headers: { Authorization: `Bearer ${token}` } }))
}

export async function getAdminProjects(token) {
  return parseResponse(await fetch('/api/ramp/admin/projects/', { headers: { Authorization: `Bearer ${token}` } }))
}

