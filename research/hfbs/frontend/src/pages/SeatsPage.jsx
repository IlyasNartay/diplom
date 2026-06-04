/**
 * src/pages/SeatsPage.jsx
 * Интерактивная карта мест с блокировкой через Redis
 *
 * Ключевые моменты:
 * - FREE (синий)     → можно выбрать
 * - RESERVED (жёлт.) → заблокировано, 409 если попытаться взять
 * - SOLD (красный)   → продано
 * - Выбранное (зелёный) → ваш выбор
 */
import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { seatsAPI, ordersAPI } from '../services/api'
import useStore from '../store/useStore'

const STATUS_STYLE = {
  FREE:     { bg: 'var(--bg3)', border: 'var(--accent)',  color: 'var(--accent)',  label: 'Свободно',     cursor: 'pointer' },
  RESERVED: { bg: '#2a2010',    border: 'var(--warning)', color: 'var(--warning)', label: 'Занято',       cursor: 'not-allowed' },
  SOLD:     { bg: '#200a0a',    border: 'var(--accent2)', color: 'var(--accent2)', label: 'Продано',      cursor: 'not-allowed' },
  SELECTED: { bg: '#0a2010',    border: 'var(--success)', color: 'var(--success)', label: 'Ваш выбор',    cursor: 'pointer' },
}

