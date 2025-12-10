'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

export default function AccessCodePage() {
  const [code, setCode] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const router = useRouter()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      const response = await fetch('/api/auth/validate-access-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: code.trim().toUpperCase() }),
      })

      const data = await response.json()

      if (!response.ok) {
        setError(data.error || 'Código inválido')
        setLoading(false)
        return
      }

      // Success - force hard navigation to ensure server components re-fetch
      // This prevents the access code loop by ensuring first_login_completed flag is read fresh
      window.location.href = '/'
    } catch (err) {
      setError('Error al validar código')
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-xl p-8">
      <div className="text-center mb-8">
        <div className="text-6xl mb-4">🔑</div>
        <h1 className="text-2xl font-bold text-us-open-blue mb-2">
          Código de Acceso
        </h1>
        <p className="text-gray-600">
          Ingresa el código de acceso proporcionado por el administrador
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="code" className="block text-sm font-medium text-gray-700 mb-1">
            Código de Acceso
          </label>
          <input
            id="code"
            type="text"
            value={code}
            onChange={(e) => setCode(e.target.value.toUpperCase())}
            required
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-us-open-light-blue focus:border-transparent text-center text-lg font-mono tracking-wider"
            maxLength={20}
          />
        </div>

        {error && (
          <div className="bg-red-50 text-red-700 px-4 py-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-us-open-light-blue text-white font-semibold py-3 rounded-lg hover:bg-us-open-blue transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Validando...' : 'Validar Código'}
        </button>
      </form>

      <div className="mt-6 text-center text-sm text-gray-600">
        ¿No tienes un código de acceso? Contacta al administrador
      </div>
    </div>
  )
}
