import { useState } from 'react'
import { Link } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'
import AuthScreen from '../components/AuthScreen'
import { Button, Notice, TextField } from '../components/ui'

export default function Login() {
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  async function submit(event) {
    event.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await login({ email: email.trim(), password })
    } catch (failure) {
      setError(failure.message)
      setLoading(false)
    }
  }

  return (
    <AuthScreen
      title="Connexion"
      subtitle="Retrouvez vos dépenses et vos budgets."
      footer={
        <>
          Pas encore de compte ? <Link to="/inscription">Créer un compte</Link>
        </>
      }
    >
      <form className="form" onSubmit={submit}>
        {error && <Notice>{error}</Notice>}
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
          autoComplete="current-password"
          required
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
        <Button type="submit" block loading={loading}>
          Se connecter
        </Button>
      </form>
    </AuthScreen>
  )
}
