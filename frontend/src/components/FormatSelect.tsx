import type { OutputFormat } from '../types'

interface FormatSelectProps {
  value: OutputFormat
  onChange: (value: OutputFormat) => void
  disabled?: boolean
}

const formats: { value: OutputFormat; label: string; description: string }[] = [
  { value: 'markdown', label: 'Markdown', description: 'Best for LLMs and notes' },
  { value: 'json', label: 'JSON', description: 'Structured data format' },
]

export function FormatSelect({ value, onChange, disabled }: FormatSelectProps) {
  return (
    <div className="space-y-2">
      <label className="label-field block">
        Output Format
      </label>
      <div className="flex gap-3">
        {formats.map((format) => (
          <label
            key={format.value}
            className={`
              flex-1 relative cursor-pointer
              ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
            `}
          >
            <input
              type="radio"
              name="format"
              value={format.value}
              checked={value === format.value}
              onChange={() => onChange(format.value)}
              disabled={disabled}
              className="sr-only"
            />
            <div
              className={`
                p-3 rounded-lg border text-center transition-all
                ${value === format.value
                  ? 'border-accent-camel bg-accent-camel-subtle text-text-primary'
                  : 'border-border-subtle bg-bg-surface text-text-secondary hover:border-border-default'
                }
              `}
            >
              <div className="font-semibold text-sm">{format.label}</div>
              <div className="text-xs mt-1 text-text-muted">{format.description}</div>
            </div>
          </label>
        ))}
      </div>
    </div>
  )
}
