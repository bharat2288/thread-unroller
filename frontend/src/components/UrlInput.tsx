import { useState, useCallback } from 'react'
import { isValidTwitterUrl } from '../utils/validators'

interface UrlInputProps {
  value: string
  onChange: (value: string) => void
  disabled?: boolean
}

export function UrlInput({ value, onChange, disabled }: UrlInputProps) {
  const [touched, setTouched] = useState(false)

  const isValid = !touched || !value || isValidTwitterUrl(value)

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(e.target.value)
  }, [onChange])

  const handleBlur = useCallback(() => {
    setTouched(true)
  }, [])

  const handleClear = useCallback(() => {
    onChange('')
    setTouched(false)
  }, [onChange])

  const handlePaste = useCallback(async () => {
    try {
      const text = await navigator.clipboard.readText()
      onChange(text)
      setTouched(true)
    } catch {
      // Clipboard access denied
    }
  }, [onChange])

  return (
    <div className="space-y-2">
      <label htmlFor="url-input" className="label-field block">
        Thread URL
      </label>
      <div className="relative">
        <input
          id="url-input"
          type="text"
          value={value}
          onChange={handleChange}
          onBlur={handleBlur}
          disabled={disabled}
          placeholder="https://x.com/user/status/123456789"
          className={`
            input-field w-full px-4 py-3
            disabled:opacity-50 disabled:cursor-not-allowed
            ${!isValid ? 'border-semantic-error' : ''}
          `}
        />
        {value && !disabled && (
          <button
            type="button"
            onClick={handleClear}
            className="absolute right-12 top-1/2 -translate-y-1/2 p-1 text-text-muted hover:text-text-secondary transition-colors"
            aria-label="Clear input"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
        <button
          type="button"
          onClick={handlePaste}
          disabled={disabled}
          className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-text-muted hover:text-text-secondary disabled:opacity-50 transition-colors"
          aria-label="Paste from clipboard"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
        </button>
      </div>
      {!isValid && (
        <p className="text-sm text-semantic-error">
          Please enter a valid Twitter/X thread URL
        </p>
      )}
      <p className="text-xs text-text-muted">
        Paste a Twitter or X.com thread URL to extract its content
      </p>
    </div>
  )
}
