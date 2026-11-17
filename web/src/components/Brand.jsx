export default function Brand({ className = '' }) {
  return (
    <div className={`brand ${className}`}>
      <span className="brand-mark" aria-hidden="true">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <path d="M3 13V5l6 6 6-6v8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </span>
      Mes Dépenses
    </div>
  )
}
