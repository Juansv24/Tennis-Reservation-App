import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import ReservationGrid from '@/components/ReservationGrid'
import { getTodayDate } from '@/lib/constants'

export const dynamic = 'force-dynamic'
export const revalidate = 0

export default async function DashboardPage() {
  const supabase = await createClient()
  const today = getTodayDate()

  // Get user
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) redirect('/login')

  // Get user profile
  const { data: profile } = await supabase
    .from('users')
    .select('*')
    .eq('id', user.id)
    .single()

  if (!profile) redirect('/login')

  // Get today's reservations and maintenance
  const [reservationsResult, maintenanceResult] = await Promise.all([
    supabase
      .from('reservations')
      .select('*, users(full_name)')
      .eq('date', today)
      .order('hour'),
    supabase
      .from('blocked_slots')
      .select('*')
      .eq('date', today),
  ])

  return (
    <ReservationGrid
      initialReservations={reservationsResult.data || []}
      initialMaintenance={maintenanceResult.data || []}
      user={profile}
      initialDate={today}
    />
  )
}
