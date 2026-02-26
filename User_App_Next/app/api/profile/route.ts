// ABOUTME: API route for reading and updating the current user's player profile.
// ABOUTME: GET returns full profile and updates last_profile_visit. PUT validates and saves fields.
import { createClient } from '@/lib/supabase/server'
import { NextRequest, NextResponse } from 'next/server'

const VALID_LEVEL_TIERS = ['Principiante', 'Intermedio', 'Avanzado']
const VALID_CATEGORIAS = ['Primera', 'Segunda', 'Tercera', 'Cuarta', 'Quinta', 'No sé']
const VALID_GENDERS = ['masculino', 'femenino', 'otro']

export async function GET(_request: NextRequest) {
  const supabase = await createClient()
  const { data: { user }, error: authError } = await supabase.auth.getUser()
  if (authError || !user) {
    return NextResponse.json({ error: 'No autenticado' }, { status: 401 })
  }

  const { data: profile, error } = await supabase
    .from('users')
    .select('*')
    .eq('id', user.id)
    .single()

  if (error || !profile) {
    return NextResponse.json({ error: 'Perfil no encontrado' }, { status: 404 })
  }

  // Update last_profile_visit (fire and forget)
  supabase.from('users').update({ last_profile_visit: new Date().toISOString() }).eq('id', user.id)

  return NextResponse.json({ profile })
}

export async function PUT(request: NextRequest) {
  const supabase = await createClient()
  const { data: { user }, error: authError } = await supabase.auth.getUser()
  if (authError || !user) {
    return NextResponse.json({ error: 'No autenticado' }, { status: 401 })
  }

  const body = await request.json()
  const { gender, age, level_tier, categoria, notify_suggestions, notify_match_posts, notify_messages } = body

  if (gender !== undefined && gender !== null && !VALID_GENDERS.includes(gender)) {
    return NextResponse.json({ error: 'Género inválido' }, { status: 400 })
  }
  if (level_tier !== undefined && level_tier !== null && !VALID_LEVEL_TIERS.includes(level_tier)) {
    return NextResponse.json({ error: 'Nivel inválido' }, { status: 400 })
  }
  if (categoria !== undefined && categoria !== null && !VALID_CATEGORIAS.includes(categoria)) {
    return NextResponse.json({ error: 'Categoría inválida' }, { status: 400 })
  }
  if (age !== undefined && age !== null && (typeof age !== 'number' || age < 1 || age > 120)) {
    return NextResponse.json({ error: 'Edad inválida' }, { status: 400 })
  }

  const updates: Record<string, any> = { profile_completed: true }
  if (gender !== undefined) updates.gender = gender
  if (age !== undefined) updates.age = age
  if (level_tier !== undefined) updates.level_tier = level_tier
  if (categoria !== undefined) updates.categoria = categoria
  if (notify_suggestions !== undefined) updates.notify_suggestions = notify_suggestions
  if (notify_match_posts !== undefined) updates.notify_match_posts = notify_match_posts
  if (notify_messages !== undefined) updates.notify_messages = notify_messages

  const { error } = await supabase.from('users').update(updates).eq('id', user.id)
  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }

  return NextResponse.json({ success: true })
}
