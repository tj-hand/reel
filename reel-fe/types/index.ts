/**
 * Reel types - TypeScript interfaces for audit logging
 */

/**
 * Log severity levels
 */
export type LogSeverity = 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL'

/**
 * Log entry from the API
 */
export interface LogEntry {
  id: string
  module: string
  action: string
  severity: LogSeverity
  actor_id: string | null
  actor_email: string | null
  actor_name: string | null
  tenant_id: string
  client_id: string | null
  resource_type: string | null
  resource_id: string | null
  data: Record<string, unknown> | null
  ip_address: string | null
  user_agent: string | null
  request_id: string | null
  created_at: string
}

/**
 * Filter parameters for log queries
 */
export interface LogFilter {
  start_date?: string
  end_date?: string
  actor_id?: string
  module?: string
  action?: string
  severity?: LogSeverity
  min_severity?: LogSeverity
  resource_type?: string
  resource_id?: string
  client_id?: string
  search?: string
}

/**
 * Paginated list of log entries
 */
export interface LogEntryList {
  items: LogEntry[]
  total: number
  page: number
  page_size: number
  pages: number
}

/**
 * Log statistics for a tenant
 */
export interface LogStats {
  total_entries: number
  entries_by_severity: Record<string, number>
  entries_by_module: Record<string, number>
  entries_today: number
  entries_this_week: number
}

/**
 * Request for log export
 */
export interface LogExportRequest {
  filter?: LogFilter
  format?: 'csv' | 'json'
  include_data?: boolean
}

/**
 * Response for log export
 */
export interface LogExportResponse {
  download_url: string
  filename: string
  record_count: number
  expires_at: string
}

/**
 * Create log entry request (for client-side logging)
 */
export interface LogEntryCreate {
  module: string
  action: string
  severity?: LogSeverity
  resource_type?: string
  resource_id?: string
  data?: Record<string, unknown>
}

/**
 * Pagination parameters
 */
export interface PaginationParams {
  page?: number
  page_size?: number
}

/**
 * Combined query parameters for log listing
 */
export type LogQueryParams = LogFilter & PaginationParams
