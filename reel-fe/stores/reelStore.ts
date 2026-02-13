/**
 * Reel Store
 *
 * Pinia store for audit log state management.
 * Handles log listing, filtering, pagination, and statistics.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  LogEntry,
  LogEntryList,
  LogStats,
  LogFilter,
  LogQueryParams,
  LogExportRequest,
  LogExportResponse,
} from '../types'
import {
  fetchLogs,
  fetchLog,
  fetchLogStats,
  exportLogs,
} from '../services/reel-api'

export const useReelStore = defineStore('reel', () => {
  // ============================================================================
  // STATE
  // ============================================================================

  // Log entries
  const logs = ref<LogEntry[]>([])
  const currentLog = ref<LogEntry | null>(null)

  // Pagination
  const totalLogs = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(50)
  const totalPages = ref(0)

  // Filter state
  const filter = ref<LogFilter>({})

  // Statistics
  const stats = ref<LogStats | null>(null)

  // Loading states
  const isLoading = ref(false)
  const isLoadingStats = ref(false)
  const isExporting = ref(false)

  // Error state
  const error = ref<string | null>(null)

  // ============================================================================
  // GETTERS (Computed)
  // ============================================================================

  const hasLogs = computed(() => logs.value.length > 0)
  const hasMorePages = computed(() => currentPage.value < totalPages.value)
  const hasPreviousPage = computed(() => currentPage.value > 1)

  const activeFiltersCount = computed(() => {
    return Object.values(filter.value).filter(
      (v) => v !== undefined && v !== null && v !== ''
    ).length
  })

  const hasActiveFilters = computed(() => activeFiltersCount.value > 0)

  // ============================================================================
  // ACTIONS
  // ============================================================================

  /**
   * Load logs with current filter and pagination
   */
  async function loadLogs(resetPage = false): Promise<void> {
    if (resetPage) {
      currentPage.value = 1
    }

    const params: LogQueryParams = {
      ...filter.value,
      page: currentPage.value,
      page_size: pageSize.value,
    }

    isLoading.value = true
    error.value = null

    try {
      const result = await fetchLogs(params)
      logs.value = result.items
      totalLogs.value = result.total
      totalPages.value = result.pages
      currentPage.value = result.page
      pageSize.value = result.page_size
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load logs'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Load a single log entry
   */
  async function loadLog(logId: string): Promise<LogEntry> {
    isLoading.value = true
    error.value = null

    try {
      const result = await fetchLog(logId)
      currentLog.value = result
      return result
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load log'
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Load log statistics
   */
  async function loadStats(): Promise<void> {
    isLoadingStats.value = true
    error.value = null

    try {
      stats.value = await fetchLogStats()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load stats'
      throw e
    } finally {
      isLoadingStats.value = false
    }
  }

  /**
   * Export logs with current filter
   */
  async function exportCurrentLogs(
    format: 'csv' | 'json' = 'csv',
    includeData = false
  ): Promise<LogExportResponse> {
    const request: LogExportRequest = {
      filter: hasActiveFilters.value ? filter.value : undefined,
      format,
      include_data: includeData,
    }

    isExporting.value = true
    error.value = null

    try {
      const result = await exportLogs(request)
      return result
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to export logs'
      throw e
    } finally {
      isExporting.value = false
    }
  }

  /**
   * Go to next page
   */
  async function nextPage(): Promise<void> {
    if (hasMorePages.value) {
      currentPage.value++
      await loadLogs()
    }
  }

  /**
   * Go to previous page
   */
  async function previousPage(): Promise<void> {
    if (hasPreviousPage.value) {
      currentPage.value--
      await loadLogs()
    }
  }

  /**
   * Go to specific page
   */
  async function goToPage(page: number): Promise<void> {
    if (page >= 1 && page <= totalPages.value) {
      currentPage.value = page
      await loadLogs()
    }
  }

  /**
   * Set filter and reload logs
   */
  async function setFilter(newFilter: LogFilter): Promise<void> {
    filter.value = { ...newFilter }
    await loadLogs(true) // Reset to page 1
  }

  /**
   * Update filter property and reload
   */
  async function updateFilter<K extends keyof LogFilter>(
    key: K,
    value: LogFilter[K]
  ): Promise<void> {
    filter.value[key] = value
    await loadLogs(true)
  }

  /**
   * Clear all filters and reload
   */
  async function clearFilters(): Promise<void> {
    filter.value = {}
    await loadLogs(true)
  }

  /**
   * Set page size and reload
   */
  async function setPageSize(size: number): Promise<void> {
    pageSize.value = size
    await loadLogs(true)
  }

  /**
   * Refresh current view
   */
  async function refresh(): Promise<void> {
    await loadLogs()
    await loadStats()
  }

  /**
   * Clear current log selection
   */
  function clearCurrentLog(): void {
    currentLog.value = null
  }

  /**
   * Reset store to initial state
   */
  function $reset(): void {
    logs.value = []
    currentLog.value = null
    totalLogs.value = 0
    currentPage.value = 1
    pageSize.value = 50
    totalPages.value = 0
    filter.value = {}
    stats.value = null
    isLoading.value = false
    isLoadingStats.value = false
    isExporting.value = false
    error.value = null
  }

  // ============================================================================
  // RETURN
  // ============================================================================

  return {
    // State
    logs,
    currentLog,
    totalLogs,
    currentPage,
    pageSize,
    totalPages,
    filter,
    stats,
    isLoading,
    isLoadingStats,
    isExporting,
    error,

    // Getters
    hasLogs,
    hasMorePages,
    hasPreviousPage,
    activeFiltersCount,
    hasActiveFilters,

    // Actions
    loadLogs,
    loadLog,
    loadStats,
    exportCurrentLogs,
    nextPage,
    previousPage,
    goToPage,
    setFilter,
    updateFilter,
    clearFilters,
    setPageSize,
    refresh,
    clearCurrentLog,
    $reset,
  }
})
