import { createClient } from '@/lib/supabase/server'
import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  const requestUrl = new URL(request.url)
  const code = requestUrl.searchParams.get('code')
  const origin = requestUrl.origin

  // If no code is provided, redirect to login with error
  if (!code) {
    return NextResponse.redirect(`${origin}/login?error=no_code`)
  }

  const supabase = await createClient()

  // Exchange the code for a session
  const { error } = await supabase.auth.exchangeCodeForSession(code)

  if (error) {
    // If exchange fails, redirect to login with error
    return NextResponse.redirect(`${origin}/login?error=auth_error`)
  }

  // After successful authentication, redirect to access code page
  // This is the first login flow where users enter their access code
  return NextResponse.redirect(`${origin}/access-code`)
}
