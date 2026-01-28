interface PreviewProps {
  content: string | null
  format: string
  loading?: boolean
}

export function Preview({ content, format, loading }: PreviewProps) {
  if (loading) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-text-secondary p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-accent-camel border-t-transparent mb-4" />
        <p className="text-text-primary">Extracting thread...</p>
        <p className="text-sm mt-1 text-text-muted">This may take 10-30 seconds</p>
      </div>
    )
  }

  if (!content) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-text-secondary p-8">
        <svg className="w-16 h-16 mb-4 text-text-muted opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p className="text-text-secondary">Thread preview will appear here</p>
        <p className="text-sm mt-1 text-text-muted">Enter a URL and click Unroll</p>
      </div>
    )
  }

  // Determine styling based on format
  const isCode = format === 'json'

  return (
    <div className="h-full overflow-auto bg-bg-base">
      <pre
        className={`
          p-6 text-sm leading-relaxed whitespace-pre-wrap break-words
          ${isCode ? 'font-mono text-semantic-success' : 'text-text-primary'}
        `}
      >
        {content}
      </pre>
    </div>
  )
}
