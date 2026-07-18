const API_URL = '/api/v1'

export async function api(path, options = {}) {
  const token = localStorage.getItem('casa_yeison_token')
  const headers = new Headers(options.headers || {})
  if (token) headers.set('Authorization', `Token ${token}`)
  if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json')

  const response = await fetch(`${API_URL}${path}`, { ...options, headers })
  if (response.status === 401 && path !== '/auth/pin/') {
    localStorage.removeItem('casa_yeison_token')
    window.dispatchEvent(new Event('casa-auth-expired'))
  }
  if (response.status === 204) return null
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    const detail = data.detail || Object.values(data).flat().join(' ') || 'No pudimos completar la solicitud.'
    throw new Error(detail)
  }
  return data
}

export function newIdempotencyKey() {
  return crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`
}
