import { ChartPie, Receipt, Target } from 'lucide-react'

import Brand from './Brand'

const POINTS = [
  { icon: Receipt, text: 'Notez une dépense en quelques secondes' },
  { icon: ChartPie, text: 'Voyez où part votre argent, mois après mois' },
  { icon: Target, text: 'Fixez un budget et soyez prévenu avant de le dépasser' },
]

export default function AuthScreen({ title, subtitle, children, footer }) {
  return (
    <div className="auth">
      <aside className="auth-aside">
        <Brand />
        <div className="auth-pitch">
          <h2>Gardez la main sur vos dépenses, au franc près.</h2>
          <ul>
            {POINTS.map(({ icon: Icon, text }) => (
              <li key={text}>
                <Icon size={20} strokeWidth={1.5} />
                {text}
              </li>
            ))}
          </ul>
        </div>
        <small>Vos données restent privées et ne sont visibles que de vous.</small>
      </aside>
      <main className="auth-main">
        <div className="auth-form">
          <Brand className="auth-brand-mobile" />
          <h1>{title}</h1>
          <p>{subtitle}</p>
          {children}
          <div className="auth-switch">{footer}</div>
        </div>
      </main>
    </div>
  )
}
