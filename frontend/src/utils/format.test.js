import { describe, expect, it } from 'vitest'
import { formatDate, formatMoney, formatPercentChange } from './format'

describe('format utils', () => {
  it('formats money in hryvnias', () => {
    // Символ валюти залежить від версії ICU (₴ або грн), тому перевіряємо лише число
    const digits = formatMoney('1250.5').replace(/[\s\u00a0\u202f]/g, '')
    expect(digits.startsWith('1250,50')).toBe(true)
  })

  it('formats iso date', () => {
    expect(formatDate('2026-10-05')).toBe('05.10.2026')
  })

  it('calculates percent change', () => {
    expect(formatPercentChange('150', '100')).toBe(50)
    expect(formatPercentChange('50', '100')).toBe(-50)
    expect(formatPercentChange('10', '0')).toBeNull()
  })
})
