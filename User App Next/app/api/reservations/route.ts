import { createClient } from '@/lib/supabase/server'
import { NextRequest, NextResponse } from 'next/server'

// GET /api/reservations?date=YYYY-MM-DD
export async function GET(request: NextRequest) {
  const supabase = createClient()
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
  const supabase = createClient()

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

  // Check credits (unless VIP)
  if (!profile.is_vip && profile.credits < 1) {
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
    return NextResponse.json(
      { error: 'Slot ya reservado' },
      { status: 409 }
    )
  }

  if (reservationError) {
    return NextResponse.json(
      { error: reservationError.message },
      { status: 500 }
    )
  }

  // Deduct credit (unless VIP)
  if (!profile.is_vip) {
    await supabase
      .from('users')
      .update({ credits: profile.credits - 1 })
      .eq('id', user.id)
  }

  return NextResponse.json({
    success: true,
    reservation,
    new_credits: profile.is_vip ? profile.credits : profile.credits - 1,
  })
}
