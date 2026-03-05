// ABOUTME: API route for reading a message thread with a specific user and marking messages as read.
// ABOUTME: GET fetches all messages between current user and [userId], marks received ones as read.
import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ userId: string }> }
) {
  const supabase = await createClient()
  const { data: { user }, error: authError } = await supabase.auth.getUser()
  if (authError || !user) return NextResponse.json({ error: 'No autenticado' }, { status: 401 })

  const { userId: otherId } = await params

  const { data: messages, error } = await supabase
    .from('direct_messages')
    .select('*')
    .or(
      `and(sender_id.eq.${user.id},recipient_id.eq.${otherId}),` +
      `and(sender_id.eq.${otherId},recipient_id.eq.${user.id})`
    )
    .order('created_at', { ascending: true })

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })

  // Mark unread messages sent to current user as read (fire and forget)
  supabase
    .from('direct_messages')
    .update({ read_at: new Date().toISOString() })
    .eq('sender_id', otherId)
    .eq('recipient_id', user.id)
    .is('read_at', null)

  return NextResponse.json({ messages: messages || [] })
}
