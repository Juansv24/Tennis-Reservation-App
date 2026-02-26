// ABOUTME: API route for listing and adding comments on a match post.
// ABOUTME: GET returns all comments for a post. POST adds a comment from the authenticated user.
import { createClient } from '@/lib/supabase/server'
import { NextRequest, NextResponse } from 'next/server'

interface RouteContext {
  params: Promise<{ id: string }>
}

export async function GET(_request: NextRequest, context: RouteContext) {
  const supabase = await createClient()
  const { data: { user }, error: authError } = await supabase.auth.getUser()
  if (authError || !user) return NextResponse.json({ error: 'No autenticado' }, { status: 401 })

  const { id } = await context.params

  const { data: comments, error } = await supabase
    .from('match_post_comments')
    .select('*, users(full_name)')
    .eq('post_id', id)
    .order('created_at', { ascending: true })

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json({ comments: comments || [] })
}

export async function POST(request: NextRequest, context: RouteContext) {
  const supabase = await createClient()
  const { data: { user }, error: authError } = await supabase.auth.getUser()
  if (authError || !user) return NextResponse.json({ error: 'No autenticado' }, { status: 401 })

  const { id } = await context.params
  const body = await request.json()
  const { content } = body

  if (!content || typeof content !== 'string' || !content.trim()) {
    return NextResponse.json({ error: 'Contenido requerido' }, { status: 400 })
  }
  if (content.length > 500) {
    return NextResponse.json({ error: 'El comentario no puede superar 500 caracteres' }, { status: 400 })
  }

  const { data: userProfile } = await supabase
    .from('users')
    .select('profile_completed')
    .eq('id', user.id)
    .single()
  if (!userProfile?.profile_completed) {
    return NextResponse.json({ error: 'Completa tu perfil para poder comentar' }, { status: 403 })
  }

  const { data: comment, error } = await supabase
    .from('match_post_comments')
    .insert({ post_id: id, user_id: user.id, content: content.trim() })
    .select('*, users(full_name)')
    .single()

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json({ comment }, { status: 201 })
}
