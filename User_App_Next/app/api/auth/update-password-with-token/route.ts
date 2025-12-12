import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'
import { getColombiaTimeServer } from '@/lib/timezone-server'

export async function POST(request: NextRequest) {
  try {
    const { token, password } = await request.json()

    // Validate inputs
    if (!token || !password) {
      return NextResponse.json({ error: 'Datos requeridos faltantes' }, { status: 400 })
    }

    if (password.length < 6) {
      return NextResponse.json({ error: 'Contraseña muy corta' }, { status: 400 })
    }

    // Create Supabase admin client
    const supabase = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.SUPABASE_SERVICE_ROLE_KEY!,
      {
        auth: {
          autoRefreshToken: false,
          persistSession: false
        }
      }
    )

    // Look up token in database
    const { data: tokenData, error: tokenError } = await supabase
      .from('password_reset_tokens')
      .select('*')
      .eq('token', token)
      .is('used_at', null)
      .single()

    if (tokenError || !tokenData) {
      return NextResponse.json({ error: 'Token no válido' }, { status: 404 })
    }

    // Check if token is expired (using Colombian timezone)
    const now = getColombiaTimeServer()
    const expiresAt = new Date(tokenData.expires_at)
    if (now > expiresAt) {
      return NextResponse.json({ error: 'Token expirado' }, { status: 410 })
    }

    // Mark token as used
    await supabase
      .from('password_reset_tokens')
      .update({ used_at: now.toISOString() })
      .eq('token', token)

    // Update user's password using admin API
    const { error: updateError } = await supabase.auth.admin.updateUserById(
      tokenData.user_id,
      { password }
    )

    if (updateError) {
      console.error('Error updating password:', updateError)
      return NextResponse.json({ error: 'Error al actualizar contraseña' }, { status: 500 })
    }

    return NextResponse.json({ success: true, message: 'Contraseña actualizada exitosamente' })
  } catch (error) {
    console.error('Error updating password with token:', error)
    return NextResponse.json({ error: 'Error al procesar solicitud' }, { status: 500 })
  }
}
