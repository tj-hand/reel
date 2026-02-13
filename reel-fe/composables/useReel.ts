/**
 * useReel Composable
 *
 * Primary composable for audit logging functionality.
 * Provides logging actions and log management for Vue components.
 */

import { computed, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useReelStore } from '../stores/reelStore'
import { createLog } from '../services/reel-api'
import type {
  LogEntry,
  LogEntryCreate,
  LogSeverity,
  LogFilter,
  LogExportResponse,
} from '../types'

/**
 * Options for useReel composable
 */
export interface UseReelOptions {
  /**
   * Automatically load logs on mount
   * @default false
   */
  autoLoad?: boolean

  /**
   * Automatically load stats on mount
   * @default false
   */
  autoLoadStats?: boolean

  /**
   * Initial filter to apply
   */
  initialFilter?: LogFilter

  /**
   * Initial page size
   * @default 50
   */
  pageSize?: number
}

/**
 * useReel composable for audit logging
 *
 * @example
 * ```typescript
 * // Basic usage - logging actions
 * const { log } = useReel()
 *
 * await log({
 *   module: 'products',
 *   action: 'create',
 *   data: { productId: '123', name: 'Widget' }
 * })
 *
 * // Dashboard usage - viewing logs
 * const { logs, loadLogs, stats, filter, setFilter } = useReel({
 *   autoLoad: true,
 *   autoLoadStats: true,
 * })
 * ```
 */
export function useReel(options: UseReelOptions = {}) {
  const {
    autoLoad = false,
    autoLoadStats = false,
    initialFilter,
    pageSize = 50,
  } = options

  // Get store and refs
  const store = useReelStore()
  const {
    logs,
    currentLog,
    totalLogs,
    currentPage,
    totalPages,
    filter,
    stats,
    isLoading,
    isLoadingStats,
    isExporting,
    error,
    hasLogs,
    hasMorePages,
    hasPreviousPage,
    activeFiltersCount,
    hasActiveFilters,
  } = storeToRefs(store)

  // Local state for logging
  const isLogging = ref(false)
  const logError = ref<string | null>(null)

  // ============================================================================
  // LOGGING ACTIONS
  // ============================================================================

  /**
   * Log an action (client-side logging)
   *
   * Use this to log client-side actions. For backend actions,
   * use the ReelService directly in the backend.
   */
  async function log(entry: LogEntryCreate): Promise<LogEntry | null> {
    isLogging.value = true
    logError.value = null

    try {
      const result = await createLog(entry)
      return result
    } catch (e) {
      logError.value = e instanceof Error ? e.message : 'Failed to log action'
      console.error('[Reel] Log error:', e)
      return null
    } finally {
      isLogging.value = false
    }
  }

  /**
   * Helper to log with INFO severity
   */
  async function logInfo(
    module: string,
    action: string,
    data?: Record<string, unknown>
  ): Promise<LogEntry | null> {
    return log({ module, action, severity: 'INFO', data })
  }

  /**
   * Helper to log with WARNING severity
   */
  async function logWarning(
    module: string,
    action: string,
    data?: Record<string, unknown>
  ): Promise<LogEntry | null> {
    return log({ module, action, severity: 'WARNING', data })
  }

  /**
   * Helper to log with ERROR severity
   */
  async function logError(
    module: string,
    action: string,
    data?: Record<string, unknown>
  ): Promise<LogEntry | null> {
    return log({ module, action, severity: 'ERROR', data })
  }

  // ============================================================================
  // LOG VIEWING
  // ============================================================================

  /**
   * Load logs with current filter/pagination
   */
  async function loadLogs(): Promise<void> {
    await store.loadLogs()
  }

  /**
   * Load a single log entry
   */
  async function loadLog(logId: string): Promise<LogEntry | undefined> {
    try {
      return await store.loadLog(logId)
    } catch {
      return undefined
    }
  }

  /**
   * Load log statistics
   */
  async function loadStats(): Promise<void> {
    await store.loadStats()
  }

  /**
   * Refresh logs and stats
   */
  async function refresh(): Promise<void> {
    await store.refresh()
  }

  // ============================================================================
  // FILTERING
  // ============================================================================

  /**
   * Set filter and reload logs
   */
  async function setFilter(newFilter: LogFilter): Promise<void> {
    await store.setFilter(newFilter)
  }

  /**
   * Update a single filter property
   */
  async function updateFilter<K extends keyof LogFilter>(
    key: K,
    value: LogFilter[K]
  ): Promise<void> {
    await store.updateFilter(key, value)
  }

  /**
   * Clear all filters
   */
  async function clearFilters(): Promise<void> {
    await store.clearFilters()
  }

  /**
   * Filter by module
   */
  async function filterByModule(module: string | undefined): Promise<void> {
    await updateFilter('module', module)
  }

  /**
   * Filter by severity
   */
  async function filterBySeverity(
    severity: LogSeverity | undefined
  ): Promise<void> {
    await updateFilter('severity', severity)
  }

  /**
   * Filter by date range
   */
  async function filterByDateRange(
    startDate: string | undefined,
    endDate: string | undefined
  ): Promise<void> {
    await setFilter({
      ...filter.value,
      start_date: startDate,
      end_date: endDate,
    })
  }

  // ============================================================================
  // PAGINATION
  // ============================================================================

  /**
   * Go to next page
   */
  async function nextPage(): Promise<void> {
    await store.nextPage()
  }

  /**
   * Go to previous page
   */
  async function previousPage(): Promise<void> {
    await store.previousPage()
  }

  /**
   * Go to specific page
   */
  async function goToPage(page: number): Promise<void> {
    await store.goToPage(page)
  }

  // ============================================================================
  // EXPORT
  // ============================================================================

  /**
   * Export logs with current filter
   */
  async function exportLogs(
    format: 'csv' | 'json' = 'csv',
    includeData = false
  ): Promise<LogExportResponse | null> {
    try {
      return await store.exportCurrentLogs(format, includeData)
    } catch {
      return null
    }
  }

  // ============================================================================
  // LIFECYCLE
  // ============================================================================

  onMounted(async () => {
    // Apply initial filter if provided
    if (initialFilter) {
      store.filter = { ...initialFilter }
    }

    // Set page size
    if (pageSize !== store.pageSize) {
      store.pageSize = pageSize
    }

    // Auto-load on mount
    if (autoLoad) {
      await loadLogs()
    }

    if (autoLoadStats) {
      await loadStats()
    }
  })

  // ============================================================================
  // RETURN
  // ============================================================================

  return {
    // Logging
    log,
    logInfo,
    logWarning,
    logError,
    isLogging,
    logErrorMessage: logError,

    // State (readonly refs from store)
    logs,
    currentLog,
    totalLogs,
    currentPage,
    totalPages,
    filter,
    stats,
    isLoading,
    isLoadingStats,
    isExporting,
    error,

    // Computed
    hasLogs,
    hasMorePages,
    hasPreviousPage,
    activeFiltersCount,
    hasActiveFilters,

    // Actions
    loadLogs,
    loadLog,
    loadStats,
    refresh,
    setFilter,
    updateFilter,
    clearFilters,
    filterByModule,
    filterBySeverity,
    filterByDateRange,
    nextPage,
    previousPage,
    goToPage,
    exportLogs,
  }
}
