// ABOUTME: API route for deleting a match post (soft delete, owner only).
// ABOUTME: Checks authentication and ownership before setting is_active to false.
import { createClient } from '@/lib/supabase/server'
import { NextRequest, NextResponse } from 'next/server'

interface RouteContext {
  params: Promise<{ id: string }>
}

export async function DELETE(_request: NextRequest, context: RouteContext) {
  const supabase = await createClient()
  const { data: { user }, error: authError } = await supabase.auth.getUser()
  if (authError || !user) return NextResponse.json({ error: 'No autenticado' }, { status: 401 })

  const { id } = await context.params

  const { data: post, error: fetchError } = await supabase
    .from('match_posts')
    .select('user_id')
    .eq('id', id)
    .single()

  if (fetchError || !post) return NextResponse.json({ error: 'No encontrado' }, { status: 404 })
  if (post.user_id !== user.id) return NextResponse.json({ error: 'Sin permiso' }, { status: 403 })

  const { error } = await supabase
    .from('match_posts')
    .update({ is_active: false })
    .eq('id', id)

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json({ success: true })
}
