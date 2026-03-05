// ABOUTME: API route for sending direct messages and listing conversations.
// ABOUTME: POST sends a message and fires an email notification if recipient opted in.
// ABOUTME: GET returns all conversations for the current user (grouped by other party).
import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'
import { createClient as createAdminClient } from '@supabase/supabase-js'
import nodemailer from 'nodemailer'

function makeAdminClient() {
  return createAdminClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    { auth: { autoRefreshToken: false, persistSession: false } }
  )
}

export async function POST(request: NextRequest) {
  const supabase = await createClient()
  const { data: { user }, error: authError } = await supabase.auth.getUser()
  if (authError || !user) return NextResponse.json({ error: 'No autenticado' }, { status: 401 })

  const { recipient_id, content } = await request.json()

  if (!recipient_id || typeof recipient_id !== 'string') {
    return NextResponse.json({ error: 'Destinatario requerido' }, { status: 400 })
  }
  if (recipient_id === user.id) {
    return NextResponse.json({ error: 'No puedes enviarte mensajes a ti mismo' }, { status: 400 })
  }
  if (!content || typeof content !== 'string' || content.trim().length === 0) {
    return NextResponse.json({ error: 'El mensaje no puede estar vacío' }, { status: 400 })
  }
  if (content.length > 1000) {
    return NextResponse.json({ error: 'El mensaje no puede superar 1000 caracteres' }, { status: 400 })
  }

  const { data: message, error } = await supabase
    .from('direct_messages')
    .insert({ sender_id: user.id, recipient_id, content: content.trim() })
    .select()
    .single()

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })

  // Email notification (fire and forget — don't fail the request if email fails)
  sendNotificationEmail(user.id, recipient_id, content.trim()).catch(err =>
    console.error('Error sending message notification email:', err)
  )

  return NextResponse.json({ message }, { status: 201 })
}

async function sendNotificationEmail(senderId: string, recipientId: string, content: string) {
  const admin = makeAdminClient()

  const [senderResult, recipientResult] = await Promise.all([
    admin.from('users').select('full_name').eq('id', senderId).single(),
    admin.from('users').select('email, full_name, notify_messages').eq('id', recipientId).single(),
  ])

  if (senderResult.error || recipientResult.error) return
  const { full_name: senderName } = senderResult.data
  const { email: recipientEmail, full_name: recipientName, notify_messages } = recipientResult.data

  if (!notify_messages) return

  const messagesUrl = `${process.env.NEXT_PUBLIC_APP_URL}/profile?tab=mensajes`
  const preview = content.length > 120 ? content.slice(0, 120) + '...' : content

  const transporter = nodemailer.createTransport({
    host: 'smtp.gmail.com',
    port: 587,
    secure: false,
    auth: { user: process.env.SMTP_EMAIL, pass: process.env.SMTP_PASSWORD },
  })

  const html = `<!DOCTYPE html>
<html>
<head>
  <style>
    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
    .header { background: linear-gradient(135deg, #001854 0%, #2478CC 100%); color: white; padding: 30px; text-align: center; border-radius: 10px; }
    .content { background: #f9f9f9; padding: 30px; border-radius: 10px; margin: 20px 0; }
    .message-preview { background: white; padding: 20px; border-radius: 8px; border-left: 5px solid #FFD400; margin: 20px 0; font-style: italic; color: #444; }
    .cta-button { background: #001854; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 20px 0; font-weight: bold; }
    .footer { text-align: center; color: #666; font-size: 14px; margin-top: 30px; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Nuevo mensaje</h1>
      <p style="margin:0;font-size:16px;">${process.env.NEXT_PUBLIC_COURT_NAME}</p>
    </div>
    <div class="content">
      <h2>Hola ${recipientName},</h2>
      <p><strong>${senderName}</strong> te ha enviado un mensaje:</p>
      <div class="message-preview">"${preview}"</div>
      <p style="text-align:center;">
        <a href="${messagesUrl}" class="cta-button">Ver mensaje</a>
      </p>
      <p style="font-size:12px;color:#666;text-align:center;">
        Puedes desactivar estas notificaciones en tu <a href="${process.env.NEXT_PUBLIC_APP_URL}/profile" style="color:#2478CC;">página de perfil</a>.
      </p>
    </div>
    <div class="footer">
      <p>${process.env.NEXT_PUBLIC_COURT_NAME}</p>
      <p>Esta es una notificación automática. Por favor no respondas a este email.</p>
    </div>
  </div>
</body>
</html>`

  await transporter.sendMail({
    from: `"${process.env.NEXT_PUBLIC_COURT_NAME}" <${process.env.SMTP_EMAIL}>`,
    to: recipientEmail,
    subject: `Nuevo mensaje de ${senderName} - ${process.env.NEXT_PUBLIC_COURT_NAME}`,
    text: `Hola ${recipientName},\n\n${senderName} te ha enviado un mensaje:\n\n"${preview}"\n\nVer mensaje: ${messagesUrl}\n\n---\n${process.env.NEXT_PUBLIC_COURT_NAME}`,
    html,
  })
}

export async function GET(_request: NextRequest) {
  const supabase = await createClient()
  const { data: { user }, error: authError } = await supabase.auth.getUser()
  if (authError || !user) return NextResponse.json({ error: 'No autenticado' }, { status: 401 })

  // Fetch all messages where user is sender or recipient, newest first
  const { data: messages, error } = await supabase
    .from('direct_messages')
    .select('*')
    .or(`sender_id.eq.${user.id},recipient_id.eq.${user.id}`)
    .order('created_at', { ascending: false })

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })

  // Group into conversations keyed by the "other" user's id
  const convMap = new Map<string, { lastMessage: typeof messages[0]; unreadCount: number }>()
  for (const msg of (messages || [])) {
    const otherId = msg.sender_id === user.id ? msg.recipient_id : msg.sender_id
    if (!convMap.has(otherId)) {
      convMap.set(otherId, { lastMessage: msg, unreadCount: 0 })
    }
    // Count unread: messages sent TO me that I haven't read
    if (msg.recipient_id === user.id && !msg.read_at) {
      convMap.get(otherId)!.unreadCount++
    }
  }

  if (convMap.size === 0) return NextResponse.json({ conversations: [], totalUnread: 0 })

  // Fetch other users' profiles
  const otherIds = [...convMap.keys()]
  const { data: otherUsers } = await supabase
    .from('users')
    .select('id, full_name, level_tier, categoria')
    .in('id', otherIds)

  const userMap = new Map((otherUsers || []).map(u => [u.id, u]))

  const conversations = otherIds
    .filter(id => userMap.has(id))
    .map(id => ({
      other_user: userMap.get(id)!,
      last_message: convMap.get(id)!.lastMessage,
      unread_count: convMap.get(id)!.unreadCount,
    }))
    // Sort by last message date, newest first
    .sort((a, b) =>
      new Date(b.last_message.created_at).getTime() - new Date(a.last_message.created_at).getTime()
    )

  const totalUnread = conversations.reduce((sum, c) => sum + c.unread_count, 0)

  return NextResponse.json({ conversations, totalUnread })
}
