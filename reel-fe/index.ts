/**
 * Reel Frontend Module
 *
 * Audit logging for all modules with log visualization.
 *
 * Exports:
 * - useReelStore: Pinia store for log state management
 * - useReel: Composable for logging and log viewing
 * - API functions: fetchLogs, fetchLog, fetchLogStats, exportLogs, createLog
 * - Types: LogEntry, LogFilter, LogStats, etc.
 */

// Store
export { useReelStore } from './stores'

// Composable
export { useReel } from './composables'
export type { UseReelOptions } from './composables/useReel'

// API functions
export {
  fetchLogs,
  fetchLog,
  fetchLogStats,
  exportLogs,
  createLog,
  downloadLogExport,
} from './services/reel-api'

// Types
export type {
  LogEntry,
  LogSeverity,
  LogFilter,
  LogEntryList,
  LogStats,
  LogExportRequest,
  LogExportResponse,
  LogEntryCreate,
  LogQueryParams,
  PaginationParams,
} from './types'
