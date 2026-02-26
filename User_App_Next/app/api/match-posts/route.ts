// ABOUTME: API route for listing and creating match posts.
// ABOUTME: GET returns all active posts with author info and comment counts. POST creates a post.
import { createClient } from '@/lib/supabase/server'
import { NextRequest, NextResponse } from 'next/server'

const VALID_LEVEL_TIERS = ['Principiante', 'Intermedio', 'Avanzado']
const VALID_CATEGORIAS = ['Primera', 'Segunda', 'Tercera', 'Cuarta', 'Quinta', 'No sé']

export async function GET(_request: NextRequest) {
  const supabase = await createClient()
  const { data: { user }, error: authError } = await supabase.auth.getUser()
  if (authError || !user) return NextResponse.json({ error: 'No autenticado' }, { status: 401 })

  const [postsResult, countsResult] = await Promise.all([
    supabase
      .from('match_posts')
      .select('*, users(full_name, level_tier, categoria)')
      .eq('is_active', true)
      .order('created_at', { ascending: false }),
    supabase
      .from('match_post_comments')
      .select('post_id'),
  ])

  const commentCounts: Record<string, number> = {}
  for (const row of countsResult.data || []) {
    commentCounts[row.post_id] = (commentCounts[row.post_id] || 0) + 1
  }

  const posts = (postsResult.data || []).map(post => ({
    ...post,
    comment_count: commentCounts[post.id] || 0,
  }))

  return NextResponse.json({ posts })
}

export async function POST(request: NextRequest) {
  const supabase = await createClient()
  const { data: { user }, error: authError } = await supabase.auth.getUser()
  if (authError || !user) return NextResponse.json({ error: 'No autenticado' }, { status: 401 })

  const body = await request.json()
  const { type, date, hour, desired_level_tier, desired_categoria, note } = body

  if (!['specific', 'standing'].includes(type)) {
    return NextResponse.json({ error: 'Tipo inválido' }, { status: 400 })
  }
  if (type === 'specific') {
    if (!date || typeof date !== 'string') {
      return NextResponse.json({ error: 'Fecha requerida para partido específico' }, { status: 400 })
    }
    if (hour === undefined || hour === null || typeof hour !== 'number' || hour < 6 || hour > 20) {
      return NextResponse.json({ error: 'Hora inválida' }, { status: 400 })
    }
  }
  if (desired_level_tier && !VALID_LEVEL_TIERS.includes(desired_level_tier)) {
    return NextResponse.json({ error: 'Nivel inválido' }, { status: 400 })
  }
  if (desired_categoria && !VALID_CATEGORIAS.includes(desired_categoria)) {
    return NextResponse.json({ error: 'Categoría inválida' }, { status: 400 })
  }
  if (note && note.length > 280) {
    return NextResponse.json({ error: 'La nota no puede superar 280 caracteres' }, { status: 400 })
  }

  const { data: userProfile } = await supabase
    .from('users')
    .select('profile_completed')
    .eq('id', user.id)
    .single()
  if (!userProfile?.profile_completed) {
    return NextResponse.json({ error: 'Completa tu perfil para poder publicar' }, { status: 403 })
  }

  const { data: post, error } = await supabase
    .from('match_posts')
    .insert({
      user_id: user.id,
      type,
      date: type === 'specific' ? date : null,
      hour: type === 'specific' ? hour : null,
      desired_level_tier: desired_level_tier || null,
      desired_categoria: desired_categoria || null,
      note: note || null,
    })
    .select()
    .single()

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json({ post }, { status: 201 })
}
