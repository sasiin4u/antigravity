import { useState } from 'react'

const DEBT_TYPES = ['Credit Card', 'Student Loan', 'Auto Loan', 'Mortgage', 'Personal Loan', 'Medical', 'Other']

export default function AddDebtModal({ debt, onSave, onClose }) {
  const [form, setForm] = useState({
    name: debt?.name || '',
    type: debt?.type || 'Credit Card',
    originalBalance: debt?.originalBalance || '',
    currentBalance: debt?.currentBalance || '',
    apr: debt?.apr || '',
    minimumPayment: debt?.minimumPayment || '',
    dueDate: debt?.dueDate || '',
    lender: debt?.lender || '',
    notes: debt?.notes || '',
  })
  const [errors, setErrors] = useState({})

  const set = (field) => (e) => setForm(f => ({ ...f, [field]: e.target.value }))

  const validate = () => {
    const errs = {}
    if (!form.name.trim()) errs.name = 'Name is required'
    if (!form.originalBalance || isNaN(form.originalBalance) || +form.originalBalance <= 0)
      errs.originalBalance = 'Enter a valid original balance'
    if (form.currentBalance === '' || isNaN(form.currentBalance) || +form.currentBalance < 0)
      errs.currentBalance = 'Enter a valid current balance'
    if (!form.apr || isNaN(form.apr) || +form.apr < 0)
      errs.apr = 'Enter a valid APR (0 or more)'
    if (!form.minimumPayment || isNaN(form.minimumPayment) || +form.minimumPayment < 0)
      errs.minimumPayment = 'Enter a valid minimum payment'
    return errs
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    const errs = validate()
    if (Object.keys(errs).length) { setErrors(errs); return }
    const payload = {
      ...debt,
      name: form.name.trim(),
      type: form.type,
      originalBalance: +form.originalBalance,
      currentBalance: +form.currentBalance,
      apr: +form.apr,
      minimumPayment: +form.minimumPayment,
      dueDate: form.dueDate,
      lender: form.lender.trim(),
      notes: form.notes.trim(),
      paid: +form.currentBalance === 0,
    }
    onSave(payload)
  }

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <h2>{debt ? 'Edit Debt' : 'Add New Debt'}</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-row">
            <div className="form-group">
              <label>Debt Name *</label>
              <input value={form.name} onChange={set('name')} placeholder="e.g. Chase Visa" />
              {errors.name && <span className="error">{errors.name}</span>}
            </div>
            <div className="form-group">
              <label>Type</label>
              <select value={form.type} onChange={set('type')}>
                {DEBT_TYPES.map(t => <option key={t}>{t}</option>)}
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Original Balance ($) *</label>
              <input type="number" min="0" step="0.01" value={form.originalBalance} onChange={set('originalBalance')} placeholder="10000" />
              {errors.originalBalance && <span className="error">{errors.originalBalance}</span>}
            </div>
            <div className="form-group">
              <label>Current Balance ($) *</label>
              <input type="number" min="0" step="0.01" value={form.currentBalance} onChange={set('currentBalance')} placeholder="8500" />
              {errors.currentBalance && <span className="error">{errors.currentBalance}</span>}
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>APR (%) *</label>
              <input type="number" min="0" step="0.01" value={form.apr} onChange={set('apr')} placeholder="19.99" />
              {errors.apr && <span className="error">{errors.apr}</span>}
            </div>
            <div className="form-group">
              <label>Minimum Payment ($/mo) *</label>
              <input type="number" min="0" step="0.01" value={form.minimumPayment} onChange={set('minimumPayment')} placeholder="200" />
              {errors.minimumPayment && <span className="error">{errors.minimumPayment}</span>}
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Payment Due Day</label>
              <input type="number" min="1" max="31" value={form.dueDate} onChange={set('dueDate')} placeholder="15" />
            </div>
            <div className="form-group">
              <label>Lender / Creditor</label>
              <input value={form.lender} onChange={set('lender')} placeholder="Chase Bank" />
            </div>
          </div>

          <div className="form-group">
            <label>Notes</label>
            <textarea value={form.notes} onChange={set('notes')} rows={2} placeholder="Any additional notes..." />
          </div>

          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn-primary">{debt ? 'Save Changes' : 'Add Debt'}</button>
          </div>
        </form>
      </div>
    </div>
  )
}
