import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'
import { getColombiaTimeServer } from '@/lib/timezone-server'

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const token = searchParams.get('token')

    if (!token) {
      return NextResponse.redirect(
        new URL('/login?error=invalid_token', request.url)
      )
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
      .from('email_verification_tokens')
      .select('*')
      .eq('token', token)
      .is('used_at', null)
      .single()

    if (tokenError || !tokenData) {
      return NextResponse.redirect(
        new URL('/login?error=token_not_found', request.url)
      )
    }

    // Check if token is expired (using Colombian timezone)
    const now = getColombiaTimeServer()
    const expiresAt = new Date(tokenData.expires_at)
    if (now > expiresAt) {
      return NextResponse.redirect(
        new URL('/login?error=token_expired', request.url)
      )
    }

    // Mark token as used
    await supabase
      .from('email_verification_tokens')
      .update({ used_at: now.toISOString() })
      .eq('token', token)

    // Update user metadata to mark email as verified
    const { error: updateError } = await supabase.auth.admin.updateUserById(
      tokenData.user_id,
      {
        email_confirm: true,
        user_metadata: { email_verified: true }
      }
    )

    if (updateError) {
      console.error('Error updating user:', updateError)
      return NextResponse.redirect(
        new URL('/login?error=verification_failed', request.url)
      )
    }

    // Success - redirect to login with success message
    return NextResponse.redirect(
      new URL('/login?verified=true', request.url)
    )
  } catch (error) {
    console.error('Error verifying email:', error)
    return NextResponse.redirect(
      new URL('/login?error=verification_error', request.url)
    )
  }
}
