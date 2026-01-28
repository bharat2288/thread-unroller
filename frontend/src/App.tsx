import { useState, useCallback } from 'react'
import { UrlInput, FormatSelect, Preview, ExportButtons, StatusIndicator } from './components'
import { useUnroll } from './hooks/useUnroll'
import { useHealth } from './hooks/useHealth'
import { isValidTwitterUrl } from './utils/validators'
import type { OutputFormat } from './types'

function App() {
  const [url, setUrl] = useState('')
  const [format, setFormat] = useState<OutputFormat>('markdown')
  const [includeMedia, setIncludeMedia] = useState(true)

  const { health, loading: healthLoading, error: healthError } = useHealth()
  const { loading, data, error, unroll, archive, reset } = useUnroll()

  const canSubmit = isValidTwitterUrl(url) && !loading && health?.status === 'healthy'

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()
    if (canSubmit) {
      await unroll(url, format, includeMedia)
    }
  }, [canSubmit, url, format, includeMedia, unroll])

  const handleReset = useCallback(() => {
    setUrl('')
    reset()
  }, [reset])

  return (
    <div className="min-h-screen bg-bg-base">
      {/* Header with character moment */}
      <header className="border-b border-border-subtle">
        <div className="max-w-6xl mx-auto px-6 py-8">
          <div className="flex items-start justify-between">
            <div>
              {/* Character moment: Display font title with hand-drawn accent */}
              <div className="flex items-center gap-3">
                <h1 className="font-display text-5xl font-bold text-text-primary tracking-tight">
                  Thread Unroller
                </h1>
                {/* Hand-drawn unrolling thread accent */}
                <svg
                  className="w-12 h-12 opacity-45"
                  viewBox="0 0 48 48"
                  fill="none"
                  style={{ color: 'var(--color-accent-camel)' }}
                >
                  {/* Spool */}
                  <circle cx="12" cy="16" r="8" stroke="currentColor" strokeWidth="2" fill="none"/>
                  <circle cx="12" cy="16" r="3" fill="currentColor"/>
                  {/* Unrolling wavy thread */}
                  <path
                    d="M20 16 Q26 12, 30 18 Q34 26, 28 32 Q22 38, 30 42"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    fill="none"
                  />
                  {/* Tweet nodes along thread */}
                  <circle cx="30" cy="18" r="2" fill="currentColor"/>
                  <circle cx="28" cy="32" r="2" fill="currentColor"/>
                  <circle cx="30" cy="42" r="2" fill="currentColor"/>
                </svg>
              </div>
              <p className="mt-3 text-sm text-text-secondary max-w-md">
                Extract Twitter/X threads to Markdown, JSON, or HTML with media
              </p>
            </div>
            <StatusIndicator
              cookiesLoaded={health?.cookies_loaded ?? null}
              cookieCount={health?.cookie_count ?? 0}
              loading={healthLoading}
              error={healthError}
            />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column: Input Card */}
          <div className="card p-8">
            {/* Section header */}
            <div className="label-section mb-6">/ Input</div>

            <form onSubmit={handleSubmit} className="space-y-6">
              <UrlInput
                value={url}
                onChange={setUrl}
                disabled={loading}
              />

              <FormatSelect
                value={format}
                onChange={setFormat}
                disabled={loading}
              />

              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  id="include-media"
                  checked={includeMedia}
                  onChange={(e) => setIncludeMedia(e.target.checked)}
                  disabled={loading}
                  className="w-4 h-4 rounded border-border-subtle bg-bg-base text-accent-camel focus:ring-accent-camel focus:ring-offset-0"
                />
                <label htmlFor="include-media" className="text-sm text-text-secondary">
                  Include media URLs in output
                </label>
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="submit"
                  disabled={!canSubmit}
                  className="btn-primary flex-1 px-6 py-3 flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-2 border-bg-base border-t-transparent" />
                      Extracting...
                    </>
                  ) : (
                    <>
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      Unroll Thread
                    </>
                  )}
                </button>

                {data && (
                  <button
                    type="button"
                    onClick={handleReset}
                    className="btn-ghost px-4 py-3"
                  >
                    Clear
                  </button>
                )}
              </div>
            </form>

            {/* Error Display */}
            {error && (
              <div className="mt-6 p-4 rounded-lg bg-semantic-error/10 border border-semantic-error/30">
                <p className="label-field text-semantic-error">Error</p>
                <p className="text-semantic-error/80 text-sm mt-1">{error}</p>
              </div>
            )}

            {/* Success Info */}
            {data?.thread_data && (
              <div className="mt-6 p-4 rounded-lg bg-semantic-success/10 border border-semantic-success/30">
                <p className="label-field text-semantic-success">Thread extracted</p>
                <p className="text-semantic-success/80 text-sm mt-1">
                  {data.thread_data.tweet_count} tweets by @{data.thread_data.handle}
                  {data.thread_data.date && ` • ${data.thread_data.date}`}
                </p>
              </div>
            )}

            {/* Export Buttons */}
            {data && (
              <div className="mt-6 pt-6 border-t border-border-subtle">
                <ExportButtons
                  content={data.formatted_output}
                  format={data.format}
                  handle={data.thread_data?.handle ?? null}
                  onArchive={archive}
                  disabled={loading}
                />
              </div>
            )}
          </div>

          {/* Right Column: Preview Card */}
          <div className="lg:sticky lg:top-8 lg:self-start">
            <div className="card overflow-hidden">
              <div className="px-6 py-4 border-b border-border-subtle flex items-center justify-between">
                <span className="label-section">/ Preview</span>
                {data?.format && (
                  <span className="label-field">{data.format}</span>
                )}
              </div>
              <div className="h-[500px]">
                <Preview
                  content={data?.formatted_output ?? null}
                  format={data?.format ?? format}
                  loading={loading}
                />
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border-subtle mt-12">
        <div className="max-w-6xl mx-auto px-6 py-4 text-center text-text-muted text-sm">
          Thread Unroller • Local-first Twitter thread extraction
        </div>
      </footer>
    </div>
  )
}

export default App
