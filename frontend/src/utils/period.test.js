import { describe, expect, it } from 'vitest'
import { formatMonthTitle, monthBounds, parseMonthKey, shiftMonthKey, toIsoDate } from './period'

describe('period utils', () => {
  it('parses valid month keys only', () => {
    expect(parseMonthKey('2026-10')).toEqual({ year: 2026, month: 10 })
    expect(parseMonthKey('2026-13')).toBeNull()
    expect(parseMonthKey('garbage')).toBeNull()
    expect(parseMonthKey(null)).toBeNull()
  })

  it('shifts months across year boundary', () => {
    expect(shiftMonthKey('2026-01', -1)).toBe('2025-12')
    expect(shiftMonthKey('2026-12', 1)).toBe('2027-01')
  })

  it('returns month bounds including leap february', () => {
    expect(monthBounds('2028-02')).toEqual({ from: '2028-02-01', to: '2028-02-29' })
    expect(monthBounds('2026-10')).toEqual({ from: '2026-10-01', to: '2026-10-31' })
  })

  it('formats local date without utc shift', () => {
    expect(toIsoDate(new Date(2026, 0, 1, 0, 30))).toBe('2026-01-01')
  })

  it('formats month title', () => {
    expect(formatMonthTitle('2026-10')).toBe('Жовтень 2026')
  })
})
