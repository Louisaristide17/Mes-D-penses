import { Navigate, Route, Routes } from 'react-router-dom'

import { useAuth } from './auth/AuthContext'
import Layout from './components/Layout'
import { Loader } from './components/ui'
import Assistant from './pages/Assistant'
import Budgets from './pages/Budgets'
import Dashboard from './pages/Dashboard'
import Expenses from './pages/Expenses'
import Login from './pages/Login'
import Profile from './pages/Profile'
import Register from './pages/Register'

export default function App() {
  const { user, loading } = useAuth()

  if (loading) return <Loader />

  if (!user) {
    return (
      <Routes>
        <Route path="/connexion" element={<Login />} />
        <Route path="/inscription" element={<Register />} />
        <Route path="*" element={<Navigate to="/connexion" replace />} />
      </Routes>
    )
  }

  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="depenses" element={<Expenses />} />
        <Route path="budgets" element={<Budgets />} />
        <Route path="assistant" element={<Assistant />} />
        <Route path="profil" element={<Profile />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
