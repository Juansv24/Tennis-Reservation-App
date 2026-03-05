/**
 * @jest-environment node
 */
// ABOUTME: Tests for GET /api/messages/[userId] — thread retrieval and mark-as-read.
// ABOUTME: Mocks Supabase to test route logic in isolation.
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
    // mark-read update (fire and forget)
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
