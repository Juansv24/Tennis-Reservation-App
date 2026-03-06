# Direct Messages Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Allow users to send direct messages to recommended players, read conversations in a new "Mensajes" tab, and receive email notifications for new messages.

**Architecture:** Three API routes handle sending/listing conversations/reading threads (all backed by the existing `direct_messages` table). A `MessageCompose` modal is triggered from `PartnerCard`. A new `MessagesTab` component handles conversation list and thread view. `ProfilePageClient` gains a third tab with an unread badge fetched on mount. Email notification fires inline when a message is sent, using the same nodemailer/Gmail setup already in the project.

**Tech Stack:** Next.js App Router API routes, Supabase (session + service-role clients), nodemailer, React state (no new libraries needed).

---

## Context: What Already Exists

- `direct_messages` table — already in DB with correct schema and RLS:
  - Columns: `id, sender_id, recipient_id, content, created_at, read_at`
  - RLS SELECT: sender or recipient only; INSERT: sender only
- `users.notify_messages BOOLEAN DEFAULT TRUE` — already in DB and profile form
- `DirectMessage` type — already in `types/database.types.ts`
- Email: nodemailer + Gmail SMTP via `SMTP_EMAIL`/`SMTP_PASSWORD` env vars
- Service-role admin client pattern: see `app/api/auth/send-verification-email/route.ts`
- Tab routing: `ProfilePageClient` reads `initialTab` prop from `?tab=` URL param

---

## Task 1: Add `Conversation` type

**Files:**
- Modify: `types/database.types.ts`

**Step 1: Add the type**

Open `types/database.types.ts` and add after the `DirectMessage` interface:

```typescript
export interface Conversation {
  other_user: Pick<User, 'id' | 'full_name' | 'level_tier' | 'categoria'>
  last_message: DirectMessage
  unread_count: number
}
```

**Step 2: Commit**

```bash
git add types/database.types.ts
git commit -m "feat: add Conversation type for direct messages"
```

---

## Task 2: `POST /api/messages` — send a message + email notification

**Files:**
- Create: `app/api/messages/route.ts`
- Test: `__tests__/api/messages.test.ts`

**Step 1: Write the failing test**

Create `__tests__/api/messages.test.ts`:

```typescript
import { POST } from '@/app/api/messages/route'
import { NextRequest } from 'next/server'

// Mock Supabase session client
jest.mock('@/lib/supabase/server', () => ({
  createClient: jest.fn(),
}))

// Mock admin client (for recipient email lookup)
jest.mock('@supabase/supabase-js', () => ({
  createClient: jest.fn(),
}))

// Mock nodemailer
jest.mock('nodemailer', () => ({
  createTransport: jest.fn(() => ({
    sendMail: jest.fn().mockResolvedValue({}),
  })),
}))

import { createClient as createSessionClient } from '@/lib/supabase/server'
import { createClient as createAdminClient } from '@supabase/supabase-js'

const mockSessionClient = {
  auth: { getUser: jest.fn() },
  from: jest.fn(),
}
const mockAdminClient = {
  from: jest.fn(),
}

beforeEach(() => {
  jest.clearAllMocks()
  ;(createSessionClient as jest.Mock).mockResolvedValue(mockSessionClient)
  ;(createAdminClient as jest.Mock).mockReturnValue(mockAdminClient)
})

function makeRequest(body: object) {
  return new NextRequest('http://localhost/api/messages', {
    method: 'POST',
    body: JSON.stringify(body),
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('POST /api/messages', () => {
  it('returns 401 when not authenticated', async () => {
    mockSessionClient.auth.getUser.mockResolvedValue({ data: { user: null }, error: new Error('unauth') })
    const res = await POST(makeRequest({ recipient_id: 'abc', content: 'hello' }))
    expect(res.status).toBe(401)
  })

  it('returns 400 when content is empty', async () => {
    mockSessionClient.auth.getUser.mockResolvedValue({ data: { user: { id: 'user1' } }, error: null })
    const res = await POST(makeRequest({ recipient_id: 'abc', content: '' }))
    expect(res.status).toBe(400)
  })

  it('returns 400 when content exceeds 1000 chars', async () => {
    mockSessionClient.auth.getUser.mockResolvedValue({ data: { user: { id: 'user1' } }, error: null })
    const res = await POST(makeRequest({ recipient_id: 'abc', content: 'x'.repeat(1001) }))
    expect(res.status).toBe(400)
  })

  it('returns 400 when sending to yourself', async () => {
    mockSessionClient.auth.getUser.mockResolvedValue({ data: { user: { id: 'user1' } }, error: null })
    const res = await POST(makeRequest({ recipient_id: 'user1', content: 'hi' }))
    expect(res.status).toBe(400)
  })

  it('inserts message and returns 201 on success', async () => {
    mockSessionClient.auth.getUser.mockResolvedValue({ data: { user: { id: 'sender1' } }, error: null })
    const fakeMessage = { id: 'msg1', sender_id: 'sender1', recipient_id: 'recip1', content: 'hi', created_at: 'now', read_at: null }
    mockSessionClient.from.mockReturnValue({
      insert: jest.fn().mockReturnValue({
        select: jest.fn().mockReturnValue({
          single: jest.fn().mockResolvedValue({ data: fakeMessage, error: null }),
        }),
      }),
    })
    // Admin client: recipient lookup
    mockAdminClient.from.mockReturnValue({
      select: jest.fn().mockReturnValue({
        eq: jest.fn().mockReturnValue({
          single: jest.fn().mockResolvedValue({
            data: { email: 'recip@test.com', full_name: 'Recip', notify_messages: false },
            error: null,
          }),
        }),
      }),
    })
    const res = await POST(makeRequest({ recipient_id: 'recip1', content: 'hi' }))
    expect(res.status).toBe(201)
    const body = await res.json()
    expect(body.message.id).toBe('msg1')
  })
})
```

