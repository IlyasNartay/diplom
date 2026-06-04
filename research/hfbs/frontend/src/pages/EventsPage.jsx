/**
 * src/pages/EventsPage.jsx
 * Список событий — главная страница
 */
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { eventsAPI } from '../services/api'
import useStore from '../store/useStore'
import { getActiveBackend } from '../services/api'

function EventCard({ event, onSelect }) {
  return (
    <div
      className="card fade-in"
      style={{ cursor: 'pointer', transition: 'border-color 0.2s, transform 0.2s' }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = 'var(--accent)'
        e.currentTarget.style.transform = 'translateY(-2px)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = 'var(--border)'
        e.currentTarget.style.transform = 'translateY(0)'
      }}
      onClick={() => onSelect(event)}
    >
      {/* Event image */}
      <div style={{
        height: 140,
        background: `linear-gradient(135deg, var(--bg3), var(--bg2))`,
        borderRadius: 2,
        marginBottom: '1rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: '3rem',
        border: '1px solid var(--border)',
      }}>
        🎭
      </div>

      <h3 style={{ fontSize: '1.1rem', fontWeight: 800, marginBottom: '0.4rem' }}>{event.title}</h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem', marginBottom: '1rem' }}>
        <span style={{ fontFamily: 'var(--mono)', fontSize: '0.78rem', color: 'var(--text2)' }}>
          📍 {event.venue}
        </span>
        <span style={{ fontFamily: 'var(--mono)', fontSize: '0.78rem', color: 'var(--text2)' }}>
          📅 {new Date(event.date).toLocaleDateString('ru-RU', {
            day: '2-digit', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit'
          })}
        </span>
        <span style={{ fontFamily: 'var(--mono)', fontSize: '0.78rem', color: 'var(--accent)' }}>
          💺 {event.total_seats} мест
        </span>
      </div>

      <p style={{ color: 'var(--text2)', fontSize: '0.85rem', marginBottom: '1rem', lineHeight: 1.5 }}>
        {event.description?.slice(0, 100)}...
      </p>

      <button className="btn btn-primary" style={{ width: '100%' }}>
        Выбрать место →
      </button>
    </div>
  )
}

export default function EventsPage() {
  const [events,  setEvents]  = useState([])
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)
  const navigate     = useNavigate()
  const setSelected  = useStore((s) => s.setSelectedEvent)
  const backend      = getActiveBackend()

  useEffect(() => {
    eventsAPI.list()
      .then((r) => setEvents(r.data))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const handleSelect = (event) => {
    setSelected(event)
    navigate(`/events/${event.id}/seats`)
  }

  return (
    <div className="page">
      <div className="container">
        {/* Header */}
        <div style={{ marginBottom: '2.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem', marginBottom: '0.5rem' }}>
            <h1 style={{ fontSize: '2rem', fontWeight: 800 }}>Предстоящие события</h1>
            <span className={`tag tag-${backend}`}>{backend}</span>
          </div>
          <p style={{ color: 'var(--text2)', fontFamily: 'var(--mono)', fontSize: '0.85rem' }}>
            High-Frequency Booking System — выберите событие для покупки билета
          </p>
        </div>

        {/* Loading */}
        {loading && (
          <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text2)' }}>
            <div className="pulse" style={{ fontSize: '2rem', marginBottom: '1rem' }}>⟳</div>
            <span className="mono">Загрузка событий...</span>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="card" style={{ borderColor: 'var(--accent2)', color: 'var(--accent2)', textAlign: 'center' }}>
            <p>Ошибка загрузки: {error}</p>
            <p style={{ fontSize: '0.8rem', marginTop: '0.5rem', color: 'var(--text2)' }}>
              Убедитесь что backend запущен на порту {backend === 'fastapi' ? '8001' : '8000'}
            </p>
          </div>
        )}

        {/* Events grid */}
        {!loading && !error && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
            gap: '1.5rem',
          }}>
            {events.length === 0 ? (
              <div className="card" style={{ gridColumn: '1/-1', textAlign: 'center', color: 'var(--text2)' }}>
                <p>Событий пока нет. Добавьте через Django Admin (/admin/).</p>
              </div>
            ) : (
              events.map((e) => (
                <EventCard key={e.id} event={e} onSelect={handleSelect} />
              ))
            )}
          </div>
        )}

        {/* Mock data hint */}
        {!loading && !error && events.length === 0 && (
          <div style={{ marginTop: '1rem', padding: '1rem', background: 'var(--bg3)', borderRadius: 'var(--radius)', fontFamily: 'var(--mono)', fontSize: '0.78rem', color: 'var(--text2)' }}>
            <strong style={{ color: 'var(--accent)' }}>Hint:</strong> Запустите seed-скрипт:<br/>
            <code style={{ color: 'var(--text)' }}>docker exec hfbs_django python manage.py shell -c "exec(open('seed.py').read())"</code>
          </div>
        )}
      </div>
    </div>
  )
}