function SeatButton({ seat, isSelected, onSelect }) {
  const st = isSelected ? STATUS_STYLE.SELECTED : STATUS_STYLE[seat.status]
  const disabled = !isSelected && seat.status !== 'FREE'

  return (
    <button
      title={`Ряд ${seat.row}, Место ${seat.number} — ${st.label} — $${seat.price}`}
      onClick={() => !disabled && onSelect(seat)}
      style={{
        width: 36, height: 36,
        background: st.bg,
        border: `1.5px solid ${st.border}`,
        borderRadius: 3,
        color: st.color,
        fontFamily: 'var(--mono)',
        fontSize: '0.65rem',
        fontWeight: 700,
        cursor: st.cursor,
        transition: 'all 0.15s',
        opacity: disabled ? 0.6 : 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
      onMouseEnter={(e) => { if (!disabled) e.currentTarget.style.transform = 'scale(1.15)' }}
      onMouseLeave={(e) => { e.currentTarget.style.transform = 'scale(1)' }}
    >
      {seat.number}
    </button>
  )
}

export default function SeatsPage() {
  const { id: eventId }    = useParams()
  const navigate           = useNavigate()
  const { selectedEvent, selectedSeat, setSelectedSeat, setCurrentOrder } = useStore()

  const [seats,    setSeats]    = useState([])
  const [loading,  setLoading]  = useState(true)
  const [error,    setError]    = useState(null)
  const [locking,  setLocking]  = useState(false)
  const [lockMsg,  setLockMsg]  = useState(null)

  // Загрузка мест
  useEffect(() => {
    seatsAPI.list(eventId)
      .then((r) => setSeats(r.data))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [eventId])

  // Группировка по рядам
  const rows = seats.reduce((acc, s) => {
    acc[s.row] = acc[s.row] || []
    acc[s.row].push(s)
    return acc
  }, {})

  // Статистика
  const stats = {
    free:     seats.filter((s) => s.status === 'FREE').length,
    reserved: seats.filter((s) => s.status === 'RESERVED').length,
    sold:     seats.filter((s) => s.status === 'SOLD').length,
  }

  const handleSeatClick = (seat) => {
    // Если уже выбрано — снять выделение
    if (selectedSeat?.id === seat.id) {
      setSelectedSeat(null)
      return
    }
    setSelectedSeat(seat)
    setLockMsg(null)
  }

  const handleReserve = async () => {
    if (!selectedSeat) return
    setLocking(true)
    setLockMsg(null)

    try {
      // 1. Блокируем место (Redis lock)
      await seatsAPI.reserve(selectedSeat.id)

      // 2. Создаём заказ
      const { data: order } = await ordersAPI.create(selectedSeat.id)
      setCurrentOrder(order)

      // Обновляем статус места локально
      setSeats((prev) =>
        prev.map((s) => s.id === selectedSeat.id ? { ...s, status: 'RESERVED' } : s)
      )

      navigate('/payment')

    } catch (err) {
      if (err.response?.status === 409) {
        // Race condition! Место уже взято
        setLockMsg({ type: 'error', text: `⚡ Race condition! ${err.response.data?.error || 'Место уже занято'}` })
        setSelectedSeat(null)
        // Обновляем список мест
        seatsAPI.list(eventId).then((r) => setSeats(r.data))
      } else {
        setLockMsg({ type: 'error', text: err.response?.data?.error || err.message })
      }
    } finally {
      setLocking(false)
    }
  }

  return (
    <div className="page">
      <div className="container">
        {/* Header */}
        <div style={{ marginBottom: '2rem' }}>
          <button
            className="btn btn-ghost"
            style={{ marginBottom: '1rem', fontSize: '0.8rem', padding: '0.3rem 0.8rem' }}
            onClick={() => navigate('/')}
          >
            ← Назад
          </button>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 800 }}>
            {selectedEvent?.title || `Событие #${eventId}`}
          </h1>
          {selectedEvent && (
            <p style={{ color: 'var(--text2)', fontFamily: 'var(--mono)', fontSize: '0.8rem', marginTop: '0.3rem' }}>
              📍 {selectedEvent.venue} &nbsp;|&nbsp;
              📅 {new Date(selectedEvent.date).toLocaleDateString('ru-RU')}
            </p>
          )}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: '2rem', alignItems: 'start' }}>

          {/* Seat map */}
          <div className="card">
            {/* Stage */}
            <div style={{
              textAlign: 'center',
              padding: '0.6rem',
              background: 'var(--bg3)',
              border: '1px solid var(--border)',
              borderRadius: 2,
              fontFamily: 'var(--mono)',
              fontSize: '0.75rem',
              color: 'var(--text2)',
              marginBottom: '1.5rem',
              letterSpacing: '0.2em',
            }}>
              ▬▬▬▬▬▬▬ СЦЕНА ▬▬▬▬▬▬▬
            </div>

            {loading ? (
              <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text2)' }} className="pulse">
                Загрузка мест...
              </div>
            ) : error ? (
              <div style={{ color: 'var(--accent2)', textAlign: 'center' }}>{error}</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {Object.entries(rows).map(([row, rowSeats]) => (
                  <div key={row} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <span style={{
                      fontFamily: 'var(--mono)', fontSize: '0.65rem', color: 'var(--text2)',
                      width: 20, textAlign: 'right', flexShrink: 0,
                    }}>
                      {row}
                    </span>
                    <div style={{ display: 'flex', gap: '0.3rem', flexWrap: 'wrap' }}>
                      {rowSeats.map((seat) => (
                        <SeatButton
                          key={seat.id}
                          seat={seat}
                          isSelected={selectedSeat?.id === seat.id}
                          onSelect={handleSeatClick}
                        />
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Legend */}
            <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem', flexWrap: 'wrap' }}>
              {[
                { status: 'FREE',     label: 'Свободно' },
                { status: 'RESERVED', label: 'Занято'   },
                { status: 'SOLD',     label: 'Продано'  },
                { status: 'SELECTED', label: 'Выбрано'  },
              ].map(({ status, label }) => {
                const st = STATUS_STYLE[status]
                return (
                  <div key={status} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <div style={{
                      width: 16, height: 16, background: st.bg,
                      border: `1.5px solid ${st.border}`, borderRadius: 2,
                    }} />
                    <span style={{ fontFamily: 'var(--mono)', fontSize: '0.72rem', color: 'var(--text2)' }}>
                      {label}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Sidebar */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>

            {/* Stats */}
            <div className="card">
              <h3 style={{ fontFamily: 'var(--mono)', fontSize: '0.8rem', color: 'var(--text2)', marginBottom: '0.8rem', letterSpacing: '0.1em' }}>
                СТАТИСТИКА
              </h3>
              {[
                { label: 'Свободно', value: stats.free,     color: 'var(--accent)'  },
                { label: 'Занято',   value: stats.reserved, color: 'var(--warning)' },
                { label: 'Продано',  value: stats.sold,     color: 'var(--accent2)' },
              ].map(({ label, value, color }) => (
                <div key={label} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                  <span style={{ fontFamily: 'var(--mono)', fontSize: '0.8rem', color: 'var(--text2)' }}>{label}</span>
                  <span style={{ fontFamily: 'var(--mono)', fontSize: '0.8rem', color, fontWeight: 700 }}>{value}</span>
                </div>
              ))}
            </div>

            {/* Selected seat info */}
            {selectedSeat && (
              <div className="card fade-in" style={{ borderColor: 'var(--success)' }}>
                <h3 style={{ fontFamily: 'var(--mono)', fontSize: '0.8rem', color: 'var(--text2)', marginBottom: '0.8rem' }}>
                  ВЫБРАННОЕ МЕСТО
                </h3>
                <div style={{ fontFamily: 'var(--mono)', display: 'flex', flexDirection: 'column', gap: '0.4rem', marginBottom: '1rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text2)', fontSize: '0.8rem' }}>Ряд</span>
                    <span style={{ color: 'var(--success)', fontWeight: 700 }}>{selectedSeat.row}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text2)', fontSize: '0.8rem' }}>Место</span>
                    <span style={{ color: 'var(--success)', fontWeight: 700 }}>{selectedSeat.number}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text2)', fontSize: '0.8rem' }}>Категория</span>
                    <span style={{ color: 'var(--text)', fontWeight: 700, textTransform: 'capitalize' }}>{selectedSeat.category}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', paddingTop: '0.4rem', borderTop: '1px solid var(--border)' }}>
                    <span style={{ color: 'var(--text2)', fontSize: '0.8rem' }}>Цена</span>
                    <span style={{ color: 'var(--accent)', fontWeight: 700, fontSize: '1.1rem' }}>${selectedSeat.price}</span>
                  </div>
                </div>

                <button
                  className="btn btn-primary"
                  style={{ width: '100%' }}
                  onClick={handleReserve}
                  disabled={locking}
                >
                  {locking ? '⟳ Блокировка...' : '🔒 Забронировать'}
                </button>

                <p style={{ fontSize: '0.7rem', color: 'var(--text2)', fontFamily: 'var(--mono)', marginTop: '0.5rem', textAlign: 'center' }}>
                  Redis lock на 5 минут
                </p>
              </div>
            )}

            {/* Lock message */}
            {lockMsg && (
              <div className="card fade-in" style={{
                borderColor: lockMsg.type === 'error' ? 'var(--accent2)' : 'var(--success)',
                color: lockMsg.type === 'error' ? 'var(--accent2)' : 'var(--success)',
                fontFamily: 'var(--mono)',
                fontSize: '0.82rem',
              }}>
                {lockMsg.text}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
