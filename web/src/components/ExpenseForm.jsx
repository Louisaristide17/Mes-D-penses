import { Tag } from 'lucide-react'
import { useEffect, useState } from 'react'

import { api } from '../lib/api'
import { formatPercent, parseAmount, today } from '../lib/format'
import { Button, Modal, Notice, SelectField, TextField } from './ui'

const AUTO = ''

export default function ExpenseForm({ expense, categories, onSaved, onClose }) {
  const editing = Boolean(expense)
  const [amount, setAmount] = useState(expense ? String(expense.amount) : '')
  const [date, setDate] = useState(expense?.date || today())
  const [note, setNote] = useState(expense?.note || '')
  const [categoryId, setCategoryId] = useState(expense ? String(expense.category.id) : AUTO)
  const [suggestion, setSuggestion] = useState(null)
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)

  // La suggestion est demandée une fois la frappe interrompue, pour ne pas appeler l'API à chaque lettre.
  useEffect(() => {
    const text = note.trim()
    if (text.length < 3) {
      setSuggestion(null)
      return undefined
    }
    let cancelled = false
    const timer = setTimeout(() => {
      api
        .suggestCategory(text)
        .then((result) => !cancelled && setSuggestion(result.category ? result : null))
        .catch(() => !cancelled && setSuggestion(null))
    }, 350)
    return () => {
      cancelled = true
      clearTimeout(timer)
    }
  }, [note])

  async function submit(event) {
    event.preventDefault()
    const value = parseAmount(amount)
    if (!value) {
      setError('Indiquez un montant supérieur à zéro.')
      return
    }
    const payload = { amount: value, date, note: note.trim() }
    if (categoryId !== AUTO) payload.category_id = Number(categoryId)
    setSaving(true)
    setError(null)
    try {
      onSaved(editing ? await api.updateExpense(expense.id, payload) : await api.createExpense(payload))
    } catch (failure) {
      setError(failure.message)
      setSaving(false)
    }
  }

  const suggested = suggestion?.category
  const showSuggestion = suggested && String(suggested.id) !== categoryId

  return (
    <Modal title={editing ? 'Modifier la dépense' : 'Nouvelle dépense'} onClose={onClose}>
      <form onSubmit={submit} noValidate>
        <div className="modal-body form">
          {error && <Notice>{error}</Notice>}
          <div className="form-row">
            <TextField
              label="Montant"
              suffix="FCFA"
              inputMode="numeric"
              autoComplete="off"
              placeholder="0"
              value={amount}
              onChange={(event) => setAmount(event.target.value.replace(/[^\d\s]/g, ''))}
            />
            <TextField
              label="Date"
              type="date"
              required
              value={date}
              onChange={(event) => setDate(event.target.value)}
            />
          </div>
          <TextField
            label="Note"
            maxLength={255}
            placeholder="Taxi pour Cocody, facture CIE, marché..."
            value={note}
            onChange={(event) => setNote(event.target.value)}
          />
          <SelectField
            label="Catégorie"
            hint={!editing && categoryId === AUTO && !suggested ? 'Choisie pour vous à partir de la note.' : undefined}
            value={categoryId}
            onChange={(event) => setCategoryId(event.target.value)}
          >
            {!editing && <option value={AUTO}>Automatique</option>}
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </SelectField>
          {showSuggestion && (
            <div className="suggestion">
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                <Tag size={14} strokeWidth={1.75} />
                <span>
                  Catégorie suggérée : <strong>{suggested.name}</strong>
                  <span className="muted"> ({formatPercent(suggestion.confidence)} de confiance)</span>
                </span>
              </span>
              <button type="button" className="link-button" onClick={() => setCategoryId(String(suggested.id))}>
                Appliquer
              </button>
            </div>
          )}
        </div>
        <div className="modal-footer">
          <Button variant="secondary" onClick={onClose}>
            Annuler
          </Button>
          <Button type="submit" loading={saving}>
            {editing ? 'Enregistrer' : 'Ajouter la dépense'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}
