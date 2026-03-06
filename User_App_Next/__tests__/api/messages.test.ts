/**
 * @jest-environment node
 */
import { POST, GET } from '@/app/api/messages/route'
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
