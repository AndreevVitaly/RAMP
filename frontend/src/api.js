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

export async function uploadRampImage(formData) {
  return parseResponse(await fetch('/api/ramp/images/', { method: 'POST', body: formData }))
}

export async function updateRampImage(id, fields) {
  return parseResponse(await fetch(`/api/ramp/images/${id}/`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(fields) }))
}

export async function deleteRampImage(id) {
  return parseResponse(await fetch(`/api/ramp/images/${id}/`, { method: 'DELETE' }))
}

export async function requestPhoneCode(fields) {
  return parseResponse(await fetch('/api/ramp/account/request-code/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(fields) }))
}

export async function verifyPhoneCode(phone, code) {
  return parseResponse(await fetch('/api/ramp/account/verify-code/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ phone, code }) }))
}

export async function getAccount(token) {
  return parseResponse(await fetch('/api/ramp/account/me/', { headers: { Authorization: `Bearer ${token}` } }))
}

export async function sendTechnicalBrief(token, fields) {
  return parseResponse(await fetch('/api/ramp/account/briefs/', { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify(fields) }))
}

export async function getAdminSettings() {
  return parseResponse(await fetch('/api/ramp/admin/settings/'))
}

export async function saveAdminSettings(key, fields) {
  return parseResponse(await fetch('/api/ramp/admin/settings/', { method: 'PUT', headers: { 'Content-Type': 'application/json', 'X-Admin-Key': key }, body: JSON.stringify(fields) }))
}

export async function getAdminBriefs(key) {
  return parseResponse(await fetch('/api/ramp/admin/briefs/', { headers: { 'X-Admin-Key': key } }))
}

