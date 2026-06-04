/**
 * src/pages/TicketPage.jsx
 * Страница успешной покупки — показывает билет и кнопку скачивания PDF
 */
import { useNavigate } from 'react-router-dom'
import useStore from '../store/useStore'
import { ticketsAPI, getActiveBackend } from '../services/api'

export default function TicketPage() {
  const navigate = useNavigate()
  const { paymentResult, selectedEvent, selectedSeat, currentOrder, resetBooking } = useStore()
  const backend = getActiveBackend()

  if (!paymentResult) {
    return (
      <div className="page">
        <div className="container" style={{ textAlign: 'center', paddingTop: '4rem' }}>
          <p style={{ color: 'var(--text2)' }}>Нет данных о покупке.</p>
          <button className="btn btn-primary" style={{ marginTop: '1rem' }} onClick={() => navigate('/')}>
            На главную
          </button>
        </div>
      </div>
    )
  }

  const handleDownload = async () => {
    try {
      const { data } = await ticketsAPI.download(currentOrder.order_id)
      const url = URL.createObjectURL(new Blob([data], { type: 'application/pdf' }))
      const a   = document.createElement('a')
      a.href    = url
      a.download = `ticket_${paymentResult.payment_id?.slice(0, 8)}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      alert('Ошибка скачивания: ' + err.message)
    }
  }

  const handleNewBooking = () => {
    resetBooking()
    navigate('/')
  }

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 580 }}>

        {/* Success header */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>✅</div>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--success)', marginBottom: '0.4rem' }}>
            Оплата прошла!
          </h1>
          <p style={{ color: 'var(--text2)', fontFamily: 'var(--mono)', fontSize: '0.85rem' }}>
            Ваш билет готов к скачиванию
          </p>
        </div>

        {/* Ticket card */}
        <div style={{
          background: 'var(--bg2)',
          border: '1px solid var(--success)',
          borderRadius: 4,
          overflow: 'hidden',
          marginBottom: '1.5rem',
          boxShadow: '0 0 30px rgba(74,222,128,0.1)',
        }}>
          {/* Ticket header */}
          <div style={{
            background: 'linear-gradient(90deg, #0a1a0a, #0a2a10)',
            padding: '1.5rem',
            borderBottom: '1px dashed var(--border)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}>
            <div>
              <div style={{ fontFamily: 'var(--mono)', fontSize: '0.7rem', color: 'var(--text2)', letterSpacing: '0.15em', marginBottom: '0.3rem' }}>
                ЭЛЕКТРОННЫЙ БИЛЕТ
              </div>
              <div style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--success)' }}>
                🎟 HFBS TICKET
              </div>
            </div>
            <span className={`tag tag-${backend}`} style={{ fontSize: '0.7rem' }}>
              {backend === 'fastapi' ? '⚡ FastAPI' : '🐍 Django'}
            </span>
          </div>

          {/* Ticket body */}
          <div style={{ padding: '1.5rem' }}>
            {[
              { label: 'Событие',    value: selectedEvent?.title || '—',           mono: false },
              { label: 'Место',      value: selectedSeat ? `Ряд ${selectedSeat.row}, Место ${selectedSeat.number}` : '—', mono: true },
              { label: 'Категория',  value: selectedSeat?.category || '—',          mono: true },
              { label: 'Сумма',      value: `$${currentOrder?.amount || '—'}`,     mono: true, accent: true },
              { label: 'Payment ID', value: paymentResult.payment_id?.slice(0, 16) + '...', mono: true },
              { label: 'Заказ №',    value: `#${paymentResult.order_id}`,           mono: true },
            ].map(({ label, value, mono, accent }) => (
              <div key={label} style={{
                display: 'flex',
                justifyContent: 'space-between',
                padding: '0.5rem 0',
                borderBottom: '1px solid var(--border)',
                fontFamily: mono ? 'var(--mono)' : 'var(--sans)',
                fontSize: '0.88rem',
              }}>
                <span style={{ color: 'var(--text2)' }}>{label}</span>
                <span style={{ color: accent ? 'var(--accent)' : 'var(--text)', fontWeight: accent ? 700 : 400 }}>
                  {value}
                </span>
              </div>
            ))}
          </div>

          {/* QR mock */}
          <div style={{
            padding: '1rem',
            textAlign: 'center',
            background: 'var(--bg3)',
            borderTop: '1px dashed var(--border)',
          }}>
            <div style={{
              display: 'inline-grid',
              gridTemplateColumns: 'repeat(8, 10px)',
              gap: 2,
              marginBottom: '0.5rem',
            }}>
              {Array.from({ length: 64 }, (_, i) => (
                <div key={i} style={{
                  width: 10, height: 10,
                  background: Math.random() > 0.5 ? 'var(--success)' : 'transparent',
                  borderRadius: 1,
                }} />
              ))}
            </div>
            <div style={{ fontFamily: 'var(--mono)', fontSize: '0.7rem', color: 'var(--text2)' }}>
              {paymentResult.payment_id?.slice(0, 8).toUpperCase()}
            </div>
          </div>
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
          <button className="btn btn-primary" style={{ width: '100%', padding: '0.9rem', fontSize: '1rem' }} onClick={handleDownload}>
            ⬇️ Скачать PDF билет
          </button>
          <button className="btn btn-outline" style={{ width: '100%' }} onClick={handleNewBooking}>
            Купить ещё один билет
          </button>
        </div>

        {/* Backend info */}
        <div className="card" style={{ marginTop: '1.5rem', background: 'var(--bg3)', textAlign: 'center' }}>
          <p style={{ fontFamily: 'var(--mono)', fontSize: '0.75rem', color: 'var(--text2)', lineHeight: 1.7 }}>
            Оплата обработана через <strong style={{ color: backend === 'fastapi' ? 'var(--accent)' : '#09bc8a' }}>
              {backend === 'fastapi' ? 'FastAPI (async)' : 'Django (sync)'}
            </strong><br />
            Redis lock → PostgreSQL transaction → PDF generation → Kafka event
          </p>
        </div>
      </div>
    </div>
  )
}
