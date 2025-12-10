'use client'

import { useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import Link from 'next/link'

export default function ResetPasswordPage() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const supabase = createClient()

  async function handleResetPassword(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      // Call custom reset email API
      const response = await fetch('/api/auth/send-reset-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim().toLowerCase() }),
      })

      if (!response.ok) {
        setError('Error al enviar el correo de recuperación')
        setLoading(false)
        return
      }

      setSuccess(true)
      setLoading(false)
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
            <h1 className="text-3xl font-bold">Recuperar Contraseña</h1>
          </div>
          <p className="text-lg opacity-90">{process.env.NEXT_PUBLIC_COURT_NAME}</p>
        </div>

        {/* Reset Password Form */}
        <div className="bg-white p-8 rounded-b-lg shadow-lg">
          {success ? (
            <div className="text-center">
              <div className="bg-green-50 text-green-700 px-4 py-3 rounded-lg text-sm border border-green-200 mb-4">
                ✅ Correo enviado exitosamente
              </div>
              <p className="text-gray-700 mb-4">
                Te hemos enviado un correo con instrucciones para recuperar tu contraseña.
              </p>
              <p className="text-gray-600 text-sm mb-6">
                Por favor revisa tu bandeja de entrada y sigue las instrucciones.
              </p>
              <Link
                href="/login"
                className="inline-block bg-us-open-blue text-white font-semibold py-3 px-6 rounded-lg hover:bg-opacity-90 transition-all shadow-md hover:shadow-lg"
              >
                Volver al Inicio de Sesión
              </Link>
            </div>
          ) : (
            <>
              <div className="text-center mb-6">
                <h2 className="text-2xl font-bold text-gray-800 inline-block border-b-4 border-us-open-yellow pb-1">
                  Recuperar Contraseña
                </h2>
                <p className="text-gray-600 text-sm mt-3">
                  Ingresa tu correo electrónico y te enviaremos instrucciones para recuperar tu contraseña.
                </p>
              </div>

              <form onSubmit={handleResetPassword} className="space-y-4">
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
                  {loading ? 'Enviando...' : 'Enviar Correo de Recuperación'}
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
            </>
          )}
        </div>
      </div>
    </div>
  )
}
