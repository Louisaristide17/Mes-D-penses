import { CircleAlert, CircleCheck, LoaderCircle, TriangleAlert, X } from 'lucide-react'
import { useEffect, useId, useRef } from 'react'

export function Button({ variant = 'primary', icon: Icon, loading = false, block = false, children, ...props }) {
  const classes = ['button']
  if (variant !== 'primary') classes.push(`button-${variant}`)
  if (block) classes.push('button-block')
  return (
    <button type="button" className={classes.join(' ')} {...props} disabled={loading || props.disabled}>
      {loading ? <LoaderCircle size={16} className="spin" /> : Icon && <Icon size={16} strokeWidth={1.75} />}
      {children}
    </button>
  )
}

export function IconButton({ icon: Icon, label, ...props }) {
  return (
    <button type="button" className="button button-ghost button-icon" aria-label={label} title={label} {...props}>
      <Icon size={16} strokeWidth={1.75} />
    </button>
  )
}

export function Field({ label, hint, error, children }) {
  const id = useId()
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      {children(id)}
      {error ? <span className="field-error">{error}</span> : hint && <span className="field-hint">{hint}</span>}
    </div>
  )
}

export function TextField({ label, hint, error, suffix, ...props }) {
  return (
    <Field label={label} hint={hint} error={error}>
      {(id) =>
        suffix ? (
          <div className="input-with-suffix">
            <input id={id} className="input" {...props} />
            <span className="input-suffix">{suffix}</span>
          </div>
        ) : (
          <input id={id} className="input" {...props} />
        )
      }
    </Field>
  )
}

export function SelectField({ label, hint, children, ...props }) {
  return (
    <Field label={label} hint={hint}>
      {(id) => (
        <select id={id} className="input" {...props}>
          {children}
        </select>
      )}
    </Field>
  )
}

const NOTICE_ICONS = { error: CircleAlert, success: CircleCheck, warning: TriangleAlert }

export function Notice({ tone = 'error', children }) {
  const Icon = NOTICE_ICONS[tone]
  return (
    <div className={`notice notice-${tone}`} role={tone === 'error' ? 'alert' : 'status'}>
      <Icon size={16} strokeWidth={1.75} />
      <span>{children}</span>
    </div>
  )
}

export function Loader() {
  return (
    <div className="loader" role="status" aria-label="Chargement">
      <LoaderCircle size={24} className="spin" />
    </div>
  )
}

export function EmptyState({ icon: Icon, title, text, action }) {
  return (
    <div className="empty">
      <div className="empty-icon">
        <Icon size={24} strokeWidth={1.5} />
      </div>
      <h2>{title}</h2>
      <p>{text}</p>
      {action}
    </div>
  )
}

export function Modal({ title, onClose, footer, children }) {
  const ref = useRef(null)
  // onClose change d'identité à chaque rendu du parent : on le garde dans une référence
  // pour que l'effet (et la prise de focus) ne s'exécute qu'à l'ouverture.
  const close = useRef(onClose)
  close.current = onClose

  useEffect(() => {
    const previous = document.activeElement
    ref.current?.querySelector('input, select, button')?.focus()
    const onKey = (event) => event.key === 'Escape' && close.current()
    document.addEventListener('keydown', onKey)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = ''
      previous?.focus?.()
    }
  }, [])

  return (
    <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <div className="modal" role="dialog" aria-modal="true" aria-label={title}>
        <div className="modal-header">
          <h2>{title}</h2>
          <IconButton icon={X} label="Fermer" onClick={onClose} />
        </div>
        <div ref={ref}>{children}</div>
        {footer && <div className="modal-footer">{footer}</div>}
      </div>
    </div>
  )
}

export function ConfirmDialog({ title, text, confirmLabel, loading, onConfirm, onClose }) {
  return (
    <Modal
      title={title}
      onClose={onClose}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Annuler
          </Button>
          <Button variant="danger" loading={loading} onClick={onConfirm}>
            {confirmLabel}
          </Button>
        </>
      }
    >
      <div className="modal-body">
        <p>{text}</p>
      </div>
    </Modal>
  )
}
