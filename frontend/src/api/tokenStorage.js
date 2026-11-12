const ACCESS_KEY = 'treker.access_token'
const REFRESH_KEY = 'treker.refresh_token'

function read(key) {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

export const tokenStorage = {
  get access() {
    return read(ACCESS_KEY)
  },
  get refresh() {
    return read(REFRESH_KEY)
  },
  save({ access_token, refresh_token }) {
    localStorage.setItem(ACCESS_KEY, access_token)
    localStorage.setItem(REFRESH_KEY, refresh_token)
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
  },
}
