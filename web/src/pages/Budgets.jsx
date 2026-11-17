import { Pencil, Plus, Target, Trash2 } from 'lucide-react'
import { useState } from 'react'

import { CategoryLabel } from '../components/Category'
import MonthPicker from '../components/MonthPicker'
import {
  Button,
  ConfirmDialog,
  EmptyState,
  IconButton,
  Loader,
  Modal,
  Notice,
  SelectField,
  TextField,
} from '../components/ui'
import { api } from '../lib/api'
import { currentMonth, formatAmount, formatPercent, monthLabel, parseAmount } from '../lib/format'
import { useAsync } from '../lib/useAsync'

const LEVEL_LABELS = { ok: 'Dans le budget', attention: 'Bientôt atteint', depasse: 'Dépassé' }

function BudgetCard({ status, onEdit, onDelete }) {
  const over = status.remaining < 0
  return (
    <article className="card card-body">
      <div className="budget-head">
        <CategoryLabel category={status.category} />
        <div className="row-actions">
          <span className={`badge badge-${status.level}`}>{LEVEL_LABELS[status.level]}</span>
          <IconButton icon={Pencil} label="Modifier le plafond" onClick={onEdit} />
          <IconButton icon={Trash2} label="Supprimer le budget" onClick={onDelete} />
        </div>
      </div>
      <div
        className="progress"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.min(100, Math.round(status.ratio * 100))}
        aria-label={`Budget ${status.category.name}`}
      >
        <div className={`progress-bar ${status.level}`} style={{ width: `${Math.min(100, status.ratio * 100)}%` }} />
      </div>
      <div className="budget-figures">
        <span className="amount">
          {formatAmount(status.spent)} sur {formatAmount(status.ceiling)} ({formatPercent(status.ratio)})
        </span>
        <span className="amount">
          {over ? `Dépassement de ${formatAmount(-status.remaining)}` : `Reste ${formatAmount(status.remaining)}`}
        </span>
      </div>
    </article>
  )
}

function BudgetForm({ month, budget, categories, onSaved, onClose }) {
  const [categoryId, setCategoryId] = useState(budget ? String(budget.category.id) : String(categories[0]?.id || ''))
  const [ceiling, setCeiling] = useState(budget ? String(budget.ceiling) : '')
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)

  async function submit(event) {
    event.preventDefault()
    const value = parseAmount(ceiling)
    if (!value) {
      setError('Indiquez un plafond supérieur à zéro.')
      return
    }
    setSaving(true)
    setError(null)
    try {
      await api.setBudget({ category_id: Number(categoryId), month, ceiling: value })
      onSaved()
    } catch (failure) {
      setError(failure.message)
      setSaving(false)
    }
  }

  return (
    <Modal title={budget ? 'Modifier le plafond' : 'Nouveau budget'} onClose={onClose}>
      <form onSubmit={submit} noValidate>
        <div className="modal-body form">
          {error && <Notice>{error}</Notice>}
          <SelectField
            label="Catégorie"
            value={categoryId}
            disabled={Boolean(budget)}
            onChange={(event) => setCategoryId(event.target.value)}
          >
            {(budget ? [budget.category] : categories).map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </SelectField>
          <TextField
            label={`Plafond pour ${monthLabel(month).toLowerCase()}`}
            suffix="FCFA"
            inputMode="numeric"
            autoComplete="off"
            placeholder="0"
            value={ceiling}
            onChange={(event) => setCeiling(event.target.value.replace(/[^\d\s]/g, ''))}
          />
        </div>
        <div className="modal-footer">
          <Button variant="secondary" onClick={onClose}>
            Annuler
          </Button>
          <Button type="submit" loading={saving}>
            Enregistrer
          </Button>
        </div>
      </form>
    </Modal>
  )
}

export default function Budgets() {
  const [month, setMonth] = useState(currentMonth())
  const [form, setForm] = useState(null) // null, 'new' ou le budget à modifier
  const [toDelete, setToDelete] = useState(null)
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState(null)
  const statuses = useAsync(() => api.budgetStatuses(month), [month])
  const categories = useAsync(() => api.categories(), [])

  const used = new Set((statuses.data || []).map((status) => status.category.id))
  const available = (categories.data || []).filter((category) => !used.has(category.id))
  const totalCeiling = (statuses.data || []).reduce((sum, status) => sum + status.ceiling, 0)
  const totalSpent = (statuses.data || []).reduce((sum, status) => sum + status.spent, 0)

  async function confirmDelete() {
    setDeleting(true)
    try {
      await api.deleteBudget(toDelete.budget_id)
      statuses.reload()
    } catch (failure) {
      setError(failure.message)
    } finally {
      setDeleting(false)
      setToDelete(null)
    }
  }

  const addButton = (
    <Button icon={Plus} disabled={available.length === 0} onClick={() => setForm('new')}>
      Nouveau budget
    </Button>
  )

  return (
    <>
      <header className="page-header">
        <div>
          <h1>Budgets</h1>
          <p>
            {statuses.data?.length
              ? `${formatAmount(totalSpent)} dépensés sur ${formatAmount(totalCeiling)} prévus.`
              : 'Fixez un plafond mensuel par catégorie.'}
          </p>
        </div>
        <div className="actions">
          <MonthPicker month={month} onChange={setMonth} allowFuture />
          {addButton}
        </div>
      </header>

      <div className="stack">
        {(error || statuses.error) && <Notice>{error || statuses.error}</Notice>}
        {!statuses.data && statuses.loading && <Loader />}

        {statuses.data?.length === 0 && (
          <section className="card">
            <EmptyState
              icon={Target}
              title={`Aucun budget pour ${monthLabel(month).toLowerCase()}`}
              text="Un budget fixe un plafond pour une catégorie. Vous êtes prévenu à 80 % du plafond, puis en cas de dépassement."
              action={addButton}
            />
          </section>
        )}

        {statuses.data?.map((status) => (
          <BudgetCard
            key={status.budget_id}
            status={status}
            onEdit={() => setForm(status)}
            onDelete={() => setToDelete(status)}
          />
        ))}
      </div>

      {form && (
        <BudgetForm
          month={month}
          budget={form === 'new' ? null : form}
          categories={available}
          onClose={() => setForm(null)}
          onSaved={() => {
            setForm(null)
            statuses.reload()
          }}
        />
      )}

      {toDelete && (
        <ConfirmDialog
          title="Supprimer le budget"
          text={`Le budget ${toDelete.category.name} de ${monthLabel(month).toLowerCase()} sera supprimé. Vos dépenses ne sont pas modifiées.`}
          confirmLabel="Supprimer"
          loading={deleting}
          onConfirm={confirmDelete}
          onClose={() => setToDelete(null)}
        />
      )}
    </>
  )
}
