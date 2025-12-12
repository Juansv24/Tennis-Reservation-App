/**
 * Server-side Colombian Timezone Utilities
 * For use in API routes and server components
 * All dates and times use America/Bogota timezone (UTC-5)
 */

// Colombia timezone offset: UTC-5 (no DST)
const COLOMBIA_OFFSET_HOURS = -5

/**
 * Get current date and time in Colombian timezone (for server-side use)
 * Use this instead of new Date() in API routes
 */
export function getColombiaTimeServer(): Date {
  const now = new Date()

  // Get UTC time
  const utc = now.getTime() + (now.getTimezoneOffset() * 60000)

  // Apply Colombia offset
  const colombiaTime = new Date(utc + (3600000 * COLOMBIA_OFFSET_HOURS))

  return colombiaTime
}

/**
 * Get current hour in Colombian timezone (0-23) - server-side
 */
export function getColombiaHourServer(): number {
  return getColombiaTimeServer().getHours()
}

/**
 * Get today's date in Colombian timezone (YYYY-MM-DD format) - server-side
 */
export function getColombiaTodayServer(): string {
  const colombiaTime = getColombiaTimeServer()
  // Extract date components directly (don't use toISOString which converts back to UTC!)
  const year = colombiaTime.getFullYear()
  const month = String(colombiaTime.getMonth() + 1).padStart(2, '0')
  const day = String(colombiaTime.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

/**
 * Get tomorrow's date in Colombian timezone (YYYY-MM-DD format) - server-side
 */
export function getColombiaTomorrowServer(): string {
  const colombiaTime = getColombiaTimeServer()
  colombiaTime.setDate(colombiaTime.getDate() + 1)
  // Extract date components directly (don't use toISOString which converts back to UTC!)
  const year = colombiaTime.getFullYear()
  const month = String(colombiaTime.getMonth() + 1).padStart(2, '0')
  const day = String(colombiaTime.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

/**
 * Add hours to current Colombian time (for token expiration)
 * @param hours - Number of hours to add
 */
export function getColombiaTimePlusHours(hours: number): Date {
  const colombiaTime = getColombiaTimeServer()
  colombiaTime.setHours(colombiaTime.getHours() + hours)
  return colombiaTime
}
