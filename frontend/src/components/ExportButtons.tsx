import { useState, useCallback } from 'react'

interface ArchiveResult {
  success: boolean
  archivePath?: string
  filesCreated?: string[]
  mediaDownloaded?: number
  mediaFailed?: number
  error?: string
}

interface ExportButtonsProps {
  content: string | null
  format: string
  handle: string | null
  onArchive: () => Promise<ArchiveResult>
  disabled?: boolean
}

export function ExportButtons({ content, format, handle, onArchive, disabled }: ExportButtonsProps) {
  const [copySuccess, setCopySuccess] = useState(false)
  const [archiveStatus, setArchiveStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle')
  const [archiveMessage, setArchiveMessage] = useState('')

  const handleCopy = useCallback(async () => {
    if (!content) return

    try {
      await navigator.clipboard.writeText(content)
      setCopySuccess(true)
      setTimeout(() => setCopySuccess(false), 2000)
    } catch {
      // Clipboard write failed
    }
  }, [content])

  const handleDownload = useCallback(() => {
    if (!content) return

    const extensions: Record<string, string> = {
      markdown: 'md',
      json: 'json',
    }

    const ext = extensions[format] || 'md'
    const filename = handle ? `${handle}_thread.${ext}` : `thread.${ext}`

    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)

    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }, [content, format, handle])

  const handleArchive = useCallback(async () => {
    setArchiveStatus('saving')
    setArchiveMessage('Downloading media...')

    const result = await onArchive()

    if (result.success) {
      setArchiveStatus('success')
      // Build success message with details
      const parts: string[] = []
      if (result.filesCreated?.length) {
        parts.push(result.filesCreated.join(', '))
      }
      if (result.mediaDownloaded !== undefined && result.mediaDownloaded > 0) {
        parts.push(`${result.mediaDownloaded} media files`)
      }
      if (result.mediaFailed !== undefined && result.mediaFailed > 0) {
        parts.push(`${result.mediaFailed} failed`)
      }
      setArchiveMessage(parts.length > 0 ? parts.join(' • ') : 'Saved!')
    } else {
      setArchiveStatus('error')
      setArchiveMessage(result.error || 'Failed to save')
    }

    setTimeout(() => {
      setArchiveStatus('idle')
      setArchiveMessage('')
    }, 5000)
  }, [onArchive])

  const isDisabled = disabled || !content

  return (
    <div className="space-y-4">
      <div className="label-field">Export</div>
      <div className="flex gap-3">
        {/* Copy Button */}
        <button
          onClick={handleCopy}
          disabled={isDisabled}
          className={`
            btn-ghost flex-1 px-4 py-2 font-medium text-sm
            flex items-center justify-center gap-2
            ${isDisabled ? 'opacity-50 cursor-not-allowed' : ''}
          `}
        >
          {copySuccess ? (
            <>
              <svg className="w-4 h-4 text-semantic-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Copied!
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
              </svg>
              Copy
            </>
          )}
        </button>

        {/* Download Button */}
        <button
          onClick={handleDownload}
          disabled={isDisabled}
          className={`
            btn-ghost flex-1 px-4 py-2 font-medium text-sm
            flex items-center justify-center gap-2
            ${isDisabled ? 'opacity-50 cursor-not-allowed' : ''}
          `}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Download
        </button>
      </div>

      {/* Archive Button - Primary action for full save with media */}
      <button
        onClick={handleArchive}
        disabled={isDisabled || archiveStatus === 'saving'}
        className={`
          btn-primary w-full px-4 py-3
          flex items-center justify-center gap-2
          ${isDisabled || archiveStatus === 'saving' ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        {archiveStatus === 'saving' ? (
          <>
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-bg-base border-t-transparent" />
            Saving with media...
          </>
        ) : archiveStatus === 'success' ? (
          <>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            Archived!
          </>
        ) : archiveStatus === 'error' ? (
          <>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
            Error
          </>
        ) : (
          <>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
            </svg>
            Save to Archive (with media)
          </>
        )}
      </button>

      {archiveMessage && (
        <p className={`text-xs text-center ${archiveStatus === 'error' ? 'text-semantic-error' : 'text-text-muted'}`}>
          {archiveMessage}
        </p>
      )}
    </div>
  )
}
