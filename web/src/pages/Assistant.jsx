import { MessageSquarePlus, MessagesSquare, SendHorizontal } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

import { Button, Notice } from '../components/ui'
import { api } from '../lib/api'

const SUGGESTIONS = [
  'Combien ai-je dépensé ce mois-ci ?',
  'Quelle est ma plus grosse dépense du mois ?',
  'Où en sont mes budgets ?',
  'Ajoute 2 000 FCFA de taxi',
  'Comment mieux tenir mon budget ?',
]

// Noms des outils renvoyés par l'API, traduits pour l'utilisateur.
const TOOL_LABELS = {
  total_depenses: 'total des dépenses',
  depenses_par_categorie: 'répartition par catégorie',
  lister_depenses: 'liste des dépenses',
  etat_budgets: 'état des budgets',
  ajouter_depense: 'ajout d’une dépense',
}

function sourcesOf(tools) {
  return tools.map((tool) => TOOL_LABELS[tool] || tool).join(', ')
}

export default function Assistant() {
  const [messages, setMessages] = useState([])
  const [conversationId, setConversationId] = useState(null)
  const [draft, setDraft] = useState('')
  const [waiting, setWaiting] = useState(false)
  const [error, setError] = useState(null)
  const bottom = useRef(null)
  const input = useRef(null)

  useEffect(() => {
    bottom.current?.scrollIntoView({ block: 'end' })
  }, [messages, waiting])

  async function send(text) {
    const message = text.trim()
    if (!message || waiting) return
    setMessages((previous) => [...previous, { role: 'user', content: message }])
    setDraft('')
    setError(null)
    setWaiting(true)
    try {
      const answer = await api.askAssistant({ message, conversation_id: conversationId })
      setConversationId(answer.conversation_id)
      setMessages((previous) => [
        ...previous,
        { role: 'assistant', content: answer.reply, tools: answer.tools_used, changed: answer.data_changed },
      ])
    } catch (failure) {
      // La question reste affichée : l'utilisateur peut la renvoyer sans la retaper.
      setError(failure.message)
      setDraft(message)
      setMessages((previous) => previous.slice(0, -1))
    } finally {
      setWaiting(false)
      input.current?.focus()
    }
  }

  function reset() {
    setMessages([])
    setConversationId(null)
    setError(null)
    input.current?.focus()
  }

  return (
    <div className="chat">
      <header className="page-header">
        <div>
          <h1>Assistant</h1>
          <p>Interrogez vos dépenses, ajoutez-en une, ou posez une question générale.</p>
        </div>
        {messages.length > 0 && (
          <Button variant="secondary" icon={MessageSquarePlus} onClick={reset}>
            Nouvelle conversation
          </Button>
        )}
      </header>

      <section className="card chat-card">
        <div className="chat-messages" aria-live="polite">
          {messages.length === 0 && !waiting && (
            <div className="chat-empty">
              <div className="empty-icon">
                <MessagesSquare size={24} strokeWidth={1.5} />
              </div>
              <h2>Que voulez-vous savoir ?</h2>
              <p>Les chiffres viennent de vos dépenses et de vos budgets. Pour le reste, l’assistant répond à partir de ses connaissances générales, sans accès à internet.</p>
              <div className="chat-suggestions">
                {SUGGESTIONS.map((suggestion) => (
                  <button key={suggestion} type="button" className="chip" onClick={() => send(suggestion)}>
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message, index) => (
            <div key={index} className={`bubble-row ${message.role}`}>
              <div className={`bubble ${message.role}`}>
                {message.content}
                {message.tools?.length > 0 && (
                  <span className="bubble-sources">
                    {message.changed ? 'Action : ' : 'Calculé à partir de : '}
                    {sourcesOf(message.tools)}
                  </span>
                )}
              </div>
            </div>
          ))}

          {waiting && (
            <div className="bubble-row assistant">
              <div className="bubble assistant typing" role="status" aria-label="L’assistant rédige sa réponse">
                <span />
                <span />
                <span />
              </div>
            </div>
          )}
          <div ref={bottom} />
        </div>

        {error && (
          <div className="chat-error">
            <Notice>{error}</Notice>
          </div>
        )}

        <form
          className="chat-form"
          onSubmit={(event) => {
            event.preventDefault()
            send(draft)
          }}
        >
          <input
            ref={input}
            className="input"
            aria-label="Votre message"
            placeholder="Écrivez votre question"
            maxLength={1000}
            autoFocus
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
          />
          <Button type="submit" icon={SendHorizontal} disabled={!draft.trim()} loading={waiting}>
            Envoyer
          </Button>
        </form>
      </section>
    </div>
  )
}
