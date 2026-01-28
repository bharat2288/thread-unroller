import type {
  UnrollRequest,
  UnrollResponse,
  HealthResponse,
  ArchiveRequest,
  ArchiveResponse,
  ThreadData
} from '../types'

const API_BASE = 'http://localhost:8000'

export async function checkHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE}/health`)
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`)
  }
  return response.json()
}

export async function unrollThread(request: UnrollRequest): Promise<UnrollResponse> {
  const response = await fetch(`${API_BASE}/unroll`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    throw new Error(`Unroll request failed: ${response.status}`)
  }

  return response.json()
}

export async function saveToArchive(
  threadData: ThreadData
): Promise<ArchiveResponse> {
  const request: ArchiveRequest = {
    thread_data: threadData,
  }

  const response = await fetch(`${API_BASE}/archive`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    throw new Error(`Archive request failed: ${response.status}`)
  }

  return response.json()
}
