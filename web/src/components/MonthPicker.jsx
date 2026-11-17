import { ChevronLeft, ChevronRight } from 'lucide-react'

import { currentMonth, monthLabel, shiftMonth } from '../lib/format'

export default function MonthPicker({ month, onChange, allowFuture = false }) {
  const atLimit = !allowFuture && month >= currentMonth()
  return (
    <div className="month-picker">
      <button
        type="button"
        className="button button-ghost button-icon"
        aria-label="Mois précédent"
        onClick={() => onChange(shiftMonth(month, -1))}
      >
        <ChevronLeft size={16} />
      </button>
      <span aria-live="polite">{monthLabel(month)}</span>
      <button
        type="button"
        className="button button-ghost button-icon"
        aria-label="Mois suivant"
        disabled={atLimit}
        onClick={() => onChange(shiftMonth(month, 1))}
      >
        <ChevronRight size={16} />
      </button>
    </div>
  )
}
