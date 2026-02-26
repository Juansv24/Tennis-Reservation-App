// ABOUTME: Unit tests for the partner matching algorithm.
// ABOUTME: Tests level matching, schedule overlap, message formatting, and sorting.
import {
  isLevelMatch,
  buildDayHourPattern,
  findOverlapPairs,
  formatOverlapMessage,
  computeSuggestions,
} from '@/lib/matching'

const makeUser = (overrides: Partial<{ id: string; full_name: string; level_tier: string | null; categoria: string | null }> = {}) => ({
  id: 'user-1',
  full_name: 'Test User',
  level_tier: 'Intermedio' as string | null,
  categoria: 'Segunda' as string | null,
  ...overrides,
})

const makeReservation = (user_id: string, date: string, hour: number) => ({ user_id, date, hour })

// A Monday date (2025-01-06 is a Monday)
const MON = '2025-01-06'
const TUE = '2025-01-07'
const WED = '2025-01-08'

describe('isLevelMatch', () => {
  it('matches users with same level_tier', () => {
    expect(isLevelMatch(makeUser({ level_tier: 'Intermedio', categoria: null }), makeUser({ level_tier: 'Intermedio', categoria: null }))).toBe(true)
  })

  it('does not match users with different level_tier and no categoria', () => {
    expect(isLevelMatch(makeUser({ level_tier: 'Principiante', categoria: null }), makeUser({ level_tier: 'Avanzado', categoria: null }))).toBe(false)
  })

  it('matches users with categoria rank diff of 1', () => {
    expect(isLevelMatch(makeUser({ level_tier: null, categoria: 'Segunda' }), makeUser({ level_tier: null, categoria: 'Tercera' }))).toBe(true)
  })

  it('does not match users with categoria rank diff of 2', () => {
    expect(isLevelMatch(makeUser({ level_tier: null, categoria: 'Primera' }), makeUser({ level_tier: null, categoria: 'Tercera' }))).toBe(false)
  })

  it('returns false when both categorias are null and level_tiers differ', () => {
    expect(isLevelMatch(makeUser({ level_tier: 'Principiante', categoria: null }), makeUser({ level_tier: 'Intermedio', categoria: null }))).toBe(false)
  })

  it('matches when same level_tier even if categorias differ widely', () => {
    expect(isLevelMatch(makeUser({ level_tier: 'Intermedio', categoria: 'Primera' }), makeUser({ level_tier: 'Intermedio', categoria: 'Quinta' }))).toBe(true)
  })

  it('excludes No sé from rank comparison', () => {
    // "No sé" has no rank, so rank comparison cannot happen; falls back to level_tier
    expect(isLevelMatch(makeUser({ level_tier: 'Intermedio', categoria: 'No sé' }), makeUser({ level_tier: 'Principiante', categoria: 'Segunda' }))).toBe(false)
  })
})

describe('buildDayHourPattern', () => {
  it('groups hours by day of week for the given user', () => {
    const reservations = [
      makeReservation('user-1', MON, 8),
      makeReservation('user-1', MON, 9),
      makeReservation('user-1', TUE, 14),
      makeReservation('user-2', MON, 8), // different user, excluded
    ]
    const pattern = buildDayHourPattern(reservations, 'user-1')
    expect(pattern.monday).toEqual([8, 9])
    expect(pattern.tuesday).toEqual([14])
    expect(pattern.monday).not.toContain(undefined)
  })

  it('returns empty object when user has no reservations', () => {
    expect(buildDayHourPattern([], 'user-1')).toEqual({})
  })
})

describe('findOverlapPairs', () => {
  it('returns overlapping (day, hour) pairs', () => {
    const patternA = { monday: [8, 9, 14], wednesday: [10] }
    const patternB = { monday: [8, 14, 15], thursday: [8] }
    const pairs = findOverlapPairs(patternA, patternB)
    expect(pairs).toEqual(expect.arrayContaining([
      { day: 'monday', hour: 8 },
      { day: 'monday', hour: 14 },
    ]))
    expect(pairs).toHaveLength(2)
  })

  it('returns empty when no overlap', () => {
    const patternA = { monday: [8] }
    const patternB = { tuesday: [8] }
    expect(findOverlapPairs(patternA, patternB)).toHaveLength(0)
  })
})

