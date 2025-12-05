import { NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

export async function GET() {
  const supabase = createClient()

  // Verify authentication
  const {
    data: { user },
    error: authError,
  } = await supabase.auth.getUser()

  if (authError || !user) {
    return NextResponse.json({ error: 'No autenticado' }, { status: 401 })
  }

  // Query lock_code table for the most recent code
  const { data, error } = await supabase
    .from('lock_code')
    .select('code')
    .order('created_at', { ascending: false })
    .limit(1)
    .single()

  if (error) {
    console.error('Error fetching lock code:', error)
    return NextResponse.json(
      { error: 'Error al obtener el código del candado' },
      { status: 500 }
    )
  }

  if (!data) {
    return NextResponse.json(
      { error: 'No se encontró código del candado' },
      { status: 404 }
    )
  }

  return NextResponse.json({ lock_code: data.code })
}
