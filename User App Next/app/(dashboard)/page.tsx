import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import ReservationGrid from '@/components/ReservationGrid'
import LockCodeDisplay from '@/components/LockCodeDisplay'
import { getTodayDate, getTomorrowDate } from '@/lib/constants'

export const dynamic = 'force-dynamic'
export const revalidate = 0

export default async function DashboardPage() {
  const supabase = await createClient()
  const today = getTodayDate()
  const tomorrow = getTomorrowDate()

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

  // Get today's and tomorrow's reservations and maintenance
  const [reservationsResult, maintenanceResult, userReservations, lockCodeResult] = await Promise.all([
    supabase
      .from('reservations')
      .select('*, users(full_name)')
      .eq('date', today)
      .order('hour'),
    supabase
      .from('maintenance_slots')
      .select('*')
      .eq('date', today),
    supabase
      .from('reservations')
      .select('*')
      .eq('user_id', user.id)
      .in('date', [today, tomorrow]),
    supabase
      .from('lock_code')
      .select('code')
      .order('created_at', { ascending: false })
      .limit(1)
      .single(),
  ])

  const hasReservations = userReservations.data && userReservations.data.length > 0
  const lockCode = lockCodeResult.data?.code || ''

  return (
    <div className="space-y-4">
      <LockCodeDisplay lockCode={lockCode} hasReservations={hasReservations} />
      <ReservationGrid
        initialReservations={reservationsResult.data || []}
        initialMaintenance={maintenanceResult.data || []}
        user={profile}
        initialDate={today}
      />
    </div>
  )
}