**Step 2: Run test to verify it fails**

```bash
cd "C:\Users\jsval\OneDrive\Documents\Personal\Code\Python Proyects\Tennis-Reservation-App\User_App_Next"
npx jest __tests__/api/messages.test.ts --no-coverage
```

Expected: FAIL — `Cannot find module '@/app/api/messages/route'`

**Step 3: Implement `POST /api/messages`**

Create `app/api/messages/route.ts`:

```typescript
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
        Puedes desactivar estas notificaciones en tu <a href="${process.env.NEXT_PUBLIC_APP_URL}/profile" style="color:#2478CC;">pagina de perfil</a>.
      </p>
    </div>
    <div class="footer">
      <p>${process.env.NEXT_PUBLIC_COURT_NAME}</p>
      <p>Esta es una notificacion automatizada. Por favor no respondas a este email.</p>
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
```

**Step 4: Run tests and verify they pass**

```bash
npx jest __tests__/api/messages.test.ts --no-coverage
```

Expected: all tests PASS

**Step 5: Commit**

```bash
git add app/api/messages/route.ts __tests__/api/messages.test.ts
git commit -m "feat: POST /api/messages with email notification"
```

---

## Task 3: `GET /api/messages` — list conversations

**Files:**
- Modify: `app/api/messages/route.ts` (add `GET` export)

**Step 1: Add conversation-fetching test cases to the existing test file**

Open `__tests__/api/messages.test.ts` and add at the end:

