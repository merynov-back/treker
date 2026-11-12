import { Field } from '../../components/ui'

const GROUPS = [
  { type: 'expense', label: 'Витрати' },
  { type: 'income', label: 'Доходи' },
]

export default function CategorySelect({ categories = [], placeholder, onlyType, ...props }) {
  const groups = onlyType ? GROUPS.filter((group) => group.type === onlyType) : GROUPS

  return (
    <Field as="select" {...props}>
      {placeholder !== undefined && <option value="">{placeholder}</option>}
      {groups.map((group) => (
        <optgroup key={group.type} label={group.label}>
          {categories
            .filter((category) => category.type === group.type)
            .map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}
        </optgroup>
      ))}
    </Field>
  )
}
