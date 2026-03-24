import { useState, useEffect } from 'react'
import Dashboard from './components/Dashboard'
import DebtList from './components/DebtList'
import AddDebtModal from './components/AddDebtModal'
import PaymentModal from './components/PaymentModal'
import './App.css'

const STORAGE_KEY = 'debt_manager_data'

function App() {
  const [debts, setDebts] = useState([])
  const [payments, setPayments] = useState([])
  const [showAddDebt, setShowAddDebt] = useState(false)
  const [showPayment, setShowPayment] = useState(false)
  const [editingDebt, setEditingDebt] = useState(null)
  const [payingDebt, setPayingDebt] = useState(null)
  const [activeTab, setActiveTab] = useState('dashboard')

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      const { debts: d, payments: p } = JSON.parse(saved)
      setDebts(d || [])
      setPayments(p || [])
    }
  }, [])

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ debts, payments }))
  }, [debts, payments])

  const addDebt = (debt) => {
    const newDebt = { ...debt, id: Date.now(), createdAt: new Date().toISOString() }
    setDebts(prev => [...prev, newDebt])
    setShowAddDebt(false)
  }

  const updateDebt = (updated) => {
    setDebts(prev => prev.map(d => d.id === updated.id ? updated : d))
    setEditingDebt(null)
    setShowAddDebt(false)
  }

  const deleteDebt = (id) => {
    if (!confirm('Delete this debt and all its payment history?')) return
    setDebts(prev => prev.filter(d => d.id !== id))
    setPayments(prev => prev.filter(p => p.debtId !== id))
  }

  const addPayment = (payment) => {
    const newPayment = { ...payment, id: Date.now(), date: new Date().toISOString() }
    setPayments(prev => [...prev, newPayment])
    setDebts(prev => prev.map(d => {
      if (d.id === payment.debtId) {
        const newBalance = Math.max(0, d.currentBalance - payment.amount)
        return { ...d, currentBalance: newBalance, paid: newBalance === 0 }
      }
      return d
    }))
    setShowPayment(false)
    setPayingDebt(null)
  }

  const handleEditDebt = (debt) => {
    setEditingDebt(debt)
    setShowAddDebt(true)
  }

  const handlePayDebt = (debt) => {
    setPayingDebt(debt)
    setShowPayment(true)
  }

  const debtPayments = (debtId) => payments.filter(p => p.debtId === debtId)

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <div className="logo">
            <span className="logo-icon">💳</span>
            <h1>DebtFree</h1>
          </div>
          <button className="btn-primary" onClick={() => { setEditingDebt(null); setShowAddDebt(true) }}>
            + Add Debt
          </button>
        </div>
      </header>

      <nav className="tab-nav">
        <button
          className={`tab-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => setActiveTab('dashboard')}
        >
          Dashboard
        </button>
        <button
          className={`tab-btn ${activeTab === 'debts' ? 'active' : ''}`}
          onClick={() => setActiveTab('debts')}
        >
          My Debts ({debts.filter(d => !d.paid).length})
        </button>
      </nav>

      <main className="main">
        {activeTab === 'dashboard' && (
          <Dashboard
            debts={debts}
            payments={payments}
            onAddDebt={() => { setEditingDebt(null); setShowAddDebt(true) }}
            onPayDebt={handlePayDebt}
          />
        )}
        {activeTab === 'debts' && (
          <DebtList
            debts={debts}
            onEdit={handleEditDebt}
            onDelete={deleteDebt}
            onPay={handlePayDebt}
            debtPayments={debtPayments}
          />
        )}
      </main>

      {showAddDebt && (
        <AddDebtModal
          debt={editingDebt}
          onSave={editingDebt ? updateDebt : addDebt}
          onClose={() => { setShowAddDebt(false); setEditingDebt(null) }}
        />
      )}

      {showPayment && payingDebt && (
        <PaymentModal
          debt={payingDebt}
          onSave={addPayment}
          onClose={() => { setShowPayment(false); setPayingDebt(null) }}
        />
      )}
    </div>
  )
}

export default App
