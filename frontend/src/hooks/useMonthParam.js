import { useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import { currentMonthKey, parseMonthKey } from '../utils/period'

// Обраний місяць живе в URL (?month=2026-10): переживає перезавантаження і спільний між сторінками
export function useMonthParam() {
  const [searchParams, setSearchParams] = useSearchParams()
  const raw = searchParams.get('month')
  const month = parseMonthKey(raw) ? raw : currentMonthKey()

  const setMonth = useCallback((value) => {
    setSearchParams((params) => {
      params.set('month', value)
      return params
    }, { replace: true })
  }, [setSearchParams])

  return [month, setMonth]
}
