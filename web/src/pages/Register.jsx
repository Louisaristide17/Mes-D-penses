import { useState } from 'react'
import { Link } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'
import AuthScreen from '../components/AuthScreen'
import { Button, Notice, TextField } from '../components/ui'

const MIN_PASSWORD = 8

export default function Register() {
  const { register } = useAuth()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  async function submit(event) {
    event.preventDefault()
    if (password.length < MIN_PASSWORD) {
      setError(`Le mot de passe doit contenir au moins ${MIN_PASSWORD} caractères.`)
      return
    }
    setLoading(true)
    setError(null)
    try {
      await register({ name: name.trim(), email: email.trim(), password })
    } catch (failure) {
      setError(failure.message)
      setLoading(false)
    }
  }

  return (
    <AuthScreen
      title="Créer un compte"
      subtitle="Une minute suffit pour commencer à suivre vos dépenses."
      footer={
        <>
          Déjà inscrit ? <Link to="/connexion">Se connecter</Link>
        </>
      }
    >
      <form className="form" onSubmit={submit}>
        {error && <Notice>{error}</Notice>}
        <TextField
          label="Nom complet"
          autoComplete="name"
          required
          minLength={2}
          value={name}
          onChange={(event) => setName(event.target.value)}
        />
        <TextField
          label="Adresse e-mail"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />
        <TextField
          label="Mot de passe"
          type="password"
          autoComplete="new-password"
          required
          hint={`${MIN_PASSWORD} caractères au minimum.`}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
        <Button type="submit" block loading={loading}>
          Créer mon compte
        </Button>
      </form>
    </AuthScreen>
  )
}
