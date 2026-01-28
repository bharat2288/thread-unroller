interface StatusIndicatorProps {
  cookiesLoaded: boolean | null
  cookieCount: number
  loading: boolean
  error: string | null
}

export function StatusIndicator({ cookiesLoaded, cookieCount, loading, error }: StatusIndicatorProps) {
  if (loading) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-bg-surface border border-border-subtle">
        <div className="animate-pulse w-2 h-2 rounded-full bg-accent-camel" />
        <span className="text-text-secondary text-sm">Checking...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-bg-surface border border-border-subtle">
        <div className="status-dot-offline" />
        <span className="text-semantic-error text-sm">Backend offline</span>
      </div>
    )
  }

  if (cookiesLoaded) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-bg-surface border border-border-subtle">
        <div className="status-dot-online" />
        <span className="text-text-secondary text-sm">Ready ({cookieCount} cookies)</span>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-bg-surface border border-border-subtle">
      <div className="w-2 h-2 rounded-full bg-accent-camel" />
      <span className="text-accent-camel text-sm">No cookies</span>
    </div>
  )
}
