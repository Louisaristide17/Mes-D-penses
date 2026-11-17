import { Minus, Plus, Receipt, TrendingDown, TrendingUp, TriangleAlert } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { CategoryIcon } from '../components/Category'
import ExpenseForm from '../components/ExpenseForm'
import MonthPicker from '../components/MonthPicker'
import { Button, EmptyState, Loader, Notice } from '../components/ui'
import { api } from '../lib/api'
import {
  currentMonth,
  formatAmount,
  formatCompactAmount,
  formatDate,
  formatPercent,
  monthLabel,
  shortMonthLabel,
} from '../lib/format'
import { useAsync } from '../lib/useAsync'

const MAX_LEGEND_ROWS = 6

function Variation({ variation }) {
  if (variation === null) {
    return (
      <p className="stat-note">
        <Minus size={14} /> Pas de dépense le mois précédent
      </p>
    )
  }
  const rising = variation > 0
  const Icon = rising ? TrendingUp : TrendingDown
  return (
    <p className="stat-note">
      <span className={rising ? 'trend-up' : 'trend-down'} style={{ display: 'inline-flex', gap: 4, alignItems: 'center' }}>
        <Icon size={14} />
        {rising ? '+' : '-'}
        {formatPercent(Math.abs(variation))}
      </span>
      par rapport au mois précédent
    </p>
  )
}

function AmountTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  return (
    <div className="chart-tooltip">
      <span className="muted">{payload[0].payload.full || payload[0].name}</span>
      <strong>{formatAmount(payload[0].value)}</strong>
    </div>
  )
}

