// ABOUTME: Server component for the /profile page — fetches profile, computes partner suggestions.
// ABOUTME: Reads tab from searchParams and passes initialTab + suggestions to ProfilePageClient.
import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import ProfilePageClient from '@/components/profile/ProfilePageClient'
import { computeSuggestions } from '@/lib/matching'

function thirtyDaysAgo(): string {
  const d = new Date()
  d.setDate(d.getDate() - 30)
  return d.toISOString().slice(0, 10)
}

export default async function ProfilePage({
  searchParams,
}: {
  searchParams: Promise<{ tab?: string }>
}) {
  const supabase = await createClient()
  const { data: { user }, error: authError } = await supabase.auth.getUser()
  if (authError || !user) redirect('/login')

  const { tab } = await searchParams

  const [profileResult, allProfilesResult, reservationsResult] = await Promise.all([
    supabase.from('users').select('*').eq('id', user.id).single(),
    supabase
      .from('users')
      .select('id, full_name, level_tier, categoria')
      .eq('profile_completed', true),
    supabase
      .from('reservations')
      .select('user_id, date, hour')
      .gte('date', thirtyDaysAgo()),
  ])

  const { data: profile, error } = profileResult
  if (error || !profile) redirect('/login')

  // Update last_profile_visit (fire and forget)
  supabase.from('users').update({ last_profile_visit: new Date().toISOString() }).eq('id', user.id)

  const suggestions = computeSuggestions(
    profile,
    allProfilesResult.data || [],
    reservationsResult.data || [],
  )

  return (
    <ProfilePageClient
      profile={profile}
      initialTab={tab}
      suggestions={suggestions}
    />
  )
}
