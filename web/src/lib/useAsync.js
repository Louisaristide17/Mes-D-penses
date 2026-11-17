import { useCallback, useEffect, useRef, useState } from 'react'

// Charge une ressource et la recharge quand les dépendances changent.
// Une réponse arrivée après une requête plus récente est ignorée.
export function useAsync(loader, deps) {
  const [state, setState] = useState({ data: null, error: null, loading: true })
  const latest = useRef(0)

  const reload = useCallback(() => {
    const call = ++latest.current
    setState((previous) => ({ ...previous, loading: true, error: null }))
    return loader()
      .then((data) => {
        if (call === latest.current) setState({ data, error: null, loading: false })
      })
      .catch((error) => {
        if (call === latest.current) setState({ data: null, error: error.message, loading: false })
      })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  useEffect(() => {
    reload()
  }, [reload])

  return { ...state, reload }
}
