// Quick timezone test - Run this to verify Colombian time calculations
const COLOMBIA_OFFSET_HOURS = -5

function getColombiaTime() {
  const now = new Date()
  const utc = now.getTime() + (now.getTimezoneOffset() * 60000)
  const colombiaTime = new Date(utc + (3600000 * COLOMBIA_OFFSET_HOURS))
  return colombiaTime
}

function getColombiaToday() {
  const colombiaTime = getColombiaTime()
  // Extract date components directly (don't use toISOString which converts back to UTC!)
  const year = colombiaTime.getFullYear()
  const month = String(colombiaTime.getMonth() + 1).padStart(2, '0')
  const day = String(colombiaTime.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function getColombiaTomorrow() {
  const colombiaTime = getColombiaTime()
  colombiaTime.setDate(colombiaTime.getDate() + 1)
  // Extract date components directly (don't use toISOString which converts back to UTC!)
  const year = colombiaTime.getFullYear()
  const month = String(colombiaTime.getMonth() + 1).padStart(2, '0')
  const day = String(colombiaTime.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

console.log('=== TIMEZONE DIAGNOSTIC ===')
console.log('')
console.log('Your Local Machine:')
const local = new Date()
console.log('  Time:', local.toString())
console.log('  Timezone offset:', local.getTimezoneOffset(), 'minutes')
console.log('  ISO:', local.toISOString())
console.log('')

console.log('Colombian Time Calculation:')
const colombia = getColombiaTime()
console.log('  Time:', colombia.toString())
console.log('  ISO:', colombia.toISOString())
console.log('  Hour:', colombia.getHours())
console.log('')

console.log('Dates:')
console.log('  Today (Colombia):', getColombiaToday())
console.log('  Tomorrow (Colombia):', getColombiaTomorrow())
console.log('')

console.log('Expected for Dec 11, 2025 at ~8 PM Colombia:')
console.log('  Today should be: 2025-12-11')
console.log('  Tomorrow should be: 2025-12-12')
console.log('  Hour should be: ~20 (8 PM)')
