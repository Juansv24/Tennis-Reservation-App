import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'
import nodemailer from 'nodemailer'
import crypto from 'crypto'

export async function POST(request: NextRequest) {
  try {
    const { email } = await request.json()

    // Validate input
    if (!email) {
      return NextResponse.json({ error: 'Email requerido' }, { status: 400 })
    }

    // Create Supabase admin client
    const supabase = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.SUPABASE_SERVICE_ROLE_KEY!,
      {
        auth: {
          autoRefreshToken: false,
          persistSession: false
        }
      }
    )

    // Look up user by email (admin access to auth.users)
    const { data: { users }, error: userError } = await supabase.auth.admin.listUsers()
    const user = users?.find(u => u.email?.toLowerCase() === email.toLowerCase())

    // Always return success to prevent email enumeration
    // Only actually send email if user exists
    if (user) {
      // Generate secure token
      const token = crypto.randomBytes(32).toString('hex')
      const expiresAt = new Date()
      expiresAt.setHours(expiresAt.getHours() + 24)

      // Store token in database
      const { error: insertError } = await supabase
        .from('password_reset_tokens')
        .insert({
          user_id: user.id,
          token,
          expires_at: expiresAt.toISOString(),
        })

      if (insertError) {
        console.error('Error storing reset token:', insertError)
        // Still return success to user
        return NextResponse.json({
          success: true,
          message: 'Si el email existe, recibirás instrucciones para recuperar tu contraseña'
        })
      }

      // Build reset link
      const resetLink = `${process.env.NEXT_PUBLIC_APP_URL}/update-password?token=${token}`

      // Get user's full name from metadata
      const userName = user.user_metadata?.full_name || 'Usuario'

      // Configure SMTP transporter
      const transporter = nodemailer.createTransport({
        host: 'smtp.gmail.com',
        port: 587,
        secure: false,
        auth: {
          user: process.env.SMTP_EMAIL,
          pass: process.env.SMTP_PASSWORD,
        },
      })

      // Email HTML template
      const htmlBody = `
        <!DOCTYPE html>
        <html>
        <head>
          <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #001854 0%, #2478CC 100%); color: white; padding: 30px; text-align: center; border-radius: 10px; }
            .content { background: #f9f9f9; padding: 30px; border-radius: 10px; margin: 20px 0; }
            .reset-button { background: #FFD400; color: #001854; padding: 15px 40px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 20px 0; font-weight: bold; font-size: 16px; }
            .reset-button:hover { background: #ffc700; }
            .info-box { background: white; padding: 20px; border-radius: 8px; border-left: 5px solid #FFD400; margin: 20px 0; }
            .footer { text-align: center; color: #666; font-size: 14px; margin-top: 30px; }
            .warning { color: #666; font-size: 12px; margin-top: 20px; }
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <h1>🔐 Recuperar Contraseña</h1>
              <p style="margin: 0; font-size: 18px;">${process.env.NEXT_PUBLIC_COURT_NAME}</p>
            </div>

            <div class="content">
              <h2>¡Hola ${userName}!</h2>
              <p>Recibimos una solicitud para recuperar la contraseña de tu cuenta.</p>
              <p>Haz clic en el botón de abajo para crear una nueva contraseña:</p>

              <div style="text-align: center;">
                <a href="${resetLink}" class="reset-button">
                  🔑 Restablecer Contraseña
                </a>
              </div>

              <div class="info-box">
                <p><strong>⏰ Este enlace expira en 24 horas</strong></p>
                <p style="margin: 0; font-size: 14px; color: #666;">Si no solicitaste recuperar tu contraseña, puedes ignorar este correo de manera segura.</p>
              </div>

              <div class="warning">
                <p>¿Problemas con el botón? Copia y pega este enlace en tu navegador:</p>
                <p style="word-break: break-all; color: #2478CC;">${resetLink}</p>
              </div>
            </div>

            <div class="footer">
              <p>Sistema de Reservas de Cancha de Tenis - ${process.env.NEXT_PUBLIC_COURT_NAME}</p>
              <p>Esta es una confirmación automatizada. Por favor no respondas a este email.</p>
            </div>
          </div>
        </body>
        </html>
      `

      // Email text version (fallback)
      const textBody = `
Recuperar Contraseña - ${process.env.NEXT_PUBLIC_COURT_NAME}

¡Hola ${userName}!

Recibimos una solicitud para recuperar la contraseña de tu cuenta.

Para crear una nueva contraseña, visita el siguiente enlace:

${resetLink}

Este enlace expira en 24 horas.

Si no solicitaste recuperar tu contraseña, puedes ignorar este correo de manera segura.

Sistema de Reservas de Cancha de Tenis - ${process.env.NEXT_PUBLIC_COURT_NAME}
      `

      // Send email
      await transporter.sendMail({
        from: `"${process.env.NEXT_PUBLIC_COURT_NAME}" <${process.env.SMTP_EMAIL}>`,
        to: email,
        subject: `🔐 Recuperar contraseña - ${process.env.NEXT_PUBLIC_COURT_NAME}`,
        text: textBody,
        html: htmlBody,
      })
    }

    // Always return success (security: prevent email enumeration)
    return NextResponse.json({
      success: true,
      message: 'Si el email existe, recibirás instrucciones para recuperar tu contraseña'
    })
  } catch (error) {
    console.error('Error sending reset email:', error)
    // Still return success to prevent information leakage
    return NextResponse.json({
      success: true,
      message: 'Si el email existe, recibirás instrucciones para recuperar tu contraseña'
    })
  }
}
