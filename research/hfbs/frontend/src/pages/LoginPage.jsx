/**
 * src/pages/LoginPage.jsx
 * Страница авторизации — поддерживает оба backend
 */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { authAPI, getActiveBackend } from '../services/api'
import useStore from '../store/useStore'

export default function LoginPage() {
  const navigate  = useNavigate()
  const setAuth   = useStore((s) => s.setAuth)
  const backend   = getActiveBackend()

  const [tab,      setTab]      = useState('login') // 'login' | 'register'
  const [username, setUsername] = useState('testuser')
  const [email,    setEmail]    = useState('test@hfbs.dev')
  const [password, setPassword] = useState('testpass123')
  const [loading,  setLoading]  = useState(false)
  const [error,    setError]    = useState(null)
  const [success,  setSuccess]  = useState(null)

  const handleLogin = async () => {
    setLoading(true); setError(null)
    try {
      const data = await authAPI.login(username, password)
      setAuth(data.access_token, username)
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || err.response?.data?.non_field_errors?.[0] || 'Ошибка авторизации')
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async () => {
    setLoading(true); setError(null); setSuccess(null)
    try {
      await fetch // FastAPI has /register, Django has it via DRF
      const res = await fetch(
        `${backend === 'fastapi' ? 'http://localhost:8001' : 'http://localhost:8000'}/api/v1/auth/register/`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, email, password }),
        }
      )
      if (!res.ok) {
        const d = await res.json()
        throw new Error(d.detail || d.error || 'Ошибка регистрации')
      }
      setSuccess('Аккаунт создан! Теперь войдите.')
      setTab('login')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ width: '100%', maxWidth: 400 }}>

        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>⚡</div>
          <h1 style={{ fontFamily: 'var(--mono)', fontSize: '1.4rem', fontWeight: 700, letterSpacing: '0.1em' }}>HFBS</h1>
          <p style={{ color: 'var(--text2)', fontSize: '0.8rem', fontFamily: 'var(--mono)' }}>
            high-frequency booking system
          </p>
          <span className={`tag tag-${backend}`} style={{ marginTop: '0.5rem' }}>
            {backend === 'fastapi' ? '⚡ FastAPI backend' : '🐍 Django backend'}
          </span>
        </div>

        <div className="card">
          {/* Tabs */}
          <div style={{ display: 'flex', marginBottom: '1.5rem', background: 'var(--bg3)', borderRadius: 'var(--radius)', padding: 3 }}>
            {['login', 'register'].map((t) => (
              <button
                key={t}
                onClick={() => { setTab(t); setError(null); setSuccess(null) }}
                style={{
                  flex: 1, padding: '0.5rem',
                  background: tab === t ? 'var(--accent)' : 'transparent',
                  color: tab === t ? '#fff' : 'var(--text2)',
                  border: 'none',
                  borderRadius: 2,
                  fontFamily: 'var(--mono)',
                  fontSize: '0.8rem',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
              >
                {t === 'login' ? 'Войти' : 'Регистрация'}
              </button>
            ))}
          </div>

          {/* Fields */}
          <div style={{ marginBottom: '0.8rem' }}>
            <label style={{ display: 'block', fontFamily: 'var(--mono)', fontSize: '0.72rem', color: 'var(--text2)', marginBottom: '0.3rem', letterSpacing: '0.1em' }}>
              ЛОГИН
            </label>
            <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="username" />
          </div>

          {tab === 'register' && (
            <div style={{ marginBottom: '0.8rem' }}>
              <label style={{ display: 'block', fontFamily: 'var(--mono)', fontSize: '0.72rem', color: 'var(--text2)', marginBottom: '0.3rem', letterSpacing: '0.1em' }}>
                EMAIL
              </label>
              <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="user@example.com" type="email" />
            </div>
          )}

          <div style={{ marginBottom: '1.2rem' }}>
            <label style={{ display: 'block', fontFamily: 'var(--mono)', fontSize: '0.72rem', color: 'var(--text2)', marginBottom: '0.3rem', letterSpacing: '0.1em' }}>
              ПАРОЛЬ
            </label>
            <input
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="password"
              type="password"
              onKeyDown={(e) => e.key === 'Enter' && (tab === 'login' ? handleLogin() : handleRegister())}
            />
          </div>

          {error && (
            <div style={{
              background: 'rgba(255,107,107,0.1)', border: '1px solid var(--accent2)',
              borderRadius: 'var(--radius)', padding: '0.7rem',
              color: 'var(--accent2)', fontFamily: 'var(--mono)', fontSize: '0.8rem',
              marginBottom: '1rem',
            }}>
              {error}
            </div>
          )}

          {success && (
            <div style={{
              background: 'rgba(74,222,128,0.1)', border: '1px solid var(--success)',
              borderRadius: 'var(--radius)', padding: '0.7rem',
              color: 'var(--success)', fontFamily: 'var(--mono)', fontSize: '0.8rem',
              marginBottom: '1rem',
            }}>
              {success}
            </div>
          )}

          <button
            className="btn btn-primary"
            style={{ width: '100%', padding: '0.8rem', fontSize: '0.95rem' }}
            onClick={tab === 'login' ? handleLogin : handleRegister}
            disabled={loading}
          >
            {loading ? '⟳ Загрузка...' : tab === 'login' ? '→ Войти' : '+ Создать аккаунт'}
          </button>

          <p style={{ textAlign: 'center', fontFamily: 'var(--mono)', fontSize: '0.72rem', color: 'var(--text2)', marginTop: '1rem' }}>
            Для теста: testuser / testpass123
          </p>
        </div>
      </div>
    </div>
  )
}
