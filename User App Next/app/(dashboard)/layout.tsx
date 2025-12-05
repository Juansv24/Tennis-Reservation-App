import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import Header from '@/components/Header'
import WelcomeBanner from '@/components/WelcomeBanner'
import UserDetailsBox from '@/components/UserDetailsBox'
import InstructionsSection from '@/components/InstructionsSection'

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const supabase = await createClient()

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

  return (
    <div className="min-h-screen bg-gray-50">
      <Header user={profile} />
      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="space-y-6">
          <WelcomeBanner user={profile} />

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              {children}
            </div>
            <div className="space-y-6">
              <UserDetailsBox user={profile} />
              <InstructionsSection />
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
