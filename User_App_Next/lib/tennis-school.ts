import type { MaintenanceSlot } from '@/types/database.types'

/**
 * Generate tennis school slots for a given date
 * Tennis school is on Saturdays and Sundays from 8:00 AM to 12:00 PM (hours 8-11)
 */
export function generateTennisSchoolSlots(date: string): MaintenanceSlot[] {
  const dateObj = new Date(date + 'T00:00:00')
  const dayOfWeek = dateObj.getDay() // 0 = Sunday, 6 = Saturday

  // Only generate for weekends
  if (dayOfWeek !== 0 && dayOfWeek !== 6) {
    return []
  }

  // Generate slots for hours 8, 9, 10, 11 (8:00 AM - 12:00 PM)
  const tennisSchoolHours = [8, 9, 10, 11]

  return tennisSchoolHours.map((hour) => ({
    id: `tennis-school-${date}-${hour}`,
    date,
    hour,
    reason: 'Escuela de Tenis',
    type: 'tennis_school',
    created_at: new Date().toISOString(),
  }))
}

/**
 * Check if a specific date/hour is tennis school time
 */
export function isTennisSchoolTime(date: string, hour: number): boolean {
  const dateObj = new Date(date + 'T00:00:00')
  const dayOfWeek = dateObj.getDay() // 0 = Sunday, 6 = Saturday

  const isWeekend = dayOfWeek === 0 || dayOfWeek === 6
  const isTennisSchoolHour = hour >= 8 && hour <= 11

  return isWeekend && isTennisSchoolHour
}
