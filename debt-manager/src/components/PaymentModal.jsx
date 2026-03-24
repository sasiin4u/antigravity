import { useState } from 'react'

function fmt(amount) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount)
}

export default function PaymentModal({ debt, onSave, onClose }) {
  const [amount, setAmount] = useState(debt.minimumPayment || '')
  const [note, setNote] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!amount || isNaN(amount) || +amount <= 0) {
      setError('Enter a valid payment amount')
      return
    }
    if (+amount > debt.currentBalance) {
      setError(`Amount exceeds current balance of ${fmt(debt.currentBalance)}`)
      return
    }
    onSave({ debtId: debt.id, amount: +amount, note: note.trim() })
  }

  const presets = [
    { label: 'Min', value: debt.minimumPayment },
    { label: '2x Min', value: debt.minimumPayment * 2 },
    { label: 'Full', value: debt.currentBalance },
  ]

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal modal-sm">
        <div className="modal-header">
          <h2>Make Payment</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <div className="payment-debt-info">
          <div className="payment-debt-name">{debt.name}</div>
          <div className="payment-debt-balance">Balance: {fmt(debt.currentBalance)}</div>
        </div>
        <form onSubmit={handleSubmit} className="modal-form">
          <div className="preset-buttons">
            {presets.map(p => p.value > 0 && (
              <button
                key={p.label}
                type="button"
                className={`preset-btn ${+amount === p.value ? 'active' : ''}`}
                onClick={() => setAmount(p.value)}
              >
                {p.label} ({fmt(p.value)})
              </button>
            ))}
          </div>

          <div className="form-group">
            <label>Payment Amount ($) *</label>
            <input
              type="number"
              min="0.01"
              step="0.01"
              value={amount}
              onChange={e => { setAmount(e.target.value); setError('') }}
              placeholder="0.00"
              autoFocus
            />
            {error && <span className="error">{error}</span>}
          </div>

          <div className="form-group">
            <label>Note (optional)</label>
            <input value={note} onChange={e => setNote(e.target.value)} placeholder="e.g. January payment" />
          </div>

          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn-primary">Record Payment</button>
          </div>
        </form>
      </div>
    </div>
  )
}
