/**
 * src/services/api.js
 * ───────────────────────────────────────────────────────────
 * Единый API-клиент, который работает с Django И FastAPI.
 *
 * Ключевая идея: оба backend имеют ОДИНАКОВЫЕ эндпоинты.
 * Переключение происходит через переменную VITE_BACKEND.
 *
 * Django  (sync):  http://164.92.180.99:8000
 * FastAPI (async): http://164.92.180.99:8001
 *
 * Используй: localStorage.setItem('backend', 'fastapi') для переключения.
 */
import axios from 'axios'

const DJANGO_URL  = import.meta.env.VITE_DJANGO_URL  || 'http://164.92.180.99:8000'
const FASTAPI_URL = import.meta.env.VITE_FASTAPI_URL || 'http://164.92.180.99:8001'

/** Возвращает текущий активный backend */
export const getActiveBackend = () =>
  localStorage.getItem('backend') || 'django'

/** Возвращает base URL текущего backend */
export const getBaseURL = () =>
  getActiveBackend() === 'fastapi' ? FASTAPI_URL : DJANGO_URL

/** Переключает backend и перезагружает страницу */
export const switchBackend = (backend) => {
  localStorage.setItem('backend', backend)
  window.location.reload()
}

// ── Axios instance ────────────────────────────────────────────
const api = axios.create({
  baseURL: getBaseURL(),
  headers: { 'Content-Type': 'application/json' },
  timeout: 10000,
})

// Автоматически добавляем JWT-токен
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Обрабатываем 401 — редиректим на логин
api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)


// ── Auth API ──────────────────────────────────────────────────

export const authAPI = {
  /**
   * Логин: Django → /api/v1/auth/token/ (JSON body)
   *        FastAPI → /api/v1/auth/token/ (form-data, OAuth2)
   */
  login: async (username, password) => {
    const backend = getActiveBackend()

    if (backend === 'fastapi') {
      // FastAPI использует OAuth2PasswordRequestForm (form-data)
      const form = new URLSearchParams()
      form.append('username', username)
      form.append('password', password)
      const res = await api.post('/api/v1/auth/token/', form, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })
      return res.data // { access_token, token_type }
    } else {
      // Django simplejwt ожидает JSON
      const res = await api.post('/api/v1/auth/token/', { username, password })
      return { access_token: res.data.access }
    }
  },

  register: (username, email, password) =>
    api.post('/api/v1/auth/register/', { username, email, password }),
}


// ── Events API ────────────────────────────────────────────────

export const eventsAPI = {
  list: () => api.get('/api/v1/events/'),
  detail: (id) => api.get(`/api/v1/events/${id}/`),
}


// ── Seats API ─────────────────────────────────────────────────

export const seatsAPI = {
  list: (eventId) => api.get('/api/v1/seats/', { params: { event_id: eventId } }),

  /** Бронь места — возможен HTTP 409 если race condition */
  reserve: (seatId) => api.post(`/api/v1/seats/${seatId}/reserve/`),

  release: (seatId) => api.post(`/api/v1/seats/${seatId}/release/`),
}


// ── Orders API ────────────────────────────────────────────────

export const ordersAPI = {
  create: (seatId) => api.post('/api/v1/orders/', { seat_id: seatId }),
  detail: (orderId) => api.get(`/api/v1/orders/${orderId}/`),
}


// ── Payments API ──────────────────────────────────────────────

export const paymentsAPI = {
  /**
   * Обработка оплаты.
   * Возвращает: { payment_id, order_id, ticket_url }
   */
  process: (orderId, cardToken = 'tok_mock_visa') =>
    api.post('/api/v1/payments/', { order_id: orderId, card_token: cardToken }),
}


// ── Tickets API ───────────────────────────────────────────────

export const ticketsAPI = {
  download: (orderId) =>
    api.get(`/api/v1/tickets/${orderId}/`, { responseType: 'blob' }),
}

export default api
