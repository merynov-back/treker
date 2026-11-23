import { addDays, createUser, today } from './server'
import { nextId } from './store'

export const DEMO_EMAIL = 'demo@treker.app'
export const DEMO_PASSWORD = 'demo12345'

// Детермінований генератор — щоб у всіх демо виглядало однаково
function random(seed) {
  let state = seed
  return () => {
    state = (state * 1103515245 + 12345) % 2147483648
    return state / 2147483648
  }
}

// [категорія, опис, мін, макс, разів на місяць]
const EXPENSES = [
  ['Продукти', ['Сільпо', 'АТБ', 'Novus', 'Ринок'], 250, 1400, 9],
  ['Транспорт', ['Метро', 'Bolt', 'Uklon', 'АЗС WOG'], 40, 900, 6],
  ['Кафе та ресторани', ['Кава з собою', 'Обід з колегами', 'Піца', 'Вечеря'], 90, 1100, 5],
  ['Комунальні послуги', ['Світло', 'Вода', 'Інтернет'], 250, 1300, 3],
  ["Здоров'я", ['Аптека', 'Стоматолог'], 150, 1800, 1],
  ['Розваги', ['Кіно', 'Підписка Netflix', 'Концерт', 'Книги'], 150, 1500, 3],
]

export async function seedDemoUser(db) {
  if (db.users.some((u) => u.email === DEMO_EMAIL)) return

  const user = await createUser(db, { name: 'Демо Користувач', email: DEMO_EMAIL, password: DEMO_PASSWORD })
  const categoryId = (name, type) => db.categories.find((c) => c.user_id === user.id && c.name === name && c.type === type).id
  const rnd = random(42)
  const end = today()
  const start = `${addDays(`${end.slice(0, 8)}01`, -70).slice(0, 8)}01`

  const add = (date, name, type, amount, description) => {
    db.transactions.push({
      id: nextId(db, 'transactions'),
      user_id: user.id,
      category_id: categoryId(name, type),
      amount: Math.round(amount) * 100,
      date,
      description,
      created_at: `${date}T12:00:00.000Z`,
    })
  }

  for (let month = start; month <= end; month = `${addDays(`${month}`, 32).slice(0, 8)}01`) {
    const dayOf = (day) => `${month.slice(0, 8)}${String(day).padStart(2, '0')}`
    const lastDay = Number(addDays(`${addDays(month, 32).slice(0, 8)}01`, -1).slice(8))
    const until = month.slice(0, 7) === end.slice(0, 7) ? Number(end.slice(8)) : lastDay

    if (until >= 5) add(dayOf(5), 'Зарплата', 'income', 32000, 'Зарплата')
    if (until >= 20) add(dayOf(20), 'Подарунки', 'income', 1500 + rnd() * 2000, 'Фріланс')

    for (const [name, descriptions, min, max, times] of EXPENSES) {
      for (let i = 0; i < times; i++) {
        const day = 1 + Math.floor(rnd() * lastDay)
        if (day > until) continue
        const description = descriptions[Math.floor(rnd() * descriptions.length)]
        add(dayOf(day), name, 'expense', min + rnd() * (max - min), description)
      }
    }

    const [year, monthNumber] = month.split('-').map(Number)
    const budget = (name, amount) => db.budgets.push({
      id: nextId(db, 'budgets'),
      user_id: user.id,
      category_id: name && categoryId(name, 'expense'),
      amount: amount * 100,
      year,
      month: monthNumber,
    })
    budget(null, 25000)
    budget('Продукти', 7000)
    budget('Кафе та ресторани', 2500)
    budget('Розваги', 2000)
  }
}