```typescript
import { GET } from '@/app/api/messages/route'

describe('GET /api/messages', () => {
  it('returns 401 when not authenticated', async () => {
    mockSessionClient.auth.getUser.mockResolvedValue({ data: { user: null }, error: new Error('unauth') })
    const req = new NextRequest('http://localhost/api/messages')
    const res = await GET(req)
    expect(res.status).toBe(401)
  })

  it('returns conversations array on success', async () => {
    mockSessionClient.auth.getUser.mockResolvedValue({ data: { user: { id: 'user1' } }, error: null })

    // messages query
    mockSessionClient.from.mockReturnValueOnce({
      select: jest.fn().mockReturnValue({
        or: jest.fn().mockReturnValue({
          order: jest.fn().mockResolvedValue({
            data: [
              { id: 'm1', sender_id: 'user2', recipient_id: 'user1', content: 'hi', created_at: '2026-01-01', read_at: null },
            ],
            error: null,
          }),
        }),
      }),
    })
    // users query
    mockSessionClient.from.mockReturnValueOnce({
      select: jest.fn().mockReturnValue({
        in: jest.fn().mockResolvedValue({
          data: [{ id: 'user2', full_name: 'Ana', level_tier: 'Intermedio', categoria: 'Tercera' }],
          error: null,
        }),
      }),
    })

    const req = new NextRequest('http://localhost/api/messages')
    const res = await GET(req)
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.conversations).toHaveLength(1)
    expect(body.conversations[0].other_user.id).toBe('user2')
    expect(body.conversations[0].unread_count).toBe(1)
  })
})
```

**Step 2: Run to verify new tests fail**

```bash
npx jest __tests__/api/messages.test.ts --no-coverage
```

Expected: the two new GET tests FAIL — `GET is not a function`

**Step 3: Add the `GET` handler to `app/api/messages/route.ts`**

Append this export to the end of `app/api/messages/route.ts`:

```typescript
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
```

**Step 4: Run tests and verify all pass**

```bash
npx jest __tests__/api/messages.test.ts --no-coverage
```

Expected: all tests PASS

**Step 5: Commit**

```bash
git add app/api/messages/route.ts __tests__/api/messages.test.ts
git commit -m "feat: GET /api/messages returns grouped conversations"
```

---

## Task 4: `GET /api/messages/[userId]` — thread + mark as read

**Files:**
- Create: `app/api/messages/[userId]/route.ts`
- Test: `__tests__/api/messages-thread.test.ts`

**Step 1: Write the failing tests**

Create `__tests__/api/messages-thread.test.ts`:

```typescript
import { GET } from '@/app/api/messages/[userId]/route'
import { NextRequest } from 'next/server'

jest.mock('@/lib/supabase/server', () => ({ createClient: jest.fn() }))

import { createClient } from '@/lib/supabase/server'

const mockClient = {
  auth: { getUser: jest.fn() },
  from: jest.fn(),
}
beforeEach(() => {
  jest.clearAllMocks()
  ;(createClient as jest.Mock).mockResolvedValue(mockClient)
})

function makeRequest(userId: string) {
  return new NextRequest(`http://localhost/api/messages/${userId}`)
}