describe('formatOverlapMessage', () => {
  it('formats a single day single bucket', () => {
    const msg = formatOverlapMessage([{ day: 'monday', hour: 8 }, { day: 'monday', hour: 9 }])
    expect(msg).toBe('Ambos juegan usualmente los lunes en la mañana')
  })

  it('formats a single day with two buckets', () => {
    const msg = formatOverlapMessage([{ day: 'monday', hour: 8 }, { day: 'monday', hour: 14 }])
    expect(msg).toBe('Ambos juegan usualmente los lunes en la mañana y en la tarde')
  })

  it('formats two days', () => {
    const msg = formatOverlapMessage([{ day: 'monday', hour: 8 }, { day: 'wednesday', hour: 14 }])
    expect(msg).toBe('Ambos juegan usualmente los lunes en la mañana y los miércoles en la tarde')
  })

  it('returns empty string for empty pairs', () => {
    expect(formatOverlapMessage([])).toBe('')
  })

  it('formats a noche hour correctly', () => {
    const msg = formatOverlapMessage([{ day: 'friday', hour: 19 }, { day: 'friday', hour: 20 }])
    expect(msg).toBe('Ambos juegan usualmente los viernes en la noche')
  })
})

describe('computeSuggestions', () => {
  const currentUser = makeUser({ id: 'me', level_tier: 'Intermedio', categoria: 'Segunda' })

  it('excludes the current user from suggestions', () => {
    const profiles = [makeUser({ id: 'me', level_tier: 'Intermedio', categoria: 'Segunda' })]
    const reservations = [makeReservation('me', MON, 8)]
    expect(computeSuggestions(currentUser, profiles, reservations)).toHaveLength(0)
  })

  it('excludes inactive users (no reservations in input)', () => {
    const profiles = [makeUser({ id: 'other', level_tier: 'Intermedio', categoria: 'Segunda' })]
    const reservations = [makeReservation('me', MON, 8)] // other has no reservations
    expect(computeSuggestions(currentUser, profiles, reservations)).toHaveLength(0)
  })

  it('excludes users with no level match', () => {
    const profiles = [makeUser({ id: 'other', level_tier: 'Principiante', categoria: 'Quinta' })]
    const reservations = [
      makeReservation('me', MON, 8),
      makeReservation('other', MON, 8),
    ]
    expect(computeSuggestions(currentUser, profiles, reservations)).toHaveLength(0)
  })

  it('assigns nivel+horario badge when overlap >= 2', () => {
    const profiles = [makeUser({ id: 'other', level_tier: 'Intermedio', categoria: 'Segunda' })]
    const reservations = [
      makeReservation('me', MON, 8),
      makeReservation('me', TUE, 14),
      makeReservation('other', MON, 8),
      makeReservation('other', TUE, 14),
    ]
    const result = computeSuggestions(currentUser, profiles, reservations)
    expect(result[0].badge).toBe('nivel+horario')
    expect(result[0].overlapMessage).not.toBeNull()
  })

  it('assigns solo-nivel badge when overlap < 2', () => {
    const profiles = [makeUser({ id: 'other', level_tier: 'Intermedio', categoria: 'Segunda' })]
    const reservations = [
      makeReservation('me', MON, 8),
      makeReservation('other', TUE, 14), // different slots — no overlap
    ]
    const result = computeSuggestions(currentUser, profiles, reservations)
    expect(result[0].badge).toBe('solo-nivel')
    expect(result[0].overlapMessage).toBeNull()
  })

  it('sorts nivel+horario matches before solo-nivel', () => {
    const profiles = [
      makeUser({ id: 'solo', level_tier: 'Intermedio', categoria: 'Segunda' }),
      makeUser({ id: 'overlap', level_tier: 'Intermedio', categoria: 'Segunda' }),
    ]
    const reservations = [
      makeReservation('me', MON, 8),
      makeReservation('me', TUE, 14),
      makeReservation('solo', WED, 10),    // active but no overlap with me
      makeReservation('overlap', MON, 8),
      makeReservation('overlap', TUE, 14),
    ]
    const result = computeSuggestions(currentUser, profiles, reservations)
    expect(result[0].badge).toBe('nivel+horario')
    expect(result[1].badge).toBe('solo-nivel')
  })
})
