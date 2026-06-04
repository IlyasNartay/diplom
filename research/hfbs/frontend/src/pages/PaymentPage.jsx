/**
 * src/pages/PaymentPage.jsx
 * Форма оплаты — mock payment flow
 */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { paymentsAPI } from '../services/api'
import useStore from '../store/useStore'

function CardInput({ label, value, onChange, placeholder, maxLength }) {
  return (
    <div style={{ marginBottom: '1rem' }}>
      <label style={{ display: 'block', fontFamily: 'var(--mono)', fontSize: '0.75rem', color: 'var(--text2)', marginBottom: '0.4rem', letterSpacing: '0.1em' }}>
        {label}
      </label>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        maxLength={maxLength}
        style={{ letterSpacing: '0.08em' }}
      />
    </div>
  )
}

export default function PaymentPage() {
  const navigate   = useNavigate()
  const { selectedEvent, selectedSeat, currentOrder, setPaymentResult } = useStore()

  const [cardNum,  setCardNum]  = useState('4242 4242 4242 4242')
  const [expiry,   setExpiry]   = useState('12/27')
  const [cvv,      setCvv]      = useState('123')
  const [name,     setName]     = useState('TEST USER')
  const [loading,  setLoading]  = useState(false)
  const [error,    setError]    = useState(null)

  if (!currentOrder) {
    return (
      <div className="page">
        <div className="container" style={{ textAlign: 'center', paddingTop: '4rem' }}>
          <p style={{ color: 'var(--text2)' }}>Нет активного заказа.</p>
          <button className="btn btn-primary" style={{ marginTop: '1rem' }} onClick={() => navigate('/')}>
            На главную
          </button>
        </div>
      </div>
    )
  }

  const handlePay = async () => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await paymentsAPI.process(currentOrder.order_id, 'tok_mock_visa')
      setPaymentResult(data)
      navigate('/ticket')
    } catch (err) {
      setError(err.response?.data?.error || err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 680 }}>
        {/* Header */}
        <button className="btn btn-ghost" style={{ marginBottom: '1.5rem', fontSize: '0.8rem', padding: '0.3rem 0.8rem' }} onClick={() => navigate(-1)}>
          ← Назад
        </button>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 800, marginBottom: '0.4rem' }}>Оплата билета</h1>
        <p style={{ color: 'var(--text2)', fontFamily: 'var(--mono)', fontSize: '0.8rem', marginBottom: '2rem' }}>
          Mock payment — никаких реальных денег не списывается
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', alignItems: 'start' }}>

          {/* Card form */}
          <div className="card">
            <h2 style={{ fontFamily: 'var(--mono)', fontSize: '0.85rem', color: 'var(--text2)', marginBottom: '1.2rem', letterSpacing: '0.1em' }}>
              ДАННЫЕ КАРТЫ
            </h2>

            {/* Card preview */}
            <div style={{
              background: 'linear-gradient(135deg, #1a2a4a, #0a1a3a)',
              border: '1px solid var(--accent)',
              borderRadius: 8,
              padding: '1.2rem',
              marginBottom: '1.5rem',
              fontFamily: 'var(--mono)',
            }}>
              <div style={{ fontSize: '0.65rem', color: 'rgba(255,255,255,0.5)', marginBottom: '1rem', letterSpacing: '0.1em' }}>
                HFBS MOCK CARD
              </div>
              <div style={{ fontSize: '1rem', letterSpacing: '0.15em', marginBottom: '0.8rem', color: '#fff' }}>
                {cardNum || '•••• •••• •••• ••••'}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'rgba(255,255,255,0.7)' }}>
                <span>{name || 'CARD HOLDER'}</span>
                <span>{expiry || 'MM/YY'}</span>
              </div>
            </div>

            <CardInput label="НОМЕР КАРТЫ"     value={cardNum}  onChange={setCardNum}  placeholder="1234 5678 9012 3456" maxLength={19} />
            <CardInput label="ИМОДЕРЖАТЕЛЬ"    value={name}     onChange={setName}     placeholder="IVAN PETROV" />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.8rem' }}>
              <CardInput label="СРОК ДЕЙСТВИЯ" value={expiry}   onChange={setExpiry}   placeholder="MM/YY" maxLength={5} />
              <CardInput label="CVV"            value={cvv}      onChange={setCvv}      placeholder="•••" maxLength={3} />
            </div>

            {error && (
              <div style={{
                background: 'rgba(255,107,107,0.1)',
                border: '1px solid var(--accent2)',
                borderRadius: 'var(--radius)',
                padding: '0.8rem',
                color: 'var(--accent2)',
                fontFamily: 'var(--mono)',
                fontSize: '0.8rem',
                marginBottom: '1rem',
              }}>
                {error}
              </div>
            )}

            <button
              className="btn btn-primary"
              style={{ width: '100%', fontSize: '1rem', padding: '0.8rem' }}
              onClick={handlePay}
              disabled={loading}
            >
              {loading ? '⟳ Обработка платежа...' : `💳 Оплатить $${currentOrder.amount}`}
            </button>

            <p style={{ textAlign: 'center', fontFamily: 'var(--mono)', fontSize: '0.7rem', color: 'var(--text2)', marginTop: '0.8rem' }}>
              🔒 Mock режим — данные не передаются
            </p>
          </div>

          {/* Order summary */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div className="card">
              <h2 style={{ fontFamily: 'var(--mono)', fontSize: '0.85rem', color: 'var(--text2)', marginBottom: '1rem', letterSpacing: '0.1em' }}>
                ДЕТАЛИ ЗАКАЗА
              </h2>
              {[
                { label: 'Событие',    value: selectedEvent?.title || '—' },
                { label: 'Место',      value: selectedSeat ? `Ряд ${selectedSeat.row}, №${selectedSeat.number}` : '—' },
                { label: 'Категория',  value: selectedSeat?.category || '—' },
                { label: 'Заказ №',    value: `#${currentOrder.order_id}` },
                { label: 'Статус',     value: currentOrder.status },
              ].map(({ label, value }) => (
                <div key={label} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontFamily: 'var(--mono)', fontSize: '0.8rem' }}>
                  <span style={{ color: 'var(--text2)' }}>{label}</span>
                  <span style={{ color: 'var(--text)' }}>{value}</span>
                </div>
              ))}
              <div style={{ borderTop: '1px solid var(--border)', paddingTop: '0.8rem', marginTop: '0.5rem', display: 'flex', justifyContent: 'space-between', fontFamily: 'var(--mono)' }}>
                <span style={{ fontWeight: 700 }}>ИТОГО</span>
                <span style={{ color: 'var(--accent)', fontWeight: 700, fontSize: '1.1rem' }}>${currentOrder.amount}</span>
              </div>
            </div>

            <div className="card" style={{ background: 'rgba(91,143,255,0.05)', borderColor: 'rgba(91,143,255,0.3)' }}>
              <p style={{ fontFamily: 'var(--mono)', fontSize: '0.75rem', color: 'var(--text2)', lineHeight: 1.6 }}>
                <strong style={{ color: 'var(--accent)' }}>Место заблокировано</strong> в Redis на 5 минут.
                После оплаты статус изменится на <span style={{ color: 'var(--success)' }}>SOLD</span> в PostgreSQL
                и будет сгенерирован PDF-билет.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
