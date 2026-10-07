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

