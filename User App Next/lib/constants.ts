// US Open Color Theme
export const COLORS = {
  usOpenBlue: '#001854',
  usOpenLightBlue: '#2478CC',
  usOpenYellow: '#FFD400',
  availableGreen: '#4CAF50',
  takenGray: '#9E9E9E',
  maintenanceOrange: '#FF9800',
} as const

// Court hours (6 AM - 9 PM)
export const COURT_HOURS = Array.from({ length: 16 }, (_, i) => i + 6)

// Format hour for display (e.g., 14 -> "14:00")
export function formatHour(hour: number): string {
  return `${hour.toString().padStart(2, '0')}:00`
}

// Get today's date in YYYY-MM-DD format
export function getTodayDate(): string {
  return new Date().toISOString().split('T')[0]
}

// Get tomorrow's date in YYYY-MM-DD format
export function getTomorrowDate(): string {
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  return tomorrow.toISOString().split('T')[0]
}

// Format date for display (e.g., "Viernes, 7 de Diciembre")
export function formatDateFull(dateString: string): string {
  const date = new Date(dateString + 'T00:00:00')
  return date.toLocaleDateString('es-ES', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}
