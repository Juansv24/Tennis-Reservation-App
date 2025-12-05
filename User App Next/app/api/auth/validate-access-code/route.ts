import { createClient } from '@/lib/supabase/server'
import { NextRequest, NextResponse } from 'next/server'

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
  const { code } = await request.json()

  if (!code) {
    return NextResponse.json(
      { error: 'Código requerido' },
      { status: 400 }
    )
  }

  // Validate code
  const { data: accessCode } = await supabase
    .from('access_codes')
    .select('*')
    .eq('code', code.toUpperCase())
    .eq('is_active', true)
    .single()

  if (!accessCode) {
    return NextResponse.json(
      { error: 'Código inválido o inactivo' },
      { status: 400 }
    )
  }

  // Update user profile
  const { error: updateError } = await supabase
    .from('users')
    .update({ first_login_completed: true })
    .eq('id', user.id)

  if (updateError) {
    return NextResponse.json(
      { error: 'Error al actualizar perfil' },
      { status: 500 }
    )
  }

  return NextResponse.json({ success: true })
}
