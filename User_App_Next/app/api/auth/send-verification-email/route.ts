import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'
import nodemailer from 'nodemailer'
import crypto from 'crypto'

export async function POST(request: NextRequest) {
  try {
    const { userId, userEmail, userName } = await request.json()

    // Validate inputs
    if (!userId || !userEmail) {
      return NextResponse.json({ error: 'Faltan datos requeridos' }, { status: 400 })
    }

    // Create Supabase admin client for service role operations
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

    // Generate secure token
    const token = crypto.randomBytes(32).toString('hex')
    const expiresAt = new Date()
    expiresAt.setHours(expiresAt.getHours() + 24)

    // Store token in database
    const { error: insertError } = await supabase
      .from('email_verification_tokens')
      .insert({
        user_id: userId,
        token,
        expires_at: expiresAt.toISOString(),
      })

    if (insertError) {
      console.error('Error storing token:', insertError)
      return NextResponse.json({ error: 'Error al generar token' }, { status: 500 })
    }

    // Build verification link
    const verificationLink = `${process.env.NEXT_PUBLIC_APP_URL}/api/auth/verify-email?token=${token}`

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
          .verify-button { background: #FFD400; color: #001854; padding: 15px 40px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 20px 0; font-weight: bold; font-size: 16px; }
          .verify-button:hover { background: #ffc700; }
          .info-box { background: white; padding: 20px; border-radius: 8px; border-left: 5px solid #FFD400; margin: 20px 0; }
          .footer { text-align: center; color: #666; font-size: 14px; margin-top: 30px; }
          .warning { color: #666; font-size: 12px; margin-top: 20px; }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1>🎾 Verifica tu Correo</h1>
            <p style="margin: 0; font-size: 18px;">${process.env.NEXT_PUBLIC_COURT_NAME}</p>
          </div>

          <div class="content">
            <h2>¡Hola ${userName || 'Usuario'}!</h2>
            <p>Gracias por registrarte en nuestro sistema de reservas de cancha de tenis.</p>
            <p>Para completar tu registro, por favor verifica tu correo electrónico haciendo clic en el botón de abajo:</p>

            <div style="text-align: center;">
              <a href="${verificationLink}" class="verify-button">
                ✓ Verificar mi Correo
              </a>
            </div>

            <div class="info-box">
              <p><strong>⏰ Este enlace expira en 24 horas</strong></p>
              <p style="margin: 0; font-size: 14px; color: #666;">Si no solicitaste este registro, puedes ignorar este correo de manera segura.</p>
            </div>

            <div class="warning">
              <p>¿Problemas con el botón? Copia y pega este enlace en tu navegador:</p>
              <p style="word-break: break-all; color: #2478CC;">${verificationLink}</p>
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
Verifica tu Correo - ${process.env.NEXT_PUBLIC_COURT_NAME}

¡Hola ${userName || 'Usuario'}!

Gracias por registrarte en nuestro sistema de reservas de cancha de tenis.

Para completar tu registro, por favor verifica tu correo electrónico visitando el siguiente enlace:

${verificationLink}

Este enlace expira en 24 horas.

Si no solicitaste este registro, puedes ignorar este correo de manera segura.

Sistema de Reservas de Cancha de Tenis - ${process.env.NEXT_PUBLIC_COURT_NAME}
    `

    // Send email
    await transporter.sendMail({
      from: `"${process.env.NEXT_PUBLIC_COURT_NAME}" <${process.env.SMTP_EMAIL}>`,
      to: userEmail,
      subject: `🎾 Verifica tu correo - ${process.env.NEXT_PUBLIC_COURT_NAME}`,
      text: textBody,
      html: htmlBody,
    })

    return NextResponse.json({
      success: true,
      message: 'Email de verificación enviado exitosamente'
    })
  } catch (error) {
    console.error('Error sending verification email:', error)
    return NextResponse.json({
      error: 'Error al enviar email de verificación'
    }, { status: 500 })
  }
}
