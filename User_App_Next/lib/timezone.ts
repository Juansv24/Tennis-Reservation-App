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
 * Get today's date in Colombian timezone (YYYY-MM-DD format)
 */
export function getColombiaToday(): string {
  const colombiaTime = getColombiaTime()
  return colombiaTime.toISOString().split('T')[0]
}

/**
 * Get tomorrow's date in Colombian timezone (YYYY-MM-DD format)
 */
export function getColombiaTomorrow(): string {
  const colombiaTime = getColombiaTime()
  colombiaTime.setDate(colombiaTime.getDate() + 1)
  return colombiaTime.toISOString().split('T')[0]
}

/**
 * Check if current time in Colombia is within reservation hours
 * @param isVip - Whether user is VIP (VIP: 8-20, Regular: 8-16)
 * @returns [canReserve, errorMessage]
 */
export function canMakeReservationNow(isVip: boolean): [boolean, string] {
  const currentHour = getColombiaHour()

  if (isVip) {
    // VIP users: 8 AM - 8 PM (20:00)
    if (currentHour >= 8 && currentHour <= 20) {
      return [true, '']
    } else {
      if (currentHour < 8) {
        return [false, 'Las reservas están disponibles a partir de las 8:00 AM']
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
