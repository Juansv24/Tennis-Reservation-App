import { createClient } from '@/lib/supabase/server'
import { NextRequest, NextResponse } from 'next/server'
import { getColombiaHour, getColombiaToday, getColombiaTomorrow } from '@/lib/timezone'
import { logActivity } from '@/lib/activity-logger'

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

  // CHECK FOR TENNIS SCHOOL FIRST - MUST BE BEFORE ALL OTHER VALIDATIONS
  const { data: systemSettings } = await supabase
    .from('system_settings')
    .select('tennis_school_enabled')
    .single()

  if (systemSettings?.tennis_school_enabled) {
    for (const res of reservations) {
      const { date, hour } = res
      const dayOfWeek = new Date(date).getDay() // 0 = Sunday, 6 = Saturday
      const isTennisSchoolDay = dayOfWeek === 0 || dayOfWeek === 6 // Saturday or Sunday
      const isTennisSchoolHour = hour >= 8 && hour <= 11 // 8:00-11:00

      if (isTennisSchoolDay && isTennisSchoolHour) {
        const formattedHour = `${hour.toString().padStart(2, '0')}:00`
        return NextResponse.json(
          { error: `No se puede reservar a las ${formattedHour}: Escuela de Tenis (Sábados y Domingos 8:00-12:00). Recargue su navegador para ver la información más actualizada.` },
          { status: 400 }
        )
      }
    }
  }

  // CHECK FOR BLOCKED SLOTS (maintenance) - BEFORE ALL OTHER VALIDATIONS
  for (const res of reservations) {
    const { date, hour } = res

    const { data: blockedSlot, error: blockedError } = await supabase
      .from('blocked_slots')
      .select('id, maintenance_type, reason')
      .eq('date', date)
      .eq('hour', hour)
      .maybeSingle()

    // If there's an error checking blocked slots, fail the request
    if (blockedError) {
      console.error('Error checking blocked slots:', blockedError)
      return NextResponse.json(
        { error: `Error verificando disponibilidad: ${blockedError.message}` },
        { status: 500 }
      )
    }

    // If slot is blocked by maintenance, reject immediately (before deducting credits)
    if (blockedSlot) {
      const formattedHour = `${hour.toString().padStart(2, '0')}:00`
      return NextResponse.json(
        { error: `No se puede reservar a las ${formattedHour}: Cancha en mantenimiento. Recargue su navegador para ver la información más actualizada.` },
        { status: 400 }
      )
    }
  }

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

  // Use single-payload RPC approach to avoid JSONB serialization issues
  // All parameters wrapped in one JSONB object
  const { data: result, error: rpcError } = await supabase
    .rpc('confirm_batch_reservation', {
      payload: {
        user_id: user.id,
        credits_needed: creditsNeeded,
        slots: reservations.map(r => ({
          res_date: r.date,
          res_hour: r.hour
        }))
      }
    })
    .single() as { data: { success: boolean; error_code?: string; error?: string; new_credits?: number; reservation_ids?: string[] } | null; error: any }

  // Handle RPC errors (system-level failures)
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

  // Handle business logic failures (returned by function)
  if (!result.success) {
    switch (result.error_code) {
      case 'SLOT_ALREADY_TAKEN':
        return NextResponse.json(
          { error: result.error || 'Uno o más horarios ya están reservados' },
          { status: 409 }
        )
      case 'INSUFFICIENT_CREDITS':
        return NextResponse.json(
          { error: result.error || 'Sin créditos suficientes' },
          { status: 400 }
        )
      case 'DAILY_LIMIT_EXCEEDED':
        return NextResponse.json(
          { error: result.error || 'Máximo 2 horas por día' },
          { status: 400 }
        )
      case 'NON_CONSECUTIVE_HOURS':
        return NextResponse.json(
          { error: result.error || 'Las 2 horas reservadas deben ser consecutivas' },
          { status: 400 }
        )
      case 'CONSECUTIVE_DAY_SAME_HOUR':
        return NextResponse.json(
          { error: result.error || 'No puedes reservar el mismo horario en días consecutivos' },
          { status: 400 }
        )
      case 'MULTIPLE_DATES':
        return NextResponse.json(
          { error: result.error || 'Solo puedes hacer reservas para un día a la vez' },
          { status: 400 }
        )
      case 'TOO_MANY_SLOTS':
        return NextResponse.json(
          { error: result.error || 'Máximo 2 horas por reserva' },
          { status: 400 }
        )
      case 'UNAUTHORIZED':
        return NextResponse.json(
          { error: result.error || 'No autorizado' },
          { status: 403 }
        )
      default:
        return NextResponse.json(
          { error: result.error || 'Error al crear reserva' },
          { status: 400 }
        )
    }
  }

  // Success! Fetch the created reservations for the response
  const { data: createdReservations } = await supabase
    .from('reservations')
    .select('*')
    .in('id', result.reservation_ids || [])

  // Log activity - batch reservation created successfully
  const hours = reservations.map(r => r.hour).sort((a, b) => a - b)
  const hoursStr = hours.map(h => `${h.toString().padStart(2, '0')}:00`).join(', ')
  await logActivity(
    supabase,
    user.id,
    'reservation_create',
    `Reserved ${reservations[0].date} at ${hoursStr}`,
    {
      date: reservations[0].date,
      hours,
      reservation_ids: result.reservation_ids,
      credits_used: creditsNeeded,
      new_credits: result.new_credits,
      reservation_count: reservations.length
    }
  )

  return NextResponse.json({
    success: true,
    reservations: createdReservations || [],
    credits_used: creditsNeeded,
    new_credits: result.new_credits,
  })
}
