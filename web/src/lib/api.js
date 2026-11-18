// Adresse de l'API, tolérante aux erreurs de saisie courantes : espaces, barre finale, schéma oublié.
export function apiRoot(value) {
  const root = (value || 'http://localhost:8000').trim().replace(/\/+$/, '').replace(/\/api\/v1$/, '')
  return /^https?:\/\//.test(root) ? root : `https://${root}`
}

const BASE_URL = `${apiRoot(import.meta.env.VITE_API_URL)}/api/v1`
const STORAGE_KEY = 'mes-depenses.session'

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

let session = readSession()
let refreshing = null
let onSessionExpired = () => {}

function readSession() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || null
  } catch {
    return null
  }
}

export function setSession(tokens) {
  session = tokens ? { access_token: tokens.access_token, refresh_token: tokens.refresh_token } : null
  try {
    if (session) localStorage.setItem(STORAGE_KEY, JSON.stringify(session))
    else localStorage.removeItem(STORAGE_KEY)
  } catch {
    // Stockage indisponible (navigation privée stricte) : la session reste en mémoire.
  }
}

export function hasSession() {
  return session !== null
}

export function setSessionExpiredHandler(handler) {
  onSessionExpired = handler
}

async function send(path, { method = 'GET', body, params, formData } = {}) {
  const url = new URL(BASE_URL + path)
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') url.searchParams.set(key, value)
  })
  const headers = {}
  if (session) headers.Authorization = `Bearer ${session.access_token}`
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  try {
    return await fetch(url, {
      method,
      headers,
      body: formData || (body !== undefined ? JSON.stringify(body) : undefined),
    })
  } catch {
    throw new ApiError('Connexion au serveur impossible. Vérifiez votre connexion internet.', 0)
  }
}

// Plusieurs requêtes peuvent expirer en même temps : un seul renouvellement est lancé.
function refreshSession() {
  if (!refreshing) {
    refreshing = fetch(`${BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: session.refresh_token }),
    })
      .then(async (response) => {
        if (!response.ok) throw new Error('refresh')
        setSession(await response.json())
      })
      .finally(() => {
        refreshing = null
      })
  }
  return refreshing
}

async function toError(response) {
  let message = 'Une erreur est survenue. Réessayez dans un instant.'
  if (response.status === 422) {
    message = 'Certaines informations sont invalides. Vérifiez le formulaire.'
  } else {
    try {
      const data = await response.json()
      if (typeof data.detail === 'string') message = data.detail
    } catch {
      // Réponse sans corps JSON : on garde le message générique.
    }
  }
  return new ApiError(message, response.status)
}

async function request(path, options = {}) {
  let response = await send(path, options)
  const isAuthRoute = path.startsWith('/auth/')
  if (response.status === 401 && session && !isAuthRoute) {
    try {
      await refreshSession()
    } catch {
      setSession(null)
      onSessionExpired()
      throw new ApiError('Votre session a expiré. Veuillez vous reconnecter.', 401)
    }
    response = await send(path, options)
  }
  if (!response.ok) throw await toError(response)
  return response
}

async function json(path, options) {
  const response = await request(path, options)
  return response.status === 204 ? null : response.json()
}

async function download(path, params) {
  const response = await request(path, { params })
  const disposition = response.headers.get('Content-Disposition') || ''
  const filename = /filename="([^"]+)"/.exec(disposition)?.[1] || path.split('/').pop()
  const link = document.createElement('a')
  link.href = URL.createObjectURL(await response.blob())
  link.download = filename
  link.click()
  URL.revokeObjectURL(link.href)
}

export const api = {
  register: (payload) => json('/auth/register', { method: 'POST', body: payload }),
  login: (payload) => json('/auth/login', { method: 'POST', body: payload }),

  profile: () => json('/users/me'),
  updateProfile: (payload) => json('/users/me', { method: 'PATCH', body: payload }),
  changePassword: (payload) => json('/users/me/password', { method: 'POST', body: payload }),

  categories: () => json('/categories'),
  createCategory: (payload) => json('/categories', { method: 'POST', body: payload }),
  deleteCategory: (id) => json(`/categories/${id}`, { method: 'DELETE' }),

  expenses: (params) => json('/expenses', { params }),
  createExpense: (payload) => json('/expenses', { method: 'POST', body: payload }),
  updateExpense: (id, payload) => json(`/expenses/${id}`, { method: 'PATCH', body: payload }),
  deleteExpense: (id) => json(`/expenses/${id}`, { method: 'DELETE' }),
  suggestCategory: (note) => json('/expenses/suggest-category', { method: 'POST', body: { note } }),
  importExpenses: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return json('/expenses/import', { method: 'POST', formData })
  },
  exportExpenses: (format, params) => download(`/exports/expenses.${format}`, params),

  budgetStatuses: (month) => json('/budgets/status', { params: { month } }),
  setBudget: (payload) => json('/budgets', { method: 'PUT', body: payload }),
  deleteBudget: (id) => json(`/budgets/${id}`, { method: 'DELETE' }),

  dashboard: (month) => json('/dashboard/summary', { params: { month } }),

  askAssistant: (payload) => json('/assistant/messages', { method: 'POST', body: payload }),
}
