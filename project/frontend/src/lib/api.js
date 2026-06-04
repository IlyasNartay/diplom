import { clearAuthSession, readAuthSession, writeAuthSession } from '@/stores/auth'

const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL
export const API_BASE_URL = configuredApiBaseUrl === undefined ? 'http://localhost:8080' : configuredApiBaseUrl

function buildUrl(path) {
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path
  }
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  if (!API_BASE_URL) {
    return normalizedPath
  }
  return `${API_BASE_URL.replace(/\/$/, '')}${normalizedPath}`
}

function isFormDataBody(body) {
  return typeof FormData !== 'undefined' && body instanceof FormData
}

function buildHeaders(customHeaders = {}, body) {
  const session = readAuthSession()
  const headers = new Headers(customHeaders)
  const hasBody = body !== undefined && body !== null

  if (hasBody && !isFormDataBody(body) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  if (session?.access_token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${session.access_token}`)
  }

  return headers
}

async function parseResponse(response) {
  const contentType = response.headers.get('content-type') || ''
  if (contentType.includes('application/json')) {
    return response.json()
  }
  return response.text()
}

async function refreshAccessToken() {
  const session = readAuthSession()
  if (!session?.refresh_token) {
    return null
  }

  const response = await fetch(buildUrl('/api/auth/refresh'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      refresh_token: session.refresh_token
    })
  })

  if (!response.ok) {
    clearAuthSession()
    return null
  }

  const payload = await response.json()
  const nextSession = {
    ...session,
    ...payload
  }
  writeAuthSession(nextSession)
  return nextSession
}

async function request(path, options = {}, allowRefresh = true) {
  const response = await fetch(buildUrl(path), {
    ...options,
    headers: buildHeaders(options.headers, options.body)
  })

  if (response.status === 401 && allowRefresh) {
    const refreshed = await refreshAccessToken()
    if (refreshed?.access_token) {
      return request(path, options, false)
    }
  }

  const payload = await parseResponse(response)

  if (!response.ok) {
    const message =
      typeof payload === 'string'
        ? payload
        : payload?.detail || payload?.message || 'Request failed'
    throw new Error(message)
  }

  return payload
}

export const api = {
  get(path) {
    return request(path, { method: 'GET' })
  },
  post(path, body, options = {}) {
    return request(path, {
      method: 'POST',
      body: JSON.stringify(body),
      ...options
    })
  },
  postForm(path, body, options = {}) {
    return request(path, {
      method: 'POST',
      body,
      ...options
    })
  },
  put(path, body, options = {}) {
    return request(path, {
      method: 'PUT',
      body: JSON.stringify(body),
      ...options
    })
  },
  patch(path, body, options = {}) {
    return request(path, {
      method: 'PATCH',
      body: JSON.stringify(body),
      ...options
    })
  },
  delete(path, options = {}) {
    return request(path, {
      method: 'DELETE',
      ...options
    })
  }
}
