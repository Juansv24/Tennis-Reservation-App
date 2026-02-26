// ABOUTME: Server component for the /profile page — fetches user profile and renders Mi Perfil tab.
// ABOUTME: Inherits auth check, header, and layout from the (dashboard) route group layout.
import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import ProfilePageClient from '@/components/profile/ProfilePageClient'

export default async function ProfilePage() {
  const supabase = await createClient()
  const { data: { user }, error: authError } = await supabase.auth.getUser()
  if (authError || !user) redirect('/login')

  const { data: profile, error } = await supabase
    .from('users')
    .select('*')
    .eq('id', user.id)
    .single()

  if (error || !profile) redirect('/login')

  // Update last_profile_visit
  await supabase
    .from('users')
    .update({ last_profile_visit: new Date().toISOString() })
    .eq('id', user.id)

  return <ProfilePageClient profile={profile} />
}
