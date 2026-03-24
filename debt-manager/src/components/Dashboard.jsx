import { useMemo } from 'react'

function fmt(amount) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount)
}

function monthsToPayoff(balance, apr, monthlyPayment) {
  if (monthlyPayment <= 0 || balance <= 0) return null
  const r = apr / 100 / 12
  if (r === 0) return Math.ceil(balance / monthlyPayment)
  const n = -Math.log(1 - (r * balance) / monthlyPayment) / Math.log(1 + r)
  return isFinite(n) && n > 0 ? Math.ceil(n) : null
}

export default function Dashboard({ debts, payments, onAddDebt, onPayDebt }) {
  const stats = useMemo(() => {
    const active = debts.filter(d => !d.paid)
    const totalBalance = active.reduce((s, d) => s + d.currentBalance, 0)
    const totalOriginal = active.reduce((s, d) => s + d.originalBalance, 0)
    const totalPaid = debts.reduce((s, d) => s + (d.originalBalance - d.currentBalance), 0)
    const avgApr = active.length
      ? active.reduce((s, d) => s + d.apr, 0) / active.length
      : 0

    const last30 = new Date()
    last30.setDate(last30.getDate() - 30)
    const recentPayments = payments
      .filter(p => new Date(p.date) >= last30)
      .reduce((s, p) => s + p.amount, 0)

    return { active, totalBalance, totalOriginal, totalPaid, avgApr, recentPayments }
  }, [debts, payments])

  const highestInterestDebt = useMemo(() => {
    const active = debts.filter(d => !d.paid)
    return active.reduce((max, d) => (!max || d.apr > max.apr ? d : max), null)
  }, [debts])

  const smallestDebt = useMemo(() => {
    const active = debts.filter(d => !d.paid)
    return active.reduce((min, d) => (!min || d.currentBalance < min.currentBalance ? d : min), null)
  }, [debts])

  if (debts.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">🎯</div>
        <h2>Start tracking your debts</h2>
        <p>Add your first debt to see your payoff dashboard and progress.</p>
        <button className="btn-primary" onClick={onAddDebt}>+ Add Your First Debt</button>
      </div>
    )
  }

  const progress = stats.totalOriginal > 0
    ? ((stats.totalOriginal - stats.totalBalance) / stats.totalOriginal) * 100
    : 0

  return (
    <div className="dashboard">
      <div className="stats-grid">
        <div className="stat-card accent">
          <div className="stat-label">Total Remaining</div>
          <div className="stat-value">{fmt(stats.totalBalance)}</div>
          <div className="stat-sub">{stats.active.length} active debt{stats.active.length !== 1 ? 's' : ''}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Total Paid Off</div>
          <div className="stat-value green">{fmt(stats.totalPaid)}</div>
          <div className="stat-sub">lifetime payments</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Paid Last 30 Days</div>
          <div className="stat-value">{fmt(stats.recentPayments)}</div>
          <div className="stat-sub">recent activity</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Avg Interest Rate</div>
          <div className="stat-value">{stats.avgApr.toFixed(1)}%</div>
          <div className="stat-sub">APR across active debts</div>
        </div>
      </div>

      <div className="progress-section">
        <div className="progress-header">
          <h2>Overall Progress</h2>
          <span className="progress-pct">{progress.toFixed(1)}% paid off</span>
        </div>
        <div className="progress-bar-bg">
          <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
        </div>
        <div className="progress-labels">
          <span>{fmt(stats.totalOriginal - stats.totalBalance)} paid</span>
          <span>{fmt(stats.totalBalance)} remaining</span>
        </div>
      </div>

      <div className="strategy-section">
        <h2>Payoff Strategies</h2>
        <div className="strategy-grid">
          {highestInterestDebt && (
            <div className="strategy-card">
              <div className="strategy-badge avalanche">Avalanche Method</div>
              <p>Pay highest interest first to minimize total interest paid.</p>
              <div className="strategy-debt">
                <strong>{highestInterestDebt.name}</strong>
                <span>{highestInterestDebt.apr}% APR</span>
              </div>
              <div className="strategy-details">
                <span>{fmt(highestInterestDebt.currentBalance)} remaining</span>
              </div>
              <button className="btn-secondary" onClick={() => onPayDebt(highestInterestDebt)}>
                Make Payment
              </button>
            </div>
          )}
          {smallestDebt && smallestDebt.id !== highestInterestDebt?.id && (
            <div className="strategy-card">
              <div className="strategy-badge snowball">Snowball Method</div>
              <p>Pay smallest balance first for quick wins and motivation.</p>
              <div className="strategy-debt">
                <strong>{smallestDebt.name}</strong>
                <span>{fmt(smallestDebt.currentBalance)} balance</span>
              </div>
              <button className="btn-secondary" onClick={() => onPayDebt(smallestDebt)}>
                Make Payment
              </button>
            </div>
          )}
        </div>
      </div>

      {stats.active.length > 0 && (
        <div className="debt-snapshot">
          <h2>Active Debts</h2>
          <div className="snapshot-list">
            {stats.active.map(debt => {
              const pct = debt.originalBalance > 0
                ? ((debt.originalBalance - debt.currentBalance) / debt.originalBalance) * 100
                : 0
              const months = monthsToPayoff(debt.currentBalance, debt.apr, debt.minimumPayment)
              return (
                <div key={debt.id} className="snapshot-item">
                  <div className="snapshot-info">
                    <div className="snapshot-name">{debt.name}</div>
                    <div className="snapshot-meta">
                      {debt.type} · {debt.apr}% APR
                      {months ? ` · ~${months} mo to payoff` : ''}
                    </div>
                  </div>
                  <div className="snapshot-right">
                    <div className="snapshot-balance">{fmt(debt.currentBalance)}</div>
                    <div className="mini-progress">
                      <div className="mini-progress-fill" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
