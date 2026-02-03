import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import ReservationGrid from '@/components/ReservationGrid'
import { getTodayDate } from '@/lib/constants'
import { generateTennisSchoolSlots } from '@/lib/tennis-school'
import type { MaintenanceSlot } from '@/types/database.types'

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

  // Get today's reservations, maintenance, and system settings
  const [reservationsResult, maintenanceResult, systemSettingsResult] = await Promise.all([
    supabase
      .from('reservations')
      .select('*, users(full_name)')
      .eq('date', today)
      .order('hour'),
    supabase
      .from('blocked_slots')
      .select('*')
      .eq('date', today),
    supabase
      .from('system_settings')
      .select('tennis_school_enabled')
      .single(),
  ])

  // Combine blocked_slots with tennis school slots if enabled
  let maintenanceSlots: MaintenanceSlot[] = maintenanceResult.data || []

  if (systemSettingsResult.data?.tennis_school_enabled) {
    const tennisSchoolSlots = generateTennisSchoolSlots(today)
    maintenanceSlots = [...maintenanceSlots, ...tennisSchoolSlots]
  }

  return (
    <ReservationGrid
      initialReservations={reservationsResult.data || []}
      initialMaintenance={maintenanceSlots}
      user={profile}
      initialDate={today}
      tennisSchoolEnabled={systemSettingsResult.data?.tennis_school_enabled || false}
    />
  )
}
