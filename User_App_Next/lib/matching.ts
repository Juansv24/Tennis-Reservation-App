// ABOUTME: Pure functions for computing partner suggestions from reservation history.
// ABOUTME: Uses level compatibility and day/hour overlap to rank and badge suggested partners.
import type { User, SuggestedPartner } from '@/types/database.types'

const CATEGORIA_RANK: Record<string, number> = {
  'Primera': 1, 'Segunda': 2, 'Tercera': 3, 'Cuarta': 4, 'Quinta': 5,
}

const DAYS_ES: Record<string, string> = {
  monday: 'lunes', tuesday: 'martes', wednesday: 'miércoles',
  thursday: 'jueves', friday: 'viernes', saturday: 'sábados', sunday: 'domingos',
}

function getDayOfWeek(dateStr: string): string {
  const d = new Date(dateStr + 'T12:00:00')
  const days = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
  return days[d.getDay()]
}

type DayHourPattern = Record<string, number[]>

export function buildDayHourPattern(
  reservations: Array<{ user_id: string; date: string; hour: number }>,
  userId: string
): DayHourPattern {
  const sets: Record<string, Set<number>> = {}
  for (const r of reservations) {
    if (r.user_id !== userId) continue
    const day = getDayOfWeek(r.date)
    if (!sets[day]) sets[day] = new Set()
    sets[day].add(r.hour)
  }
  return Object.fromEntries(
    Object.entries(sets).map(([day, hours]) => [day, [...hours].sort((a, b) => a - b)])
  )
}

export function findOverlapPairs(
  patternA: DayHourPattern,
  patternB: DayHourPattern
): Array<{ day: string; hour: number }> {
  const pairs: Array<{ day: string; hour: number }> = []
  for (const day of Object.keys(patternA)) {
    if (!patternB[day]) continue
    const setB = new Set(patternB[day])
    for (const hour of patternA[day]) {
      if (setB.has(hour)) pairs.push({ day, hour })
    }
  }
  return pairs
}

function timeBucket(hour: number): string {
  if (hour <= 11) return 'la mañana'
  if (hour <= 17) return 'la tarde'
  return 'la noche'
}

export function formatOverlapMessage(pairs: Array<{ day: string; hour: number }>): string {
  if (pairs.length === 0) return ''
  const grouped: Record<string, Set<string>> = {}
  for (const { day, hour } of pairs) {
    if (!grouped[day]) grouped[day] = new Set()
    grouped[day].add(timeBucket(hour))
  }
  const parts = Object.entries(grouped).map(([day, buckets]) => {
    const dayES = DAYS_ES[day] || day
    const arr = [...buckets]
    return arr.length === 1
      ? `los ${dayES} en ${arr[0]}`
      : `los ${dayES} en ${arr.join(' y en ')}`
  })
  if (parts.length === 1) return `Ambos juegan usualmente ${parts[0]}`
  const last = parts[parts.length - 1]
  return `Ambos juegan usualmente ${parts.slice(0, -1).join(', ')} y ${last}`
}

export function isLevelMatch(
  a: Pick<User, 'level_tier' | 'categoria'>,
  b: Pick<User, 'level_tier' | 'categoria'>
): boolean {
  if (a.level_tier && b.level_tier && a.level_tier === b.level_tier) return true
  const rankA = a.categoria ? (CATEGORIA_RANK[a.categoria] ?? null) : null
  const rankB = b.categoria ? (CATEGORIA_RANK[b.categoria] ?? null) : null
  if (rankA !== null && rankB !== null) return Math.abs(rankA - rankB) <= 1
  return false
}

export function computeSuggestions(
  currentUser: Pick<User, 'id' | 'level_tier' | 'categoria'>,
  allProfiles: Array<Pick<User, 'id' | 'full_name' | 'level_tier' | 'categoria'>>,
  recentReservations: Array<{ user_id: string; date: string; hour: number }>
): SuggestedPartner[] {
  const activeUserIds = new Set(recentReservations.map(r => r.user_id))
  const currentPattern = buildDayHourPattern(recentReservations, currentUser.id)
  const suggestions: SuggestedPartner[] = []

  for (const other of allProfiles) {
    if (other.id === currentUser.id) continue
    if (!activeUserIds.has(other.id)) continue
    if (!isLevelMatch(currentUser, other)) continue
    const otherPattern = buildDayHourPattern(recentReservations, other.id)
    const overlapPairs = findOverlapPairs(currentPattern, otherPattern)
    const hasOverlap = overlapPairs.length >= 2
    suggestions.push({
      user: { id: other.id, full_name: other.full_name, level_tier: other.level_tier, categoria: other.categoria },
      badge: hasOverlap ? 'nivel+horario' : 'solo-nivel',
      overlapMessage: hasOverlap ? formatOverlapMessage(overlapPairs) : null,
    })
  }

  return suggestions.sort((a, b) => {
    if (a.badge === 'nivel+horario' && b.badge !== 'nivel+horario') return -1
    if (a.badge !== 'nivel+horario' && b.badge === 'nivel+horario') return 1
    return 0
  })
}
