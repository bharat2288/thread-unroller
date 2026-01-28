// API types matching the backend models

export interface Tweet {
  index: number
  text: string
  timestamp: string | null
  media_urls: string[]
}

export interface ThreadData {
  author: string
  handle: string
  date: string | null
  tweet_count: number
  tweets: Tweet[]
  thread_url: string
  tweet_id: string | null
}

export interface UnrollRequest {
  url: string
  format: 'markdown' | 'json'
  include_media: boolean
}

export interface UnrollResponse {
  success: boolean
  thread_data: ThreadData | null
  formatted_output: string | null
  format: string
  error: string | null
  error_code: string | null
}

export interface HealthResponse {
  status: string
  cookies_loaded: boolean
  cookie_count: number
  cookie_file_exists: boolean
}

export interface ArchiveRequest {
  url?: string
  thread_data?: ThreadData
}

export interface ArchiveResponse {
  success: boolean
  archive_path: string | null
  files_created: string[]
  media_downloaded: number
  media_failed: number
  error: string | null
}

export type OutputFormat = 'markdown' | 'json'
