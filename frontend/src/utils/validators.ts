/**
 * Validate that a URL is a valid Twitter/X status URL.
 */
export function isValidTwitterUrl(url: string): boolean {
  if (!url.trim()) return false

  try {
    // Add protocol if missing
    let normalizedUrl = url.trim()
    if (!normalizedUrl.startsWith('http://') && !normalizedUrl.startsWith('https://')) {
      normalizedUrl = 'https://' + normalizedUrl
    }

    const parsed = new URL(normalizedUrl)
    const domain = parsed.hostname.toLowerCase().replace('www.', '')

    // Check domain
    const validDomains = ['x.com', 'twitter.com', 'mobile.twitter.com']
    if (!validDomains.includes(domain)) {
      return false
    }

    // Check for /status/ in path
    if (!parsed.pathname.includes('/status/')) {
      return false
    }

    return true
  } catch {
    return false
  }
}

/**
 * Normalize a Twitter URL (add protocol if missing).
 */
export function normalizeUrl(url: string): string {
  const trimmed = url.trim()
  if (!trimmed.startsWith('http://') && !trimmed.startsWith('https://')) {
    return 'https://' + trimmed
  }
  return trimmed
}

/**
 * Extract handle from Twitter URL.
 */
export function extractHandle(url: string): string | null {
  try {
    const normalized = normalizeUrl(url)
    const parsed = new URL(normalized)
    const parts = parsed.pathname.split('/').filter(Boolean)
    if (parts.length > 0 && parts[0] !== 'i' && parts[0] !== 'status') {
      return parts[0]
    }
  } catch {
    // Invalid URL
  }
  return null
}
