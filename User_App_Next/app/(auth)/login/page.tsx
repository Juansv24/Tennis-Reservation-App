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
    <div className="min-h-screen bg-gradient-to-br from-us-open-blue to-us-open-light-blue flex items-center justify-center p-4">
      <div className="w-full max-w-lg min-h-[85vh] flex flex-col">
        {/* Header with Gradient */}
        <div className="bg-gradient-to-r from-us-open-blue to-us-open-light-blue text-white py-12 px-8 rounded-t-lg shadow-lg text-center">
          <h1 className="text-3xl font-bold mb-3">Sistema de Reservas</h1>
          <p className="text-lg opacity-90">Cancha de tenis Colina Campestre</p>
        </div>

        {/* Login Form */}
        <div className="bg-white pt-2 pb-12 px-8 rounded-b-lg shadow-lg flex-1 flex flex-col justify-center">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-gray-800 inline-block border-b-4 border-us-open-yellow pb-1">
              ¡Bienvenido de Vuelta!
            </h2>
          </div>

          <form onSubmit={handleLogin} className="space-y-6">
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

          <div className="mt-8 text-center space-y-3">
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

          {/* Trademark */}
          <div className="mt-8 text-center">
            <p className="text-xs text-gray-400">
              © {new Date().getFullYear()} Sistema de reservas de cancha de tenis. Todos los derechos reservados. Desarrollado por Juan Sebastian Vallejo.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
