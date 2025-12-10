import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const token = searchParams.get('token')

    if (!token) {
      return NextResponse.json({ error: 'Token requerido' }, { status: 400 })
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
      return NextResponse.json({ error: 'Token no encontrado' }, { status: 404 })
    }

    // Check if token is expired
    const now = new Date()
    const expiresAt = new Date(tokenData.expires_at)
    if (now > expiresAt) {
      return NextResponse.json({ error: 'Token expirado' }, { status: 410 })
    }

    // Token is valid
    return NextResponse.json({ valid: true, userId: tokenData.user_id })
  } catch (error) {
    console.error('Error validating token:', error)
    return NextResponse.json({ error: 'Error al validar token' }, { status: 500 })
  }
}