function MonthlyChart({ monthly, selected }) {
  const data = monthly.map((row) => ({ ...row, label: shortMonthLabel(row.month), full: monthLabel(row.month) }))
  return (
    <div className="chart">
      <ResponsiveContainer>
        <BarChart data={data} margin={{ top: 8, right: 0, bottom: 0, left: 0 }}>
          <CartesianGrid vertical={false} stroke="#E4E7E5" />
          <XAxis dataKey="label" tickLine={false} axisLine={false} tick={{ fill: '#5B6661', fontSize: 12 }} />
          <YAxis
            width={44}
            tickLine={false}
            axisLine={false}
            tick={{ fill: '#5B6661', fontSize: 12 }}
            tickFormatter={formatCompactAmount}
          />
          <Tooltip cursor={{ fill: '#F7F8F7' }} content={<AmountTooltip />} />
          <Bar dataKey="total" radius={[4, 4, 0, 0]} maxBarSize={48} isAnimationActive={false}>
            {data.map((row) => (
              <Cell key={row.month} fill={row.month === selected ? '#0F5D4A' : '#B9D3CB'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

function CategoryBreakdown({ rows }) {
  // Au-delà de six catégories, les plus petites sont regroupées pour garder la légende lisible.
  const visible = rows.slice(0, MAX_LEGEND_ROWS)
  const rest = rows.slice(MAX_LEGEND_ROWS)
  const slices = visible.map((row) => ({
    name: row.category.name,
    color: row.category.color,
    total: row.total,
    share: row.share,
  }))
  if (rest.length) {
    slices.push({
      name: `${rest.length} autres`,
      color: '#C5CBC8',
      total: rest.reduce((sum, row) => sum + row.total, 0),
      share: rest.reduce((sum, row) => sum + row.share, 0),
    })
  }
  return (
    <div className="donut">
      <div className="donut-chart">
        <ResponsiveContainer>
          <PieChart>
            <Pie
              data={slices}
              dataKey="total"
              nameKey="name"
              innerRadius={50}
              outerRadius={78}
              paddingAngle={1.5}
              stroke="none"
              isAnimationActive={false}
            >
              {slices.map((slice) => (
                <Cell key={slice.name} fill={slice.color} />
              ))}
            </Pie>
            <Tooltip content={<AmountTooltip />} />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <ul className="legend">
        {slices.map((slice) => (
          <li key={slice.name}>
            <span className="legend-swatch" style={{ background: slice.color }} />
            <span className="legend-name">{slice.name}</span>
            <span className="amount muted">{formatPercent(slice.share)}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default function Dashboard() {
  const [month, setMonth] = useState(currentMonth())
  const [adding, setAdding] = useState(false)
  const summary = useAsync(() => api.dashboard(month), [month])
  const categories = useAsync(() => api.categories(), [])
  const data = summary.data

  return (
    <>
      <header className="page-header">
        <div>
          <h1>Tableau de bord</h1>
          <p>Vos dépenses de {monthLabel(month).toLowerCase()}.</p>
        </div>
        <div className="actions">
          <MonthPicker month={month} onChange={setMonth} />
          <Button icon={Plus} onClick={() => setAdding(true)}>
            Nouvelle dépense
          </Button>
        </div>
      </header>

      {summary.error && <Notice>{summary.error}</Notice>}
      {!data && summary.loading && <Loader />}

      {data && (
        <div className="stack">
          <div className="grid grid-3">
            <div className="card card-body">
              <p className="stat-label">Total du mois</p>
              <p className="stat-value">{formatAmount(data.total)}</p>
              <Variation variation={data.variation} />
            </div>
            <div className="card card-body">
              <p className="stat-label">Nombre de dépenses</p>
              <p className="stat-value">{data.count}</p>
              <p className="stat-note">
                {data.count > 0 ? `${formatAmount(Math.round(data.total / data.count))} en moyenne` : 'Aucune saisie ce mois-ci'}
              </p>
            </div>
            <div className="card card-body">
              <p className="stat-label">Premier poste de dépense</p>
              <p className="stat-value" style={{ fontSize: 20, lineHeight: '34px' }}>
                {data.by_category[0]?.category.name || 'Aucun'}
              </p>
              <p className="stat-note">
                {data.by_category[0]
                  ? `${formatAmount(data.by_category[0].total)}, soit ${formatPercent(data.by_category[0].share)} du total`
                  : 'Ajoutez une dépense pour le voir apparaître'}
              </p>
            </div>
          </div>

          {data.alerts.map((alert) => (
            <Notice key={alert.budget_id} tone={alert.level === 'depasse' ? 'error' : 'warning'}>
              {alert.level === 'depasse' ? (
                <>
                  Budget <strong>{alert.category.name}</strong> dépassé de {formatAmount(-alert.remaining)}.
                </>
              ) : (
                <>
                  Budget <strong>{alert.category.name}</strong> consommé à {formatPercent(alert.ratio)} : il reste{' '}
                  {formatAmount(alert.remaining)}.
                </>
              )}{' '}
              <Link to="/budgets">Voir les budgets</Link>
            </Notice>
          ))}

          <div className="grid grid-2">
            <section className="card">
              <div className="card-header">
                <h2>Évolution sur six mois</h2>
              </div>
              <div className="card-body">
                <MonthlyChart monthly={data.monthly} selected={data.month} />
              </div>
            </section>
            <section className="card">
              <div className="card-header">
                <h2>Répartition par catégorie</h2>
              </div>
              <div className="card-body">
                {data.by_category.length ? (
                  <CategoryBreakdown rows={data.by_category} />
                ) : (
                  <p className="muted">Aucune dépense à répartir pour ce mois.</p>
                )}
              </div>
            </section>
          </div>

          <section className="card">
            <div className="card-header">
              <h2>Dernières dépenses</h2>
              {data.recent.length > 0 && <Link to="/depenses">Tout voir</Link>}
            </div>
            {data.recent.length === 0 ? (
              <EmptyState
                icon={Receipt}
                title="Aucune dépense ce mois-ci"
                text="Ajoutez votre première dépense : le tableau de bord se remplira au fur et à mesure."
                action={
                  <Button icon={Plus} onClick={() => setAdding(true)}>
                    Nouvelle dépense
                  </Button>
                }
              />
            ) : (
              data.recent.map((expense) => (
                <div className="list-row" key={expense.id}>
                  <div className="list-row-main">
                    <CategoryIcon category={expense.category} size={32} />
                    <div className="list-row-text">
                      <strong>{expense.note || expense.category.name}</strong>
                      <span>
                        {expense.category.name} · {formatDate(expense.date)}
                      </span>
                    </div>
                  </div>
                  <span className="amount">{formatAmount(expense.amount)}</span>
                </div>
              ))
            )}
          </section>
        </div>
      )}

      {adding && categories.data && (
        <ExpenseForm
          categories={categories.data}
          onClose={() => setAdding(false)}
          onSaved={() => {
            setAdding(false)
            summary.reload()
          }}
        />
      )}
    </>
  )
}
