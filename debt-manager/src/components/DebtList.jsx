import { useState } from 'react'

function fmt(amount) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount)
}

function fmtDate(iso) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

export default function DebtList({ debts, onEdit, onDelete, onPay, debtPayments }) {
  const [showPaid, setShowPaid] = useState(false)
  const [expandedId, setExpandedId] = useState(null)

  const active = debts.filter(d => !d.paid)
  const paid = debts.filter(d => d.paid)
  const visible = showPaid ? debts : active

  if (debts.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">📋</div>
        <h2>No debts added yet</h2>
        <p>Add your debts to start tracking your payoff journey.</p>
      </div>
    )
  }

  return (
    <div className="debt-list">
      <div className="list-header">
        <h2>{showPaid ? 'All Debts' : 'Active Debts'} ({visible.length})</h2>
        {paid.length > 0 && (
          <button className="btn-ghost" onClick={() => setShowPaid(v => !v)}>
            {showPaid ? 'Hide Paid' : `Show Paid (${paid.length})`}
          </button>
        )}
      </div>

      {visible.map(debt => {
        const pct = debt.originalBalance > 0
          ? ((debt.originalBalance - debt.currentBalance) / debt.originalBalance) * 100
          : 0
        const history = debtPayments(debt.id)
        const isExpanded = expandedId === debt.id

        return (
          <div key={debt.id} className={`debt-card ${debt.paid ? 'paid' : ''}`}>
            <div className="debt-card-header" onClick={() => setExpandedId(isExpanded ? null : debt.id)}>
              <div className="debt-card-left">
                <div className="debt-type-badge">{debt.type}</div>
                <div>
                  <div className="debt-name">
                    {debt.name}
                    {debt.paid && <span className="paid-badge">✓ Paid Off</span>}
                  </div>
                  <div className="debt-meta">{debt.apr}% APR · Min. {fmt(debt.minimumPayment)}/mo</div>
                </div>
              </div>
              <div className="debt-card-right">
                <div className="debt-balance">{fmt(debt.currentBalance)}</div>
                <div className="debt-original">of {fmt(debt.originalBalance)}</div>
                <span className="expand-icon">{isExpanded ? '▲' : '▼'}</span>
              </div>
            </div>

            <div className="debt-progress">
              <div className="debt-progress-fill" style={{ width: `${pct}%` }} />
            </div>
            <div className="debt-progress-label">{pct.toFixed(1)}% paid off</div>

            {isExpanded && (
              <div className="debt-details">
                {debt.dueDate && (
                  <div className="detail-row">
                    <span>Due Date</span>
                    <span>{debt.dueDate} of each month</span>
                  </div>
                )}
                {debt.lender && (
                  <div className="detail-row">
                    <span>Lender</span>
                    <span>{debt.lender}</span>
                  </div>
                )}
                {debt.notes && (
                  <div className="detail-row">
                    <span>Notes</span>
                    <span>{debt.notes}</span>
                  </div>
                )}
                <div className="detail-row">
                  <span>Added</span>
                  <span>{fmtDate(debt.createdAt)}</span>
                </div>

                {history.length > 0 && (
                  <div className="payment-history">
                    <h4>Payment History</h4>
                    {history.slice().reverse().map(p => (
                      <div key={p.id} className="payment-row">
                        <span>{fmtDate(p.date)}</span>
                        <span className="payment-amount">-{fmt(p.amount)}</span>
                        {p.note && <span className="payment-note">{p.note}</span>}
                      </div>
                    ))}
                  </div>
                )}

                <div className="debt-actions">
                  {!debt.paid && (
                    <button className="btn-primary btn-sm" onClick={() => onPay(debt)}>
                      Make Payment
                    </button>
                  )}
                  <button className="btn-secondary btn-sm" onClick={() => onEdit(debt)}>
                    Edit
                  </button>
                  <button className="btn-danger btn-sm" onClick={() => onDelete(debt.id)}>
                    Delete
                  </button>
                </div>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
