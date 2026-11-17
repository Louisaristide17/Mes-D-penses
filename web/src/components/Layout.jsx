import { LayoutDashboard, LogOut, MessagesSquare, Receipt, Target, User } from 'lucide-react'
import { NavLink, Outlet } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'
import Brand from './Brand'
import { IconButton } from './ui'

const LINKS = [
  { to: '/', label: 'Tableau de bord', short: 'Accueil', icon: LayoutDashboard, end: true },
  { to: '/depenses', label: 'Dépenses', short: 'Dépenses', icon: Receipt },
  { to: '/budgets', label: 'Budgets', short: 'Budgets', icon: Target },
  { to: '/assistant', label: 'Assistant', short: 'Assistant', icon: MessagesSquare },
  { to: '/profil', label: 'Profil', short: 'Profil', icon: User },
]

function initials(name) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join('')
}

export default function Layout() {
  const { user, logout } = useAuth()
  return (
    <div className="shell">
      <aside className="sidebar">
        <Brand />
        <nav className="nav" aria-label="Navigation principale">
          {LINKS.map(({ to, label, short, icon: Icon, end }) => (
            <NavLink key={to} to={to} end={end} className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
              <Icon size={20} strokeWidth={1.5} />
              <span className="nav-long">{label}</span>
              <span className="nav-short">{short}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <span className="avatar">{initials(user.name)}</span>
          <div className="sidebar-user">
            <strong>{user.name}</strong>
            <span>{user.email}</span>
          </div>
          <IconButton icon={LogOut} label="Se déconnecter" onClick={logout} />
        </div>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  )
}
