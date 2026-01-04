/**
 * Colombian Timezone Utilities
 * All dates and times in the app use America/Bogota timezone (UTC-5)
 */

// Colombia timezone offset: UTC-5 (no DST)
const COLOMBIA_OFFSET_HOURS = -5

/**
 * Get current date and time in Colombian timezone
 */
export function getColombiaTime(): Date {
  const now = new Date()

  // Get UTC time
  const utc = now.getTime() + (now.getTimezoneOffset() * 60000)

  // Apply Colombia offset
  const colombiaTime = new Date(utc + (3600000 * COLOMBIA_OFFSET_HOURS))

  return colombiaTime
}

/**
 * Get current hour in Colombian timezone (0-23)
 */
export function getColombiaHour(): number {
  return getColombiaTime().getHours()
}

/**
 * Get current minute in Colombian timezone (0-59)
 */
export function getColombiaMinute(): number {
  return getColombiaTime().getMinutes()
}

/**
 * Get today's date in Colombian timezone (YYYY-MM-DD format)
 */
export function getColombiaToday(): string {
  const colombiaTime = getColombiaTime()
  // Extract date components directly (don't use toISOString which converts back to UTC!)
  const year = colombiaTime.getFullYear()
  const month = String(colombiaTime.getMonth() + 1).padStart(2, '0')
  const day = String(colombiaTime.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

/**
 * Get tomorrow's date in Colombian timezone (YYYY-MM-DD format)
 */
export function getColombiaTomorrow(): string {
  const colombiaTime = getColombiaTime()
  colombiaTime.setDate(colombiaTime.getDate() + 1)
  // Extract date components directly (don't use toISOString which converts back to UTC!)
  const year = colombiaTime.getFullYear()
  const month = String(colombiaTime.getMonth() + 1).padStart(2, '0')
  const day = String(colombiaTime.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

/**
 * Check if current time in Colombia is within reservation hours
 * @param isVip - Whether user is VIP (VIP: 7:55AM-8PM, Regular: 8AM-5PM)
 * @returns [canReserve, errorMessage]
 */
export function canMakeReservationNow(isVip: boolean): [boolean, string] {
  const currentHour = getColombiaHour()
  const currentMinute = getColombiaMinute()

  if (isVip) {
    // VIP users: 7:55 AM - 8:00 PM (20:00)
    const isAfterStart = currentHour > 7 || (currentHour === 7 && currentMinute >= 55)
    const isBeforeEnd = currentHour < 20 || (currentHour === 20 && currentMinute === 0)

    if (isAfterStart && isBeforeEnd) {
      return [true, '']
    } else {
      if (!isAfterStart) {
        return [false, 'Las reservas están disponibles a partir de las 7:55 AM']
      } else {
        return [false, 'Las reservas están disponibles hasta las 8:00 PM']
      }
    }
  } else {
    // Regular users: 8 AM - 5 PM (17:00)
    if (currentHour >= 8 && currentHour <= 16) {
      return [true, '']
    } else {
      if (currentHour < 8) {
        return [false, 'Las reservas están disponibles a partir de las 8:00 AM']
      } else {
        return [false, 'Las reservas están disponibles hasta las 5:00 PM']
      }
    }
  }
}

/**
 * Format a date string in Colombian timezone
 */
export function formatColombiaDate(dateString: string): Date {
  // Ensure we're interpreting the date in Colombia timezone
  return new Date(dateString + 'T00:00:00-05:00')
}
