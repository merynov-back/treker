import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { analyticsApi, budgetsApi, categoriesApi, transactionsApi } from './endpoints'

export const queryKeys = {
  categories: ['categories'],
  transactions: (params) => ['transactions', params],
  budgets: (year, month) => ['budgets', year, month],
  budgetStatus: (year, month) => ['budgets', 'status', year, month],
  summary: (params) => ['analytics', 'summary', params],
  byCategory: (params) => ['analytics', 'by-category', params],
  byPeriod: (params) => ['analytics', 'by-period', params],
}

// Будь-яка зміна грошей зачіпає списки, звіти й бюджети — оновлюємо все разом
function useInvalidateFinance() {
  const queryClient = useQueryClient()
  return () => Promise.all(
    ['transactions', 'analytics', 'budgets', 'categories'].map((key) =>
      queryClient.invalidateQueries({ queryKey: [key] }),
    ),
  )
}

function useFinanceMutation(mutationFn) {
  const invalidate = useInvalidateFinance()
  return useMutation({ mutationFn, onSuccess: invalidate })
}

// За українським алфавітом, «Інше» — в кінці
const sortCategories = (categories) =>
  [...categories].sort((a, b) => {
    const aOther = a.name === 'Інше'
    const bOther = b.name === 'Інше'
    if (aOther !== bOther) return aOther ? 1 : -1
    return a.name.localeCompare(b.name, 'uk')
  })

export const useCategories = () =>
  useQuery({
    queryKey: queryKeys.categories,
    queryFn: () => categoriesApi.list(),
    select: sortCategories,
    staleTime: 60_000,
  })

export const useCreateCategory = () => useFinanceMutation(categoriesApi.create)
export const useRenameCategory = () => useFinanceMutation(({ id, name }) => categoriesApi.rename(id, name))
export const useDeleteCategory = () => useFinanceMutation(categoriesApi.remove)

export const useTransactions = (params) =>
  useQuery({
    queryKey: queryKeys.transactions(params),
    queryFn: () => transactionsApi.list(params),
    placeholderData: keepPreviousData,
  })

export const useCreateTransaction = () => useFinanceMutation(transactionsApi.create)
export const useUpdateTransaction = () => useFinanceMutation(({ id, data }) => transactionsApi.update(id, data))
export const useDeleteTransaction = () => useFinanceMutation(transactionsApi.remove)

export const useBudgetStatus = (year, month) =>
  useQuery({ queryKey: queryKeys.budgetStatus(year, month), queryFn: () => budgetsApi.status(year, month) })

export const useCreateBudget = () => useFinanceMutation(budgetsApi.create)
export const useUpdateBudget = () => useFinanceMutation(({ id, amount }) => budgetsApi.update(id, amount))
export const useDeleteBudget = () => useFinanceMutation(budgetsApi.remove)
export const useCopyBudgets = () => useFinanceMutation(({ year, month }) => budgetsApi.copyPrevious(year, month))

export const useSummary = (params) =>
  useQuery({ queryKey: queryKeys.summary(params), queryFn: () => analyticsApi.summary(params) })

export const useByCategory = (params) =>
  useQuery({ queryKey: queryKeys.byCategory(params), queryFn: () => analyticsApi.byCategory(params) })

export const useByPeriod = (params) =>
  useQuery({
    queryKey: queryKeys.byPeriod(params),
    queryFn: () => analyticsApi.byPeriod(params),
    placeholderData: keepPreviousData,
  })