describe('GET /api/messages/[userId]', () => {
  it('returns 401 when not authenticated', async () => {
    mockClient.auth.getUser.mockResolvedValue({ data: { user: null }, error: new Error() })
    const res = await GET(makeRequest('other1'), { params: Promise.resolve({ userId: 'other1' }) })
    expect(res.status).toBe(401)
  })

  it('returns messages between two users in chronological order', async () => {
    mockClient.auth.getUser.mockResolvedValue({ data: { user: { id: 'me' } }, error: null })

    const fakeMessages = [
      { id: 'm1', sender_id: 'me', recipient_id: 'other1', content: 'hello', created_at: '2026-01-01T10:00:00Z', read_at: null },
      { id: 'm2', sender_id: 'other1', recipient_id: 'me', content: 'hi back', created_at: '2026-01-01T10:01:00Z', read_at: null },
    ]

    // messages select
    mockClient.from.mockReturnValueOnce({
      select: jest.fn().mockReturnValue({
        or: jest.fn().mockReturnValue({
          order: jest.fn().mockResolvedValue({ data: fakeMessages, error: null }),
        }),
      }),
    })
    // mark-read update (fire and forget, don't need result)
    mockClient.from.mockReturnValueOnce({
      update: jest.fn().mockReturnValue({
        eq: jest.fn().mockReturnValue({
          eq: jest.fn().mockReturnValue({
            is: jest.fn().mockResolvedValue({ error: null }),
          }),
        }),
      }),
    })

    const res = await GET(makeRequest('other1'), { params: Promise.resolve({ userId: 'other1' }) })
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.messages).toHaveLength(2)
    expect(body.messages[0].id).toBe('m1')
  })
})
```

**Step 2: Run to verify failure**

```bash
npx jest __tests__/api/messages-thread.test.ts --no-coverage
```

Expected: FAIL — `Cannot find module '@/app/api/messages/[userId]/route'`

**Step 3: Implement the route**

Create `app/api/messages/[userId]/route.ts`:

```typescript
// ABOUTME: API route for reading a message thread with a specific user and marking messages as read.
// ABOUTME: GET fetches all messages between current user and [userId], marks received ones as read.
import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ userId: string }> }
) {
  const supabase = await createClient()
  const { data: { user }, error: authError } = await supabase.auth.getUser()
  if (authError || !user) return NextResponse.json({ error: 'No autenticado' }, { status: 401 })

  const { userId: otherId } = await params

  const { data: messages, error } = await supabase
    .from('direct_messages')
    .select('*')
    .or(
      `and(sender_id.eq.${user.id},recipient_id.eq.${otherId}),` +
      `and(sender_id.eq.${otherId},recipient_id.eq.${user.id})`
    )
    .order('created_at', { ascending: true })

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })

  // Mark unread messages sent to current user as read (fire and forget)
  supabase
    .from('direct_messages')
    .update({ read_at: new Date().toISOString() })
    .eq('sender_id', otherId)
    .eq('recipient_id', user.id)
    .is('read_at', null)

  return NextResponse.json({ messages: messages || [] })
}
```

**Step 4: Run tests and verify they pass**

```bash
npx jest __tests__/api/messages-thread.test.ts --no-coverage
```

Expected: all tests PASS

**Step 5: Commit**

```bash
git add app/api/messages/[userId]/route.ts __tests__/api/messages-thread.test.ts
git commit -m "feat: GET /api/messages/[userId] returns thread and marks as read"
```

---

## Task 5: `MessageCompose` modal component

**Files:**
- Create: `components/profile/MessageCompose.tsx`

**Step 1: Create the component**

```typescript
// ABOUTME: Modal for composing and sending a direct message to a specific user.
// ABOUTME: Calls POST /api/messages. Calls onSent() on success, onClose() on cancel.
'use client'

import { useState } from 'react'

interface Props {
  recipientId: string
  recipientName: string
  onClose: () => void
  onSent: () => void
}

