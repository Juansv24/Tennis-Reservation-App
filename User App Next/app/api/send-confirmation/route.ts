import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'
import nodemailer from 'nodemailer'

export async function POST(request: NextRequest) {
  try {
    const supabase = await createClient()

    // Verify authentication
    const { data: { user }, error: authError } = await supabase.auth.getUser()
    if (authError || !user) {
      return NextResponse.json({ error: 'No autenticado' }, { status: 401 })
    }

    const { date, hours, userName, userEmail, lockCode } = await request.json()

    // Validate inputs
    if (!date || !hours || !userName || !userEmail) {
      return NextResponse.json({ error: 'Faltan datos requeridos' }, { status: 400 })
    }

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

    // Format date in Spanish
    const dateObj = new Date(date + 'T00:00:00')
    const daysEs = ['domingo', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado']
    const monthsEs = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                      'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
    const dayName = daysEs[dateObj.getDay()]
    const monthName = monthsEs[dateObj.getMonth()]
    const formattedDate = `${dayName}, ${dateObj.getDate()} de ${monthName} de ${dateObj.getFullYear()}`

    // Format times
    const sortedHours = hours.sort((a: number, b: number) => a - b)
    const startTime = `${sortedHours[0].toString().padStart(2, '0')}:00`
    const endTime = `${(sortedHours[sortedHours.length - 1] + 1).toString().padStart(2, '0')}:00`

    // Create Google Calendar link
    const startDateTime = new Date(date + `T${sortedHours[0].toString().padStart(2, '0')}:00:00`)
    const endDateTime = new Date(date + `T${(sortedHours[sortedHours.length - 1] + 1).toString().padStart(2, '0')}:00:00`)

    const calStart = startDateTime.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z'
    const calEnd = endDateTime.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z'

    const calendarLink = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=Reserva%20Cancha%20de%20Tenis&dates=${calStart}/${calEnd}&details=Reserva%20de%20Cancha%20de%20Tenis%20en%20Colina%20Campestre%0A%0AReservado%20por:%20${encodeURIComponent(userName)}%0AEmail:%20${encodeURIComponent(userEmail)}&location=Cancha%20de%20Tenis%20Colina%20Campestre`

    // Email HTML template (matching Streamlit)
    const htmlBody = `
      <!DOCTYPE html>
      <html>
      <head>
        <style>
          body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
          .container { max-width: 600px; margin: 0 auto; padding: 20px; }
          .header { background: linear-gradient(135deg, #001854 0%, #2478CC 100%); color: white; padding: 30px; text-align: center; border-radius: 10px; }
          .content { background: #f9f9f9; padding: 30px; border-radius: 10px; margin: 20px 0; }
          .reservation-details { background: white; padding: 20px; border-radius: 8px; border-left: 5px solid #FFD400; margin: 20px 0; }
          .lock-code { background: linear-gradient(135deg, #001854 0%, #2478CC 100%); color: white; padding: 20px; text-align: center; border-radius: 8px; margin: 20px 0; }
          .lock-code-number { font-size: 36px; font-weight: bold; letter-spacing: 8px; margin: 10px 0; }
          .calendar-button { background: #4CAF50; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 20px 0; font-weight: bold; }
          .footer { text-align: center; color: #666; font-size: 14px; margin-top: 30px; }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1>🎾 ¡Reserva Confirmada!</h1>
          </div>

          <div class="content">
            <h2>¡Hola ${userName}!</h2>
            <p>¡Excelentes noticias! Tu reserva ha sido confirmada. Aquí están los detalles:</p>

            <div class="reservation-details">
              <h3>📅 Detalles de la Reserva</h3>
              <p><strong>Nombre:</strong> ${userName}</p>
              <p><strong>Fecha:</strong> ${formattedDate}</p>
              <p><strong>Hora:</strong> ${startTime} - ${endTime}</p>
              <p><strong>Duración:</strong> ${hours.length} hora(s)</p>
              <p><strong>Ubicación:</strong> Cancha de Tenis Colina Campestre</p>
            </div>

            ${lockCode ? `
            <div class="lock-code">
              <p><strong>🔐 Código del Candado</strong></p>
              <div class="lock-code-number">${lockCode}</div>
              <p style="font-size: 14px; opacity: 0.9;">Usa este código para acceder a la cancha</p>
            </div>
            ` : ''}

            <p style="text-align: center;">
              <a href="${calendarLink}" class="calendar-button" target="_blank">
                📅 Agregar a Google Calendar
              </a>
            </p>

            <p style="font-size: 12px; color: #666; text-align: center;">¿Problemas con el botón?
            <a href="${calendarLink}" style="color: #2478CC;">Haz clic aquí</a></p>
          </div>

          <div class="footer">
            <p>Sistema de Reservas de Cancha de Tenis - Colina Campestre</p>
            <p>Esta es una confirmación automatizada. Por favor no respondas a este email.</p>
          </div>
        </div>
      </body>
      </html>
    `

    // Email text version (fallback)
    const textBody = `
¡Reserva de Cancha de Tenis Confirmada!

¡Hola ${userName}!

Tu reserva de cancha de tenis ha sido confirmada:

Detalles de la Reserva:
- Nombre: ${userName}
- Fecha: ${formattedDate}
- Hora: ${startTime} - ${endTime}
- Duración: ${hours.length} hora(s)
- Ubicación: Cancha de Tenis Colina Campestre

${lockCode ? `Código del candado: ${lockCode}` : ''}

Agregar a Google Calendar: ${calendarLink}

Sistema de Reservas de Cancha de Tenis - Colina Campestre
    `

    // Send email
    await transporter.sendMail({
      from: `"Cancha de Tenis Colina Campestre" <${process.env.SMTP_EMAIL}>`,
      to: userEmail,
      subject: `🎾 Reserva Confirmada - ${formattedDate}`,
      text: textBody,
      html: htmlBody,
    })

    return NextResponse.json({ success: true, message: 'Email enviado exitosamente' })
  } catch (error) {
    console.error('Error sending confirmation email:', error)
    return NextResponse.json({ error: 'Error al enviar email' }, { status: 500 })
  }
}
