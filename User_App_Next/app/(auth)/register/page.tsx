'use client'

import { useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

export default function RegisterPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const router = useRouter()
  const supabase = createClient()

  async function handleRegister(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)

    // Validation
    if (!fullName.trim()) {
      setError('Por favor ingresa tu nombre completo')
      setLoading(false)
      return
    }

    if (password.length < 6) {
      setError('La contraseña debe tener al menos 6 caracteres')
      setLoading(false)
      return
    }

    // Check if password contains at least one letter
    if (!/[a-zA-Z]/.test(password)) {
      setError('La contraseña debe contener al menos una letra')
      setLoading(false)
      return
    }

    // Check if password contains at least one number
    if (!/[0-9]/.test(password)) {
      setError('La contraseña debe contener al menos un número')
      setLoading(false)
      return
    }

    // Check if passwords match
    if (password !== confirmPassword) {
      setError('Las contraseñas no coinciden')
      setLoading(false)
      return
    }

    try {
      const { data, error: signUpError } = await supabase.auth.signUp({
        email: email.trim().toLowerCase(),
        password,
        options: {
          data: {
            full_name: fullName.trim(),
          },
          emailRedirectTo: undefined, // Disable Supabase automatic emails
          // Note: User starts unconfirmed, our custom email will handle verification
        },
      })

      if (signUpError) {
        if (signUpError.message.includes('already registered')) {
          setError('Este email ya está registrado')
        } else {
          setError(signUpError.message)
        }
        setLoading(false)
        return
      }

      // Send custom verification email
      if (data.user) {
        try {
          await fetch('/api/auth/send-verification-email', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              userId: data.user.id,
              userEmail: email.trim().toLowerCase(),
              userName: fullName.trim(),
            }),
          })
        } catch (emailError) {
          console.error('Error sending verification email:', emailError)
          // Don't fail registration if email fails
        }
      }

      // Success
      alert('✅ Cuenta creada exitosamente! Por favor revisa tu correo electrónico para verificar tu cuenta.')
      router.push('/login')
    } catch (err) {
      setError('Error al crear cuenta')
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-xl p-8">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-us-open-blue mb-2">
          Crear Cuenta
        </h1>
        <p className="text-gray-600">Regístrate para reservar tu cancha</p>
      </div>

      <form onSubmit={handleRegister} className="space-y-4">
        <div>
          <label htmlFor="fullName" className="block text-sm font-medium text-gray-700 mb-1">
            Nombre Completo
          </label>
          <input
            id="fullName"
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            required
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-us-open-light-blue focus:border-transparent"
            placeholder="Juan Pérez"
          />
        </div>

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
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-us-open-light-blue focus:border-transparent"
            placeholder="tu@email.com"
          />
        </div>

        <div>
          <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
            Contraseña
          </label>
          <div className="mb-2 text-xs text-gray-600">
            <p>• Mínimo 6 caracteres</p>
            <p>• Debe contener al menos una letra</p>
            <p>• Debe contener al menos un número</p>
          </div>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-us-open-light-blue focus:border-transparent"
            placeholder="Ej: MiPass123"
          />
        </div>

        <div>
          <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-1">
            Confirmar Contraseña
          </label>
          <input
            id="confirmPassword"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            minLength={6}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-us-open-light-blue focus:border-transparent"
            placeholder="Repite tu contraseña"
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
          {loading ? 'Creando cuenta...' : 'Registrarse'}
        </button>
      </form>

      <div className="mt-6 text-center">
        <Link
          href="/login"
          className="text-us-open-light-blue hover:underline"
        >
          ¿Ya tienes cuenta? Inicia sesión
        </Link>
      </div>
    </div>
  )
}
