import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import Header from '@/components/Header'
import WelcomeBanner from '@/components/WelcomeBanner'
import CollapsibleSections from '@/components/CollapsibleSections'
import { getTodayDate, getTomorrowDate } from '@/lib/constants'

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const supabase = await createClient()
  const today = getTodayDate()
  const tomorrow = getTomorrowDate()

  // Check authentication
  const { data: { user }, error: authError } = await supabase.auth.getUser()

  if (authError || !user) {
    redirect('/login')
  }

  // Get user profile
  const { data: profile } = await supabase
    .from('users')
    .select('*')
    .eq('id', user.id)
    .single()

  if (!profile) {
    redirect('/login')
  }

  // Check if first login completed
  if (!profile.first_login_completed) {
    redirect('/access-code')
  }

  // Check if user has reservations and get lock code
  const [userReservations, lockCodeResult] = await Promise.all([
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

  const hasReservations = !!(userReservations.data && userReservations.data.length > 0)
  const lockCode = lockCodeResult.data?.code || ''

  return (
    <div className="min-h-screen bg-white md:bg-gray-50 flex items-center justify-center md:block p-4 md:p-0">
      <div className="w-full max-w-7xl md:max-w-none min-h-[95vh] md:min-h-screen flex flex-col bg-white rounded-lg md:rounded-none shadow-2xl md:shadow-none overflow-hidden">
        <Header user={profile} lockCode={lockCode} hasReservations={hasReservations} />
        <main className="px-4 py-8 flex-1 bg-white md:max-w-7xl md:mx-auto">
          <div className="space-y-6">
            <WelcomeBanner user={profile} />
            <CollapsibleSections user={profile} />
            {children}
          </div>
        </main>

        {/* Trademark Footer */}
        <footer className="mt-auto bg-white md:max-w-7xl md:mx-auto md:w-full">
          <hr className="border-gray-300" />
          <div className="py-4 text-center px-4">
            <p className="text-xs text-gray-400">
              © {new Date().getFullYear()} Sistema de reservas de cancha de tenis. Todos los derechos reservados. Desarrollado por Juan Sebastian Vallejo.
            </p>
          </div>
        </footer>
      </div>
    </div>
  )
}
