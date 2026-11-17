import { ChevronLeft, ChevronRight, Download, FileText, Pencil, Plus, Receipt, Trash2, Upload } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

import { CategoryLabel } from '../components/Category'
import ExpenseForm from '../components/ExpenseForm'
import { Button, ConfirmDialog, EmptyState, IconButton, Loader, Notice, SelectField, TextField } from '../components/ui'
import { api } from '../lib/api'
import { currentMonth, formatAmount, formatDate, monthRange } from '../lib/format'
import { useAsync } from '../lib/useAsync'

const PAGE_SIZE = 20

function useDebounced(value, delay) {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])
  return debounced
}

export default function Expenses() {
  const range = monthRange(currentMonth())
  const [filters, setFilters] = useState({ q: '', date_from: range.from, date_to: range.to, category_id: '' })
  const [page, setPage] = useState(0)
  const [form, setForm] = useState(null) // null, 'new' ou la dépense à modifier
  const [toDelete, setToDelete] = useState(null)
  const [deleting, setDeleting] = useState(false)
  const [message, setMessage] = useState(null)
  const [busy, setBusy] = useState(null)
  const fileInput = useRef(null)

  const search = useDebounced(filters.q, 300)
  const query = { ...filters, q: search }
  const list = useAsync(
    () => api.expenses({ ...query, limit: PAGE_SIZE, offset: page * PAGE_SIZE }),
    [search, filters.date_from, filters.date_to, filters.category_id, page],
  )
  const categories = useAsync(() => api.categories(), [])

  function updateFilter(name, value) {
    setFilters((previous) => ({ ...previous, [name]: value }))
    setPage(0)
  }

  async function run(name, action) {
    setBusy(name)
    setMessage(null)
    try {
      await action()
    } catch (failure) {
      setMessage({ tone: 'error', text: failure.message })
    } finally {
      setBusy(null)
    }
  }

  function importFile(event) {
    const file = event.target.files[0]
    event.target.value = ''
    if (!file) return
    run('import', async () => {
      const report = await api.importExpenses(file)
      const rejected = report.rejected
        ? ` ${report.rejected} ligne(s) ignorée(s), la première à la ligne ${report.errors[0].line} : ${report.errors[0].message}.`
        : ''
      setMessage({
        tone: report.rejected ? 'warning' : 'success',
        text: `${report.imported} dépense(s) importée(s).${rejected}`,
      })
      list.reload()
    })
  }

  async function confirmDelete() {
    setDeleting(true)
    try {
      await api.deleteExpense(toDelete.id)
      setToDelete(null)
      // Si la dernière ligne de la page vient d'être supprimée, on recule d'une page.
      if (list.data.items.length === 1 && page > 0) setPage(page - 1)
      else list.reload()
    } catch (failure) {
      setToDelete(null)
      setMessage({ tone: 'error', text: failure.message })
    } finally {
      setDeleting(false)
    }
  }

  const data = list.data
  const exportParams = { date_from: filters.date_from, date_to: filters.date_to, category_id: filters.category_id }
  const filtered = Boolean(search || filters.category_id)
  const lastPage = data ? Math.max(0, Math.ceil(data.total / PAGE_SIZE) - 1) : 0

  return (
    <>
      <header className="page-header">
        <div>
          <h1>Dépenses</h1>
          <p>Consultez, corrigez et exportez vos dépenses.</p>
        </div>
        <div className="actions">
          <input ref={fileInput} type="file" accept=".csv,text/csv" hidden onChange={importFile} />
          <Button variant="secondary" icon={Upload} loading={busy === 'import'} onClick={() => fileInput.current.click()}>
            Importer
          </Button>
          <Button
            variant="secondary"
            icon={Download}
            loading={busy === 'csv'}
            onClick={() => run('csv', () => api.exportExpenses('csv', exportParams))}
          >
            CSV
          </Button>
          <Button
            variant="secondary"
            icon={FileText}
            loading={busy === 'pdf'}
            onClick={() => run('pdf', () => api.exportExpenses('pdf', exportParams))}
          >
            PDF
          </Button>
          <Button icon={Plus} onClick={() => setForm('new')}>
            Nouvelle dépense
          </Button>
        </div>
      </header>

      <div className="stack">
        {message && <Notice tone={message.tone}>{message.text}</Notice>}
        {list.error && <Notice>{list.error}</Notice>}

        <section className="card">
          <div className="filters">
            <TextField
              label="Recherche"
              type="search"
              placeholder="Rechercher dans les notes"
              value={filters.q}
              onChange={(event) => updateFilter('q', event.target.value)}
            />
            <TextField
              label="Du"
              type="date"
              value={filters.date_from}
              onChange={(event) => updateFilter('date_from', event.target.value)}
            />
            <TextField
              label="Au"
              type="date"
              value={filters.date_to}
              onChange={(event) => updateFilter('date_to', event.target.value)}
            />
            <SelectField
              label="Catégorie"
              value={filters.category_id}
              onChange={(event) => updateFilter('category_id', event.target.value)}
            >
              <option value="">Toutes</option>
              {(categories.data || []).map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </SelectField>
          </div>

          {!data && list.loading && <Loader />}

          {data && data.total === 0 && (
            <EmptyState
              icon={Receipt}
              title={filtered ? 'Aucun résultat' : 'Aucune dépense sur cette période'}
              text={
                filtered
                  ? 'Aucune dépense ne correspond à ces critères. Élargissez la période ou modifiez la recherche.'
                  : 'Ajoutez une dépense ou importez un fichier CSV pour commencer.'
              }
              action={
                !filtered && (
                  <Button icon={Plus} onClick={() => setForm('new')}>
                    Nouvelle dépense
                  </Button>
                )
              }
            />
          )}

          {data && data.total > 0 && (
            <>
              <table className="table">
                <thead>
                  <tr>
                    <th className="tight hide-narrow">Date</th>
                    <th>Dépense</th>
                    <th className="hide-narrow">Catégorie</th>
                    <th className="right">Montant</th>
                    <th className="tight">
                      <span className="sr-only">Actions</span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((expense) => (
                    <tr key={expense.id}>
                      <td className="tight muted hide-narrow">{formatDate(expense.date)}</td>
                      <td>
                        {expense.note || <span className="muted">Sans note</span>}
                        <div className="muted show-narrow" style={{ fontSize: 12 }}>
                          {expense.category.name} · {formatDate(expense.date)}
                        </div>
                      </td>
                      <td className="hide-narrow">
                        <CategoryLabel category={expense.category} />
                      </td>
                      <td className="right amount">{formatAmount(expense.amount)}</td>
                      <td className="tight">
                        <div className="row-actions">
                          <IconButton icon={Pencil} label="Modifier" onClick={() => setForm(expense)} />
                          <IconButton icon={Trash2} label="Supprimer" onClick={() => setToDelete(expense)} />
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="pagination">
                <span>
                  {page * PAGE_SIZE + 1} à {page * PAGE_SIZE + data.items.length} sur {data.total}
                </span>
                <div className="actions">
                  <Button variant="secondary" icon={ChevronLeft} disabled={page === 0} onClick={() => setPage(page - 1)}>
                    Précédent
                  </Button>
                  <Button variant="secondary" disabled={page >= lastPage} onClick={() => setPage(page + 1)}>
                    Suivant
                    <ChevronRight size={16} strokeWidth={1.75} />
                  </Button>
                </div>
              </div>
            </>
          )}
        </section>
      </div>

      {form && categories.data && (
        <ExpenseForm
          expense={form === 'new' ? null : form}
          categories={categories.data}
          onClose={() => setForm(null)}
          onSaved={() => {
            setForm(null)
            list.reload()
          }}
        />
      )}

      {toDelete && (
        <ConfirmDialog
          title="Supprimer la dépense"
          text={`La dépense de ${formatAmount(toDelete.amount)} du ${formatDate(toDelete.date)} sera supprimée définitivement.`}
          confirmLabel="Supprimer"
          loading={deleting}
          onConfirm={confirmDelete}
          onClose={() => setToDelete(null)}
        />
      )}
    </>
  )
}
