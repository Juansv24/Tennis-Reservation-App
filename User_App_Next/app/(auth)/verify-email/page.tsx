import Link from 'next/link'

export default function VerifyEmailPage() {
  return (
    <div className="bg-white rounded-lg shadow-xl p-8 text-center">
      <div className="text-6xl mb-4">📧</div>
      <h1 className="text-2xl font-bold text-us-open-blue mb-4">
        Verifica tu Email
      </h1>
      <p className="text-gray-600 mb-6">
        Hemos enviado un enlace de verificación a tu correo electrónico.
        <br />
        Por favor revisa tu bandeja de entrada y haz clic en el enlace para activar tu cuenta.
      </p>
      <div className="bg-blue-50 text-blue-700 px-4 py-3 rounded-lg text-sm mb-6">
        💡 Revisa también tu carpeta de spam si no ves el correo
      </div>
      <Link
        href="/login"
        className="inline-block bg-us-open-light-blue text-white font-semibold px-6 py-3 rounded-lg hover:bg-us-open-blue transition-colors"
      >
        Ir a Iniciar Sesión
      </Link>
    </div>
  )
}
