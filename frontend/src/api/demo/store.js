// Демо-«база» в localStorage — лише для збірки на GitHub Pages
const STORAGE_KEY = 'treker.demo.db'

function empty() {
  return { seq: {}, users: [], categories: [], transactions: [], budgets: [], sessions: {} }
}

let memory = null

export function load() {
  if (memory) return memory
  try {
    memory = JSON.parse(localStorage.getItem(STORAGE_KEY)) ?? empty()
  } catch {
    memory = empty()
  }
  return memory
}

export function save() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(memory))
  } catch {
    // приватний режим або переповнене сховище — працюємо в пам'яті
  }
}

export function nextId(db, table) {
  db.seq[table] = (db.seq[table] ?? 0) + 1
  return db.seq[table]
}
