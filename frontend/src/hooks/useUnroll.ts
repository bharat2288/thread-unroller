import { useState, useCallback } from 'react'
import type { UnrollResponse, OutputFormat } from '../types'
import { unrollThread, saveToArchive } from '../utils/api'
import { normalizeUrl } from '../utils/validators'

interface UnrollState {
  loading: boolean
  data: UnrollResponse | null
  error: string | null
}

interface ArchiveResult {
  success: boolean
  archivePath?: string
  filesCreated?: string[]
  mediaDownloaded?: number
  mediaFailed?: number
  error?: string
}

interface UseUnrollReturn extends UnrollState {
  unroll: (url: string, format: OutputFormat, includeMedia: boolean) => Promise<void>
  archive: () => Promise<ArchiveResult>
  reset: () => void
}

export function useUnroll(): UseUnrollReturn {
  const [state, setState] = useState<UnrollState>({
    loading: false,
    data: null,
    error: null,
  })

  const unroll = useCallback(async (
    url: string,
    format: OutputFormat,
    includeMedia: boolean
  ) => {
    setState({ loading: true, data: null, error: null })

    try {
      const normalizedUrl = normalizeUrl(url)
      const result = await unrollThread({
        url: normalizedUrl,
        format,
        include_media: includeMedia,
      })

      if (result.success) {
        setState({ loading: false, data: result, error: null })
      } else {
        setState({
          loading: false,
          data: null,
          error: result.error || 'Unknown error occurred',
        })
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to connect to server'
      setState({ loading: false, data: null, error: errorMessage })
    }
  }, [])

  const archive = useCallback(async (): Promise<ArchiveResult> => {
    if (!state.data?.thread_data) {
      return { success: false, error: 'No thread data to archive' }
    }

    try {
      const result = await saveToArchive(state.data.thread_data)
      return {
        success: result.success,
        archivePath: result.archive_path ?? undefined,
        filesCreated: result.files_created,
        mediaDownloaded: result.media_downloaded,
        mediaFailed: result.media_failed,
        error: result.error ?? undefined,
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save to archive'
      return { success: false, error: errorMessage }
    }
  }, [state.data])

  const reset = useCallback(() => {
    setState({ loading: false, data: null, error: null })
  }, [])

  return {
    ...state,
    unroll,
    archive,
    reset,
  }
}
