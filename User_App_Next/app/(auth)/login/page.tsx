'use client'

import { useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const router = useRouter()
  const supabase = createClient()

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      const { data, error: signInError } = await supabase.auth.signInWithPassword({
        email: email.trim().toLowerCase(),
        password,
      })

      if (signInError) {
        setError('Email o contraseña incorrectos')
        setLoading(false)
        return
      }

      // Check if first login completed
      const { data: profile } = await supabase
        .from('users')
        .select('first_login_completed')
        .eq('id', data.user.id)
        .single()

      if (!profile?.first_login_completed) {
        router.push('/access-code')
      } else {
        router.push('/')
      }
    } catch (err) {
      setError('Error al iniciar sesión')
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Header with Gradient */}
        <div className="bg-gradient-to-r from-us-open-blue to-us-open-light-blue text-white p-8 rounded-t-lg shadow-lg text-center">
          <div className="flex items-center justify-center gap-3 mb-2">
            <span className="text-5xl">🎾</span>
            <h1 className="text-3xl font-bold">Reservas de Cancha</h1>
          </div>
          <p className="text-lg opacity-90">{process.env.NEXT_PUBLIC_COURT_NAME}</p>
        </div>

        {/* Login Form */}
        <div className="bg-white p-8 rounded-b-lg shadow-lg">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-bold text-gray-800 inline-block border-b-4 border-us-open-yellow pb-1">
              ¡Bienvenido de Vuelta!
            </h2>
          </div>

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-4 py-3 bg-gray-100 border border-gray-300 rounded-lg focus:ring-2 focus:ring-us-open-light-blue focus:border-transparent focus:bg-white transition-colors"
                placeholder="tu@email.com"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                Contraseña
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full px-4 py-3 bg-gray-100 border border-gray-300 rounded-lg focus:ring-2 focus:ring-us-open-light-blue focus:border-transparent focus:bg-white transition-colors"
                placeholder="••••••••"
              />
            </div>

            {error && (
              <div className="bg-red-50 text-red-700 px-4 py-3 rounded-lg text-sm border border-red-200">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-us-open-blue text-white font-semibold py-3 rounded-lg hover:bg-opacity-90 transition-all shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
            </button>
          </form>

          <div className="mt-6 text-center space-y-2">
            <Link
              href="/register"
              className="block text-us-open-light-blue hover:underline font-medium"
            >
              ¿No tienes cuenta? Regístrate
            </Link>
            <Link
              href="/reset-password"
              className="block text-gray-600 hover:underline text-sm"
            >
              ¿Olvidaste tu contraseña?
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
