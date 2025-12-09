'use client'

import { useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

export default function UpdatePasswordPage() {
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()
  const supabase = createClient()

  async function handleUpdatePassword(e: React.FormEvent) {
    e.preventDefault()
    setError(null)

    if (password !== confirmPassword) {
      setError('Las contraseñas no coinciden')
      return
    }

    if (password.length < 6) {
      setError('La contraseña debe tener al menos 6 caracteres')
      return
    }

    setLoading(true)

    try {
      const { error: updateError } = await supabase.auth.updateUser({
        password: password
      })

      if (updateError) {
        setError('Error al actualizar la contraseña')
        setLoading(false)
        return
      }

      // Success - redirect to login
      alert('✅ Contraseña actualizada exitosamente')
      router.push('/login')
    } catch (err) {
      setError('Error al procesar la solicitud')
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-md">
        {/* Header with Gradient */}
        <div className="bg-gradient-to-r from-us-open-blue to-us-open-light-blue text-white p-8 rounded-t-lg shadow-lg text-center">
          <div className="flex items-center justify-center gap-3 mb-2">
            <span className="text-5xl">🎾</span>
            <h1 className="text-3xl font-bold">Nueva Contraseña</h1>
          </div>
          <p className="text-lg opacity-90">{process.env.NEXT_PUBLIC_COURT_NAME}</p>
        </div>

        {/* Update Password Form */}
        <div className="bg-white p-8 rounded-b-lg shadow-lg">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-bold text-gray-800 inline-block border-b-4 border-us-open-yellow pb-1">
              Actualizar Contraseña
            </h2>
            <p className="text-gray-600 text-sm mt-3">
              Ingresa tu nueva contraseña
            </p>
          </div>

          <form onSubmit={handleUpdatePassword} className="space-y-4">
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                Nueva Contraseña
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                className="w-full px-4 py-3 bg-gray-100 border border-gray-300 rounded-lg focus:ring-2 focus:ring-us-open-light-blue focus:border-transparent focus:bg-white transition-colors"
                placeholder="••••••••"
              />
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-1">
                Confirmar Nueva Contraseña
              </label>
              <input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                minLength={6}
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
              {loading ? 'Actualizando...' : 'Actualizar Contraseña'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <Link
              href="/login"
              className="text-us-open-light-blue hover:underline font-medium"
            >
              ← Volver al Inicio de Sesión
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
