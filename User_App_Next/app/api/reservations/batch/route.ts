import { createClient } from '@/lib/supabase/server'
import { NextRequest, NextResponse } from 'next/server'
import { getColombiaHour, getColombiaToday, getColombiaTomorrow } from '@/lib/timezone'

// POST /api/reservations/batch
export async function POST(request: NextRequest) {
  const supabase = await createClient()

  // Check authentication
  const { data: { user }, error: authError } = await supabase.auth.getUser()
  if (authError || !user) {
    return NextResponse.json(
      { error: 'No autenticado' },
      { status: 401 }
    )
  }

  // Parse request - expecting array of {date, hour} objects
  const { reservations } = await request.json()

  if (!Array.isArray(reservations) || reservations.length === 0) {
    return NextResponse.json(
      { error: 'Se requiere al menos una reserva' },
      { status: 400 }
    )
  }

  // RULE 2: Validate single day selection - all reservations must be for the same date
  const uniqueDates = [...new Set(reservations.map(r => r.date))]
  if (uniqueDates.length > 1) {
    return NextResponse.json(
      { error: 'Solo puedes hacer reservas para un día a la vez. Por favor selecciona horas del mismo día.' },
      { status: 400 }
    )
  }

  // RULE 1: Validate max 2 hours and must be consecutive
  if (reservations.length > 2) {
    return NextResponse.json(
      { error: 'Máximo 2 horas por día.' },
      { status: 400 }
    )
  }

  // If 2 hours selected, they must be consecutive
  if (reservations.length === 2) {
    const hours = reservations.map(r => r.hour).sort((a, b) => a - b)
    if (hours[1] - hours[0] !== 1) {
      return NextResponse.json(
        { error: 'Las 2 horas reservadas deben ser consecutivas (una después de la otra).' },
        { status: 400 }
      )
    }
  }

  // Get user profile
  const { data: profile } = await supabase
    .from('users')
    .select('credits, is_vip')
    .eq('id', user.id)
    .single()

  if (!profile) {
    return NextResponse.json(
      { error: 'Perfil no encontrado' },
      { status: 404 }
    )
  }

  // Calculate credits needed (1 credit per hour for all users)
  const creditsNeeded = reservations.length

  // Check credits
  if (profile.credits < creditsNeeded) {
    return NextResponse.json(
      { error: `Sin créditos suficientes. Necesitas ${creditsNeeded}, tienes ${profile.credits}` },
      { status: 400 }
    )
  }

  // Check time-based reservation restrictions (Colombian timezone)
  const currentHour = getColombiaHour()
  const maxHour = profile.is_vip ? 23 : 16 // VIP: 11 PM, Regular: 4 PM (last hour to make reservation)

  if (currentHour < 8) {
    return NextResponse.json(
      { error: 'Las reservas están disponibles a partir de las 8:00 AM' },
      { status: 400 }
    )
  }

  if (currentHour > maxHour) {
    const maxTime = profile.is_vip ? '11:00 PM' : '5:00 PM'
    return NextResponse.json(
      { error: `Las reservas están disponibles hasta las ${maxTime}` },
      { status: 400 }
    )
  }

  // Get today and tomorrow dates for validation (Colombian timezone)
  const today = getColombiaToday()
  const tomorrow = getColombiaTomorrow()

  // Get user's existing reservations for today and tomorrow
  const { data: userReservations } = await supabase
    .from('reservations')
    .select('date, hour')
    .eq('user_id', user.id)
    .in('date', [today, tomorrow])

  const userTodayReservations = userReservations?.filter(r => r.date === today).map(r => r.hour) || []
  const userTomorrowReservations = userReservations?.filter(r => r.date === tomorrow).map(r => r.hour) || []

  // Validate each reservation
  for (const res of reservations) {
    const { date, hour } = res

    // RULE 3: Check if trying to book same hour on consecutive days
    if (date === today && userTomorrowReservations.includes(hour)) {
      const formattedHour = `${hour.toString().padStart(2, '0')}:00`
      return NextResponse.json(
        { error: `No puedes reservar a las ${formattedHour} hoy porque ya lo tienes reservado mañana. No se permite reservar el mismo horario en días consecutivos.` },
        { status: 400 }
      )
    }
    if (date === tomorrow && userTodayReservations.includes(hour)) {
      const formattedHour = `${hour.toString().padStart(2, '0')}:00`
      return NextResponse.json(
        { error: `No puedes reservar a las ${formattedHour} mañana porque ya lo tienes reservado hoy. No se permite reservar el mismo horario en días consecutivos.` },
        { status: 400 }
      )
    }

    // RULE 1: Check daily limit (max 2 hours per day)
    const userExistingHoursForDate = date === today ? userTodayReservations : userTomorrowReservations
    const newReservationsForDate = reservations.filter(r => r.date === date).length
    const totalHoursForDate = userExistingHoursForDate.length + newReservationsForDate

    if (totalHoursForDate > 2) {
      return NextResponse.json(
        { error: 'Solo puedes reservar máximo 2 horas por día.' },
        { status: 400 }
      )
    }

    // RULE 1b: If user has existing reservations for this day, all hours (existing + new) must be consecutive
    if (userExistingHoursForDate.length > 0) {
      const newHoursForDate = reservations.filter(r => r.date === date).map(r => r.hour)
      const allHoursForDay = [...userExistingHoursForDate, ...newHoursForDate].sort((a, b) => a - b)
      // Check if all hours are consecutive
      for (let i = 1; i < allHoursForDay.length; i++) {
        if (allHoursForDay[i] - allHoursForDay[i - 1] !== 1) {
          return NextResponse.json(
            { error: 'Las 2 horas reservadas deben ser consecutivas (una después de la otra).' },
            { status: 400 }
          )
        }
      }
    }
  }

  // DEBUG: Log what we're sending to the database
  console.log('=== RPC Call Debug ===')
  console.log('user.id:', user.id)
  console.log('reservations:', JSON.stringify(reservations, null, 2))
  console.log('reservations type:', typeof reservations)
  console.log('reservations isArray:', Array.isArray(reservations))
  console.log('creditsNeeded:', creditsNeeded)
  console.log('=====================')

  // Use atomic database function to create reservations and deduct credits
  // This eliminates race conditions - the database guarantees atomicity
  const { data: result, error: rpcError } = await supabase
    .rpc('create_batch_reservations', {
      p_user_id: user.id,
      p_reservations: reservations,
      p_credits_needed: creditsNeeded
    })
    .single() as { data: { success: boolean; error?: string; new_credits?: number; reservation_ids?: string[]; slot_taken?: { date: string; hour: number } } | null; error: any }

  // DEBUG: Log the result
  console.log('=== RPC Result Debug ===')
  console.log('result:', result)
  console.log('rpcError:', rpcError)
  console.log('========================')

  if (rpcError) {
    console.error('RPC error:', rpcError)
    return NextResponse.json(
      { error: `Error del sistema: ${rpcError.message}` },
      { status: 500 }
    )
  }

  if (!result) {
    return NextResponse.json(
      { error: 'Error del sistema: No response from database' },
      { status: 500 }
    )
  }

  // Check if the atomic operation failed
  if (!result.success) {
    // Check if it's a slot taken error (race condition)
    if (result.slot_taken) {
      return NextResponse.json(
        { error: result.error || 'Uno o más slots ya están reservados' },
        { status: 409 }
      )
    }

    // Other validation errors (credits, daily limit, etc.)
    return NextResponse.json(
      { error: result.error || 'Error al crear reserva' },
      { status: 400 }
    )
  }

  // Fetch the created reservations for the response
  const { data: createdReservations } = await supabase
    .from('reservations')
    .select('*')
    .in('id', result.reservation_ids || [])

  return NextResponse.json({
    success: true,
    reservations: createdReservations || [],
    credits_used: creditsNeeded,
    new_credits: result.new_credits,
  })
}
