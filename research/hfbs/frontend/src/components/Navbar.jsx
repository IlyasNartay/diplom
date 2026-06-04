/**
 * src/components/Navbar.jsx
 * Верхняя навигация + переключатель backend (Django / FastAPI)
 */
import { Link, useNavigate } from 'react-router-dom'
import useStore from '../store/useStore'
import { getActiveBackend, switchBackend } from '../services/api'

export default function Navbar() {
  const { token, username, logout } = useStore()
  const navigate  = useNavigate()
  const backend   = getActiveBackend()

  const handleLogout = () => { logout(); navigate('/login') }

  return (
    <nav style={{
      background: 'var(--bg2)',
      borderBottom: '1px solid var(--border)',
      height: 64,
      display: 'flex',
      alignItems: 'center',
      position: 'sticky',
      top: 0,
      zIndex: 100,
    }}>
      <div className="container" style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        width: '100%',
      }}>
        {/* Logo */}
        <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', textDecoration: 'none' }}>
          <span style={{ fontSize: '1.3rem' }}>⚡</span>
          <span style={{ fontFamily: 'var(--mono)', fontWeight: 700, fontSize: '1rem', color: 'var(--text)', letterSpacing: '0.05em' }}>
            HFBS
          </span>
          <span style={{ color: 'var(--text2)', fontSize: '0.75rem', fontFamily: 'var(--mono)' }}>
            booking system
          </span>
        </Link>

        {/* Right side */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>

          {/* Backend switcher */}
          <div style={{
            display: 'flex',
            background: 'var(--bg3)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius)',
            overflow: 'hidden',
            fontSize: '0.72rem',
          }}>
            {['django', 'fastapi'].map((b) => (
              <button
                key={b}
                onClick={() => switchBackend(b)}
                style={{
                  padding: '0.3rem 0.8rem',
                  border: 'none',
                  background: backend === b ? (b === 'fastapi' ? 'var(--accent)' : '#09bc8a') : 'transparent',
                  color: backend === b ? '#fff' : 'var(--text2)',
                  fontFamily: 'var(--mono)',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
              >
                {b === 'django' ? '🐍 Django' : '⚡ FastAPI'}
              </button>
            ))}
          </div>

          {/* Auth */}
          {token ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
              <span style={{ fontFamily: 'var(--mono)', fontSize: '0.8rem', color: 'var(--text2)' }}>
                {username}
              </span>
              <button className="btn btn-ghost" style={{ padding: '0.3rem 0.8rem', fontSize: '0.8rem' }} onClick={handleLogout}>
                Выйти
              </button>
            </div>
          ) : (
            <Link to="/login" className="btn btn-primary" style={{ padding: '0.35rem 1rem', fontSize: '0.8rem' }}>
              Войти
            </Link>
          )}
        </div>
      </div>
    </nav>
  )
}
