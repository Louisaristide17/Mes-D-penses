import { LogOut, Plus, Trash2 } from 'lucide-react'
import { useState } from 'react'

import { useAuth } from '../auth/AuthContext'
import { CATEGORY_ICONS, CategoryLabel, CUSTOM_COLORS, CUSTOM_ICONS } from '../components/Category'
import { Button, IconButton, Loader, Notice, TextField } from '../components/ui'
import { api } from '../lib/api'
import { useAsync } from '../lib/useAsync'

function useSubmit() {
  const [state, setState] = useState({ saving: false, message: null })
  async function submit(action, success) {
    setState({ saving: true, message: null })
    try {
      await action()
      setState({ saving: false, message: { tone: 'success', text: success } })
    } catch (failure) {
      setState({ saving: false, message: { tone: 'error', text: failure.message } })
    }
  }
  return { ...state, submit }
}

function IdentityCard() {
  const { user, setUser } = useAuth()
  const [name, setName] = useState(user.name)
  const [email, setEmail] = useState(user.email)
  const { saving, message, submit } = useSubmit()

  function save(event) {
    event.preventDefault()
    submit(async () => setUser(await api.updateProfile({ name: name.trim(), email: email.trim() })), 'Profil mis à jour.')
  }

  return (
    <section className="card">
      <div className="card-header">
        <h2>Informations personnelles</h2>
      </div>
      <form className="card-body form" onSubmit={save}>
        {message && <Notice tone={message.tone}>{message.text}</Notice>}
        <div className="form-row">
          <TextField label="Nom complet" required minLength={2} value={name} onChange={(e) => setName(e.target.value)} />
          <TextField label="Adresse e-mail" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <div>
          <Button type="submit" loading={saving}>
            Enregistrer
          </Button>
        </div>
      </form>
    </section>
  )
}

function PasswordCard() {
  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const { saving, message, submit } = useSubmit()

  function save(event) {
    event.preventDefault()
    submit(async () => {
      await api.changePassword({ current_password: current, new_password: next })
      setCurrent('')
      setNext('')
    }, 'Mot de passe modifié.')
  }

  return (
    <section className="card">
      <div className="card-header">
        <h2>Mot de passe</h2>
      </div>
      <form className="card-body form" onSubmit={save}>
        {message && <Notice tone={message.tone}>{message.text}</Notice>}
        <div className="form-row">
          <TextField
            label="Mot de passe actuel"
            type="password"
            autoComplete="current-password"
            required
            value={current}
            onChange={(e) => setCurrent(e.target.value)}
          />
          <TextField
            label="Nouveau mot de passe"
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            hint="8 caractères au minimum."
            value={next}
            onChange={(e) => setNext(e.target.value)}
          />
        </div>
        <div>
          <Button type="submit" loading={saving}>
            Modifier le mot de passe
          </Button>
        </div>
      </form>
    </section>
  )
}

function CategoriesCard() {
  const categories = useAsync(() => api.categories(), [])
  const [name, setName] = useState('')
  const [color, setColor] = useState(CUSTOM_COLORS[0])
  const [icon, setIcon] = useState(CUSTOM_ICONS[0])
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)
  const own = (categories.data || []).filter((category) => !category.is_default)

  async function run(action) {
    setSaving(true)
    setError(null)
    try {
      await action()
      await categories.reload()
    } catch (failure) {
      setError(failure.message)
    } finally {
      setSaving(false)
    }
  }

  function add(event) {
    event.preventDefault()
    run(async () => {
      await api.createCategory({ name: name.trim(), color, icon })
      setName('')
    })
  }

  return (
    <section className="card">
      <div className="card-header">
        <h2>Catégories personnelles</h2>
      </div>
      {!categories.data && <Loader />}
      {categories.data && own.length === 0 && (
        <p className="card-body muted" style={{ paddingBottom: 0 }}>
          Dix catégories sont fournies par défaut. Ajoutez les vôtres si l'une de vos dépenses n'y trouve pas sa place.
        </p>
      )}
      {own.map((category) => (
        <div className="list-row" key={category.id}>
          <CategoryLabel category={category} />
          <IconButton
            icon={Trash2}
            label={`Supprimer ${category.name}`}
            onClick={() => run(() => api.deleteCategory(category.id))}
          />
        </div>
      ))}
      <form className="card-body form" onSubmit={add}>
        {error && <Notice>{error}</Notice>}
        <TextField
          label="Nouvelle catégorie"
          placeholder="Tontine, épargne, dons..."
          required
          minLength={2}
          maxLength={60}
          value={name}
          onChange={(event) => setName(event.target.value)}
        />
        <div className="form-row">
          <div className="field">
            <label id="color-label">Couleur</label>
            <div className="swatches" role="group" aria-labelledby="color-label">
              {CUSTOM_COLORS.map((value) => (
                <button
                  key={value}
                  type="button"
                  className="swatch swatch-color"
                  style={{ background: value }}
                  aria-label={`Couleur ${value}`}
                  aria-pressed={color === value}
                  onClick={() => setColor(value)}
                />
              ))}
            </div>
          </div>
          <div className="field">
            <label id="icon-label">Icône</label>
            <div className="swatches" role="group" aria-labelledby="icon-label">
              {CUSTOM_ICONS.map((value) => {
                const Icon = CATEGORY_ICONS[value]
                return (
                  <button
                    key={value}
                    type="button"
                    className="swatch"
                    aria-label={`Icône ${value}`}
                    aria-pressed={icon === value}
                    onClick={() => setIcon(value)}
                  >
                    <Icon size={16} strokeWidth={1.75} />
                  </button>
                )
              })}
            </div>
          </div>
        </div>
        <div>
          <Button type="submit" variant="secondary" icon={Plus} loading={saving}>
            Ajouter la catégorie
          </Button>
        </div>
      </form>
    </section>
  )
}

export default function Profile() {
  const { logout } = useAuth()
  return (
    <div className="narrow">
      <header className="page-header">
        <div>
          <h1>Profil</h1>
          <p>Votre compte et vos réglages.</p>
        </div>
        <Button variant="secondary" icon={LogOut} onClick={logout}>
          Se déconnecter
        </Button>
      </header>
      <div className="stack">
        <IdentityCard />
        <PasswordCard />
        <CategoriesCard />
      </div>
    </div>
  )
}