export default function MessageCompose({ recipientId, recipientName, onClose, onSent }: Props) {
  const [content, setContent] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!content.trim()) return
    setSending(true)
    setError('')

    const res = await fetch('/api/messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ recipient_id: recipientId, content }),
    })

    setSending(false)
    if (res.ok) {
      onSent()
    } else {
      const data = await res.json()
      setError(data.error || 'Error al enviar')
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 space-y-4">
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-semibold text-us-open-blue">
            Mensaje a {recipientName}
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl leading-none"
            aria-label="Cerrar"
          >
            &times;
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <textarea
            value={content}
            onChange={e => setContent(e.target.value)}
            maxLength={1000}
            rows={4}
            placeholder="Escribe tu mensaje..."
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-us-open-light-blue resize-none"
            autoFocus
          />
          <p className="text-xs text-gray-400 text-right">{content.length}/1000</p>

          {error && <p className="text-red-600 text-sm">{error}</p>}

          <div className="flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={sending || !content.trim()}
              className="flex-1 py-2 bg-us-open-blue text-white rounded-lg text-sm font-semibold hover:bg-us-open-light-blue transition-colors disabled:opacity-50"
            >
              {sending ? 'Enviando...' : 'Enviar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
```

**Step 2: Commit**

```bash
git add components/profile/MessageCompose.tsx
git commit -m "feat: MessageCompose modal component"
```

---

## Task 6: Update `PartnerCard` to add "Enviar mensaje" button

**Files:**
- Modify: `components/profile/PartnerCard.tsx`

**Step 1: Update the component**

Replace the full content of `components/profile/PartnerCard.tsx` with:

```typescript
// ABOUTME: Displays a single suggested partner card with level badge and schedule overlap message.
// ABOUTME: Shows player name, level/category, compatibility badge, overlap message, and message button.
'use client'

import { useState } from 'react'
import type { SuggestedPartner } from '@/types/database.types'
import MessageCompose from './MessageCompose'

interface Props {
  partner: SuggestedPartner
}

export default function PartnerCard({ partner }: Props) {
  const { user, badge, overlapMessage } = partner
  const [composing, setComposing] = useState(false)
  const [sent, setSent] = useState(false)

  function handleSent() {
    setComposing(false)
    setSent(true)
  }

  return (
    <>
      <div className="p-4 border border-gray-200 rounded-lg bg-white space-y-2">
        <p className="font-medium text-gray-900">{user.full_name}</p>
        <p className="text-sm text-gray-500">
          {user.level_tier ?? '—'}{user.categoria ? ` / ${user.categoria}` : ''}
        </p>
        <span className={`inline-block text-xs font-medium px-2 py-0.5 rounded-full ${
          badge === 'nivel+horario'
            ? 'bg-green-100 text-green-700'
            : 'bg-blue-100 text-blue-700'
        }`}>
          {badge === 'nivel+horario' ? 'Nivel + horario' : 'Coincidencia en nivel'}
        </span>
        {overlapMessage && (
          <p className="text-xs text-gray-500 italic">{overlapMessage}</p>
        )}
        <div className="pt-1">
          {sent ? (
            <p className="text-xs text-green-600 font-medium">Mensaje enviado</p>
          ) : (
            <button
              onClick={() => setComposing(true)}
              className="text-xs font-medium text-us-open-light-blue hover:underline"
            >
              Enviar mensaje
            </button>
          )}
        </div>
      </div>

      {composing && (
        <MessageCompose
          recipientId={user.id}
          recipientName={user.full_name}
          onClose={() => setComposing(false)}
          onSent={handleSent}
        />
      )}
    </>
  )
}
```

**Step 2: Commit**

```bash
git add components/profile/PartnerCard.tsx
git commit -m "feat: add send message button to PartnerCard"
```

---

## Task 7: `MessagesTab` component

**Files:**
- Create: `components/profile/MessagesTab.tsx`

**Step 1: Create the component**

```typescript
// ABOUTME: Messages tab — shows conversation list and in-tab thread view.
// ABOUTME: Fetches GET /api/messages on mount. Clicking a conversation loads the thread.
'use client'

import { useState, useEffect, useRef } from 'react'
import type { Conversation, DirectMessage } from '@/types/database.types'
import MessageCompose from './MessageCompose'

function formatTime(iso: string): string {
  const d = new Date(iso)
  const now = new Date()
  const isToday = d.toDateString() === now.toDateString()
  if (isToday) {
    return d.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit', hour12: true })
  }
  return d.toLocaleDateString('es-CO', { day: 'numeric', month: 'short' })
}

interface Props {
  currentUserId: string
}

export default function MessagesTab({ currentUserId }: Props) {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [loading, setLoading] = useState(true)
  const [activeConv, setActiveConv] = useState<Conversation | null>(null)
  const [thread, setThread] = useState<DirectMessage[]>([])
  const [loadingThread, setLoadingThread] = useState(false)
  const [composingNew, setComposingNew] = useState(false)
  const threadBottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetchConversations()
  }, [])

  useEffect(() => {
    threadBottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [thread])

  async function fetchConversations() {
    setLoading(true)
    const res = await fetch('/api/messages')
    if (res.ok) {
      const data = await res.json()
      setConversations(data.conversations || [])
    }
    setLoading(false)
  }

  async function openConversation(conv: Conversation) {
    setActiveConv(conv)
    setLoadingThread(true)
    const res = await fetch(`/api/messages/${conv.other_user.id}`)
    if (res.ok) {
      const data = await res.json()
      setThread(data.messages || [])
      // Clear unread badge locally
      setConversations(prev =>
        prev.map(c => c.other_user.id === conv.other_user.id ? { ...c, unread_count: 0 } : c)
      )
    }
    setLoadingThread(false)
  }

  function handleReplySent() {
    if (activeConv) openConversation(activeConv)
    setComposingNew(false)
  }

  if (loading) {
    return <p className="text-sm text-gray-500">Cargando mensajes...</p>
  }

  // Thread view
  if (activeConv) {
    return (
      <div className="space-y-4">
        <button
          onClick={() => { setActiveConv(null); setThread([]) }}
          className="text-sm text-us-open-light-blue hover:underline"
        >
          &larr; Volver a conversaciones
        </button>

        <div className="flex items-center justify-between">
          <div>
            <p className="font-semibold text-us-open-blue">{activeConv.other_user.full_name}</p>
            <p className="text-xs text-gray-500">
              {activeConv.other_user.level_tier ?? '—'}
              {activeConv.other_user.categoria ? ` / ${activeConv.other_user.categoria}` : ''}
            </p>
          </div>
          <button
            onClick={() => setComposingNew(true)}
            className="px-3 py-1.5 text-xs bg-us-open-blue text-white rounded-lg font-medium hover:bg-us-open-light-blue transition-colors"
          >
            Responder
          </button>
        </div>

        <div className="border border-gray-200 rounded-lg bg-gray-50 p-4 space-y-3 max-h-96 overflow-y-auto">
          {loadingThread ? (
            <p className="text-sm text-gray-400 text-center">Cargando...</p>
          ) : thread.length === 0 ? (
            <p className="text-sm text-gray-400 text-center">Sin mensajes aun.</p>
          ) : (
            thread.map(msg => {
              const isMe = msg.sender_id === currentUserId
              return (
                <div key={msg.id} className={`flex ${isMe ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-xs px-3 py-2 rounded-xl text-sm ${
                    isMe
                      ? 'bg-us-open-blue text-white'
                      : 'bg-white border border-gray-200 text-gray-800'
                  }`}>
                    <p>{msg.content}</p>
                    <p className={`text-xs mt-1 ${isMe ? 'text-blue-200' : 'text-gray-400'}`}>
                      {formatTime(msg.created_at)}
                    </p>
                  </div>
                </div>
              )
            })
          )}
          <div ref={threadBottomRef} />
        </div>

        {composingNew && (
          <MessageCompose
            recipientId={activeConv.other_user.id}
            recipientName={activeConv.other_user.full_name}
            onClose={() => setComposingNew(false)}
            onSent={handleReplySent}
          />
        )}
      </div>
    )
  }

  // Conversation list view
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-us-open-blue">Mensajes</h3>

      {conversations.length === 0 ? (
        <p className="text-sm text-gray-500">
          Aun no tienes mensajes. Puedes escribirle a un jugador desde la pestana Comunidad.
        </p>
      ) : (
        <div className="space-y-2">
          {conversations.map(conv => (
            <button
              key={conv.other_user.id}
              onClick={() => openConversation(conv)}
              className="w-full text-left p-4 border border-gray-200 rounded-lg bg-white hover:bg-gray-50 transition-colors space-y-0.5"
            >
              <div className="flex justify-between items-start">
                <p className={`font-medium text-gray-900 ${conv.unread_count > 0 ? 'font-semibold' : ''}`}>
                  {conv.other_user.full_name}
                </p>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <span className="text-xs text-gray-400">
                    {formatTime(conv.last_message.created_at)}
                  </span>
                  {conv.unread_count > 0 && (
                    <span className="bg-us-open-light-blue text-white text-xs font-bold px-1.5 py-0.5 rounded-full">
                      {conv.unread_count}
                    </span>
                  )}
                </div>
              </div>
              <p className="text-sm text-gray-500 truncate">{conv.last_message.content}</p>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
```

**Step 2: Commit**

```bash
git add components/profile/MessagesTab.tsx
git commit -m "feat: MessagesTab with conversation list and thread view"
```

---

## Task 8: Wire up the Messages tab in `ProfilePageClient`

**Files:**
- Modify: `components/profile/ProfilePageClient.tsx`

**Step 1: Update the component**

Replace the full content of `components/profile/ProfilePageClient.tsx` with:

```typescript
// ABOUTME: Client root for the /profile page — manages tab state and profile refresh.
// ABOUTME: Renders Mi Perfil, Comunidad, or Mensajes tab. Fetches unread count for badge.
'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import type { User, SuggestedPartner } from '@/types/database.types'
import ProfileForm from './ProfileForm'
import ComunidadTab from './ComunidadTab'
import MessagesTab from './MessagesTab'

interface Props {
  profile: User
  initialTab?: string
  suggestions: SuggestedPartner[]
}

export default function ProfilePageClient({ profile: initialProfile, initialTab, suggestions }: Props) {
  const [profile, setProfile] = useState(initialProfile)
  const [unreadCount, setUnreadCount] = useState(0)

  useEffect(() => {
    fetch('/api/messages')
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data) setUnreadCount(data.totalUnread) })
      .catch(() => {})
  }, [])

  async function handleProfileSaved() {
    const res = await fetch('/api/profile')
    if (res.ok) {
      const data = await res.json()
      setProfile(data.profile)
    }
  }

  const tab = initialTab ?? 'perfil'

  return (
    <div>
      {/* Tab navigation */}
      <div className="flex gap-1 mb-6 border-b border-gray-200">
        {[
          { key: 'perfil', label: 'Mi Perfil', href: '/profile' },
          { key: 'comunidad', label: 'Comunidad', href: '/profile?tab=comunidad' },
          { key: 'mensajes', label: 'Mensajes', href: '/profile?tab=mensajes' },
        ].map(t => (
          <Link
            key={t.key}
            href={t.href}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
              tab === t.key
                ? 'border-us-open-blue text-us-open-blue'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {t.label}
            {t.key === 'mensajes' && unreadCount > 0 && (
              <span className="bg-us-open-light-blue text-white text-xs font-bold px-1.5 py-0.5 rounded-full">
                {unreadCount}
              </span>
            )}
          </Link>
        ))}
      </div>

      {tab === 'comunidad' && (
        <ComunidadTab suggestions={suggestions} currentUserId={profile.id} />
      )}

      {tab === 'mensajes' && (
        <MessagesTab currentUserId={profile.id} />
      )}

      {tab === 'perfil' && (
        <>
          <div className="bg-blue-50 border-2 border-us-open-light-blue rounded-lg p-5 shadow-sm mb-6">
            <h3 className="text-base font-semibold text-us-open-blue mb-2">Para que sirve completar tu perfil?</h3>
            <ul className="space-y-1.5 text-sm text-gray-700">
              <li>Aparecer como <strong>companhero sugerido</strong> para jugadores de tu nivel en la pestana Comunidad.</li>
              <li>Poder <strong>publicar y comentar</strong> en los posts de "Buscando partido" en la pestana Comunidad para coordinar partidos con otros jugadores registrados.</li>
              <li>El sistema encontrara jugadores con <strong>niveles y horarios compatibles</strong> con los tuyos basandose en tu historial de reservas.</li>
            </ul>
          </div>
          <ProfileForm user={profile} onSaved={handleProfileSaved} />
        </>
      )}
    </div>
  )
}
```

**Step 2: Commit**

```bash
git add components/profile/ProfilePageClient.tsx
git commit -m "feat: add Mensajes tab with unread badge to ProfilePageClient"
```

---

## Task 9: Run full test suite and verify no regressions

**Step 1: Run all tests**

```bash
npx jest --no-coverage
```

Expected: all existing tests plus the new ones PASS

**Step 2: Start dev server and manually verify**

```bash
npm run dev
```

Check:
1. `/profile` — three tabs visible (Mi Perfil, Comunidad, Mensajes)
2. Comunidad tab — each PartnerCard has "Enviar mensaje" button
3. Click "Enviar mensaje" — modal opens, can type and send
4. After sending — "Mensaje enviado" confirmation on card
5. Mensajes tab — shows conversations list (or empty state)
6. Click a conversation — thread opens with bubble layout
7. Click "Responder" — modal opens
8. Unread badge appears on Mensajes tab after receiving a message

**Step 3: Final commit if any tweaks were needed**

```bash
git add -A
git commit -m "feat: direct messages — PartnerCard button, MessagesTab, email notification"
```
