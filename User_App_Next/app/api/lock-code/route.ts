import { NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

export async function GET() {
  const supabase = await createClient()

  // Verify authentication
  const {
    data: { user },
    error: authError,
  } = await supabase.auth.getUser()

  if (authError || !user) {
    return NextResponse.json({ error: 'No autenticado' }, { status: 401 })
  }

  // Query lock_code table for the most recent code
  const { data: lockCodeData } = await supabase
    .from('lock_code')
    .select('code')
    .order('created_at', { ascending: false })
    .limit(1)
    .single()

  const lockCode = lockCodeData?.code || ''

  return NextResponse.json({ lock_code: lockCode })
}
