/**
 * Reel API Service
 *
 * HTTP client functions for audit log endpoints.
 * Uses Evoke client for authenticated requests.
 */

import { createClient } from '@/evoke'
import type {
  LogEntry,
  LogEntryList,
  LogStats,
  LogQueryParams,
  LogExportRequest,
  LogExportResponse,
  LogEntryCreate,
} from '../types'

// Create Evoke client instance
const client = createClient({
  baseURL: '/api',
})

/**
 * Build query string from params object
 */
function buildQueryParams(params: LogQueryParams): URLSearchParams {
  const searchParams = new URLSearchParams()

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.append(key, String(value))
    }
  })

  return searchParams
}

/**
 * Fetch paginated list of log entries
 */
export async function fetchLogs(params: LogQueryParams = {}): Promise<LogEntryList> {
  const queryParams = buildQueryParams(params)
  const queryString = queryParams.toString()
  const url = queryString ? `/v1/reel/logs?${queryString}` : '/v1/reel/logs'

  const response = await client.get<LogEntryList>(url)
  return response.data
}

/**
 * Fetch a single log entry by ID
 */
export async function fetchLog(logId: string): Promise<LogEntry> {
  const response = await client.get<LogEntry>(`/v1/reel/logs/${logId}`)
  return response.data
}

/**
 * Fetch log statistics for the current tenant
 */
export async function fetchLogStats(): Promise<LogStats> {
  const response = await client.get<LogStats>('/v1/reel/logs/stats')
  return response.data
}

/**
 * Export logs to file format
 */
export async function exportLogs(request: LogExportRequest = {}): Promise<LogExportResponse> {
  const response = await client.post<LogExportResponse>('/v1/reel/logs/export', request)
  return response.data
}

/**
 * Create a log entry (for client-side logging)
 *
 * Note: This is typically used for logging client-side actions.
 * Backend actions should use the ReelService directly.
 */
export async function createLog(entry: LogEntryCreate): Promise<LogEntry> {
  const response = await client.post<LogEntry>('/v1/reel/logs', entry)
  return response.data
}

/**
 * Download exported log file
 */
export async function downloadLogExport(downloadUrl: string): Promise<Blob> {
  const response = await client.get(downloadUrl, {
    responseType: 'blob',
  })
  return response.data
}
