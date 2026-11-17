import { describe, expect, it } from 'vitest'

import {
  formatAmount,
  formatCompactAmount,
  formatPercent,
  monthLabel,
  monthRange,
  parseAmount,
  shiftMonth,
} from './format'

describe('formatAmount', () => {
  it('sépare les milliers et ajoute la devise', () => {
    expect(formatAmount(1250000)).toBe('1 250 000 FCFA')
    expect(formatAmount(500)).toBe('500 FCFA')
    expect(formatAmount(0)).toBe('0 FCFA')
  })
})

describe('formatCompactAmount', () => {
  it('abrège les grands montants pour les axes des graphiques', () => {
    expect(formatCompactAmount(950)).toBe('950')
    expect(formatCompactAmount(45000)).toBe('45 k')
    expect(formatCompactAmount(1250000)).toBe('1,3 M')
  })
})

describe('parseAmount', () => {
  it('ne garde que les chiffres', () => {
    expect(parseAmount('12 500 FCFA')).toBe(12500)
    expect(parseAmount('1.500')).toBe(1500)
    expect(parseAmount('')).toBeNull()
    expect(parseAmount('abc')).toBeNull()
  })
})

describe('mois', () => {
  it('décale un mois en passant les années', () => {
    expect(shiftMonth('2026-01', -1)).toBe('2025-12')
    expect(shiftMonth('2026-12', 1)).toBe('2027-01')
    expect(shiftMonth('2026-11', -6)).toBe('2026-05')
  })

  it('donne le premier et le dernier jour', () => {
    expect(monthRange('2026-11')).toEqual({ from: '2026-11-01', to: '2026-11-30' })
    expect(monthRange('2028-02')).toEqual({ from: '2028-02-01', to: '2028-02-29' })
  })

  it('écrit le mois en toutes lettres', () => {
    expect(monthLabel('2026-11')).toBe('Novembre 2026')
  })
})

describe('formatPercent', () => {
  it('arrondit à l’entier', () => {
    expect(formatPercent(0.826)).toBe('83 %')
  })
})
