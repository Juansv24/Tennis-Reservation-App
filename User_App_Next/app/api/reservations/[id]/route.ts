import { createClient } from '@/lib/supabase/server'
import { NextRequest, NextResponse } from 'next/server'

interface RouteContext {
  params: Promise<{
    id: string
  }>
}

// DELETE /api/reservations/[id]
export async function DELETE(
  request: NextRequest,
  context: RouteContext
) {
  const supabase = await createClient()

  // Check authentication
  const { data: { user }, error: authError } = await supabase.auth.getUser()
  if (authError || !user) {
    return NextResponse.json(
      { error: 'No autenticado' },
      { status: 401 }
    )
  }

  // Get the reservation ID from params
  const { id } = await context.params

  // Get the reservation to verify ownership and get details for logging
  const { data: reservation, error: fetchError } = await supabase
    .from('reservations')
    .select('id, user_id, date, hour')
    .eq('id', id)
    .single()

  if (fetchError || !reservation) {
    return NextResponse.json(
      { error: 'Reserva no encontrada' },
      { status: 404 }
    )
  }

  // Verify ownership
  if (reservation.user_id !== user.id) {
    return NextResponse.json(
      { error: 'No tienes permiso para eliminar esta reserva' },
      { status: 403 }
    )
  }

  // Get user profile to check VIP status
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

  // Delete the reservation
  const { error: deleteError } = await supabase
    .from('reservations')
    .delete()
    .eq('id', id)

  if (deleteError) {
    return NextResponse.json(
      { error: deleteError.message },
      { status: 500 }
    )
  }

  // Refund credit (unless VIP)
  let newCredits = profile.credits
  let creditRefunded = false
  if (!profile.is_vip) {
    newCredits = profile.credits + 1
    creditRefunded = true
    await supabase
      .from('users')
      .update({ credits: newCredits })
      .eq('id', user.id)
  }

  return NextResponse.json({
    success: true,
    new_credits: newCredits,
  })
}
