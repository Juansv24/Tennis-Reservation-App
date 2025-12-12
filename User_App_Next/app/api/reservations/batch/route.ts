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
  const maxHour = profile.is_vip ? 20 : 16 // VIP: 8 PM, Regular: 4 PM (last hour to make reservation)

  if (currentHour < 8) {
    return NextResponse.json(
      { error: 'Las reservas están disponibles a partir de las 8:00 AM' },
      { status: 400 }
    )
  }

  if (currentHour > maxHour) {
    const maxTime = profile.is_vip ? '8:00 PM' : '5:00 PM'
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

    // RULE 1: Check if trying to book same hour on consecutive days
    if (date === today && userTomorrowReservations.includes(hour)) {
      const formattedHour = `${hour.toString().padStart(2, '0')}:00`
      return NextResponse.json(
        { error: `No puedes reservar a las ${formattedHour} hoy porque ya lo tienes reservado mañana.` },
        { status: 400 }
      )
    }
    if (date === tomorrow && userTodayReservations.includes(hour)) {
      const formattedHour = `${hour.toString().padStart(2, '0')}:00`
      return NextResponse.json(
        { error: `No puedes reservar a las ${formattedHour} mañana porque ya lo tienes reservado hoy.` },
        { status: 400 }
      )
    }

    // RULE 2: Check daily limit (max 2 hours per day)
    const userExistingHoursForDate = date === today ? userTodayReservations : userTomorrowReservations
    const newReservationsForDate = reservations.filter(r => r.date === date).length
    const totalHoursForDate = userExistingHoursForDate.length + newReservationsForDate

    if (totalHoursForDate > 2) {
      return NextResponse.json(
        { error: `Máximo 2 horas por día. Ya tienes ${userExistingHoursForDate.length} hora(s) reservada(s).` },
        { status: 400 }
      )
    }
  }

  // Create all reservations
  const reservationInserts = reservations.map(res => ({
    user_id: user.id,
    date: res.date,
    hour: res.hour,
  }))

  const { data: createdReservations, error: reservationError } = await supabase
    .from('reservations')
    .insert(reservationInserts)
    .select()

  // Handle unique constraint violation (slot already taken)
  if (reservationError?.code === '23505') {
    return NextResponse.json(
      { error: 'Uno o más slots ya están reservados' },
      { status: 409 }
    )
  }

  if (reservationError) {
    return NextResponse.json(
      { error: reservationError.message },
      { status: 500 }
    )
  }

  // Deduct credits - AFTER successful reservation creation
  const { error: updateError } = await supabase
    .from('users')
    .update({ credits: profile.credits - creditsNeeded })
    .eq('id', user.id)

  if (updateError) {
    // Rollback: delete the reservations we just created
    const ids = createdReservations?.map(r => r.id) || []
    if (ids.length > 0) {
      await supabase
        .from('reservations')
        .delete()
        .in('id', ids)
    }
    return NextResponse.json(
      { error: 'Error al actualizar créditos' },
      { status: 500 }
    )
  }

  const newCredits = profile.credits - creditsNeeded

  return NextResponse.json({
    success: true,
    reservations: createdReservations,
    credits_used: creditsNeeded,
    new_credits: newCredits,
  })
}
