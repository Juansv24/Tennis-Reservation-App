import { createClient } from '@/lib/supabase/server'
import { NextRequest, NextResponse } from 'next/server'
import { getColombiaHour, getColombiaToday, getColombiaTomorrow } from '@/lib/timezone'

// GET /api/reservations?date=YYYY-MM-DD
export async function GET(request: NextRequest) {
  const supabase = await createClient()
  const { searchParams } = new URL(request.url)
  const date = searchParams.get('date')

  if (!date) {
    return NextResponse.json(
      { error: 'Date parameter required' },
      { status: 400 }
    )
  }

  const { data: reservations, error } = await supabase
    .from('reservations')
    .select(`
      id,
      user_id,
      date,
      hour,
      created_at,
      users (full_name)
    `)
    .eq('date', date)
    .order('hour')

  if (error) {
    return NextResponse.json(
      { error: error.message },
      { status: 500 }
    )
  }

  return NextResponse.json({ reservations })
}

// POST /api/reservations
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

  // Parse request
  const { date, hour } = await request.json()

  if (!date || hour === undefined) {
    return NextResponse.json(
      { error: 'Fecha y hora requeridas' },
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

  // Check credits
  if (profile.credits < 1) {
    return NextResponse.json(
      { error: 'Sin créditos suficientes' },
      { status: 400 }
    )
  }

  // Check time-based reservation restrictions (Colombian timezone)
  const currentHour = getColombiaHour()
  const maxHour = profile.is_vip ? 20 : 16 // VIP: 8 PM, Regular: 4 PM

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

  // RULE 1: Check if trying to book same hour on consecutive days
  if (date === today && userTomorrowReservations.includes(hour)) {
    const formattedHour = `${hour.toString().padStart(2, '0')}:00`
    return NextResponse.json(
      { error: `No puedes reservar a las ${formattedHour} hoy porque ya lo tienes reservado mañana. No se permite reservar el mismo horario dos días seguidos.` },
      { status: 400 }
    )
  }
  if (date === tomorrow && userTodayReservations.includes(hour)) {
    const formattedHour = `${hour.toString().padStart(2, '0')}:00`
    return NextResponse.json(
      { error: `No puedes reservar a las ${formattedHour} mañana porque ya lo tienes reservado hoy. No se permite reservar el mismo horario dos días seguidos.` },
      { status: 400 }
    )
  }

  // RULE 2: Check daily limit (max 2 hours per day)
  const userExistingHoursForDate = date === today ? userTodayReservations : userTomorrowReservations
  if (userExistingHoursForDate.length >= 2) {
    return NextResponse.json(
      { error: `Máximo 2 horas por día. Ya tienes ${userExistingHoursForDate.length} hora(s) reservada(s) para este día.` },
      { status: 400 }
    )
  }

  // Atomically deduct credit BEFORE creating reservation (prevents race condition)
  const { data: creditResult, error: creditError } = await supabase
    .rpc('deduct_user_credit', { user_id_param: user.id })
    .single() as { data: { new_credits: number; success: boolean } | null; error: any }

  if (creditError || !creditResult) {
    console.error('Credit deduction error:', creditError)
    return NextResponse.json(
      { error: `Error al procesar créditos: ${creditError?.message || 'Función no encontrada'}` },
      { status: 500 }
    )
  }

  if (!creditResult.success) {
    return NextResponse.json(
      { error: 'Sin créditos suficientes' },
      { status: 400 }
    )
  }

  // Create reservation
  const { data: reservation, error: reservationError } = await supabase
    .from('reservations')
    .insert({
      user_id: user.id,
      date,
      hour,
    })
    .select()
    .single()

  // Handle unique constraint violation (slot already taken)
  if (reservationError?.code === '23505') {
    // Rollback: refund the credit we just deducted
    await supabase
      .from('users')
      .update({ credits: creditResult.new_credits + 1 })
      .eq('id', user.id)
    return NextResponse.json(
      { error: 'Slot ya reservado' },
      { status: 409 }
    )
  }

  if (reservationError) {
    // Rollback: refund the credit we just deducted
    await supabase
      .from('users')
      .update({ credits: creditResult.new_credits + 1 })
      .eq('id', user.id)
    return NextResponse.json(
      { error: reservationError.message },
      { status: 500 }
    )
  }

  return NextResponse.json({
    success: true,
    reservation,
    new_credits: creditResult.new_credits,
  })
}
