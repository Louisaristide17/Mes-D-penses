const amountFormat = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 0 })
const dateFormat = new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' })
const monthFormat = new Intl.DateTimeFormat('fr-FR', { month: 'long', year: 'numeric' })
const shortMonthFormat = new Intl.DateTimeFormat('fr-FR', { month: 'short' })

const pad = (value) => String(value).padStart(2, '0')

// Les dates de l'API sont des jours civils (AAAA-MM-JJ) : on les lit en heure locale
// pour éviter le décalage d'un jour que produirait new Date('2026-11-01').
function parseDay(isoDay) {
  const [year, month, day] = isoDay.split('-').map(Number)
  return new Date(year, month - 1, day)
}

export function formatAmount(amount) {
  // Intl insère des espaces insécables fines : on les remplace par des insécables simples,
  // mieux rendues par toutes les polices.
  return `${amountFormat.format(amount).replace(/\s/g, ' ')} FCFA`
}

export function formatCompactAmount(amount) {
  if (amount >= 1_000_000) return `${(amount / 1_000_000).toFixed(1).replace('.', ',')} M`
  if (amount >= 1_000) return `${Math.round(amount / 1_000)} k`
  return String(amount)
}

export function formatDate(isoDay) {
  return dateFormat.format(parseDay(isoDay))
}

export function formatPercent(ratio) {
  return `${Math.round(ratio * 100)} %`
}

export function parseAmount(text) {
  const digits = String(text).replace(/[^\d]/g, '')
  return digits ? Number(digits) : null
}

export function toIsoDay(date) {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

export function today() {
  return toIsoDay(new Date())
}

export function currentMonth() {
  return today().slice(0, 7)
}

export function shiftMonth(month, offset) {
  const [year, number] = month.split('-').map(Number)
  const index = year * 12 + (number - 1) + offset
  return `${Math.floor(index / 12)}-${pad((index % 12) + 1)}`
}

export function monthRange(month) {
  const [year, number] = month.split('-').map(Number)
  const lastDay = new Date(year, number, 0).getDate()
  return { from: `${month}-01`, to: `${month}-${pad(lastDay)}` }
}

export function monthLabel(month) {
  const label = monthFormat.format(parseDay(`${month}-01`))
  return label.charAt(0).toUpperCase() + label.slice(1)
}

export function shortMonthLabel(month) {
  return shortMonthFormat.format(parseDay(`${month}-01`)).replace('.', '')
}
