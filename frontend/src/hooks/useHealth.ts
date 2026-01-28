import { useState, useEffect, useCallback } from 'react'
import type { HealthResponse } from '../types'
import { checkHealth } from '../utils/api'

interface UseHealthReturn {
  health: HealthResponse | null
  loading: boolean
  error: string | null
  refresh: () => void
}

export function useHealth(): UseHealthReturn {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const result = await checkHealth()
      setHealth(result)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to check health'
      setError(message)
      setHealth(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  return { health, loading, error, refresh }
}
