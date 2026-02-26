/**
 * @jest-environment node
 */
// ABOUTME: Integration tests for GET and POST /api/match-posts.
// ABOUTME: Mocks Supabase to test route logic in isolation.
import { GET, POST } from '@/app/api/match-posts/route'
import { NextRequest } from 'next/server'

jest.mock('@/lib/supabase/server', () => ({ createClient: jest.fn() }))
import { createClient } from '@/lib/supabase/server'
const mockCreateClient = createClient as jest.MockedFunction<typeof createClient>

function makeAuth(userId = 'user-1') {
  return { auth: { getUser: jest.fn().mockResolvedValue({ data: { user: { id: userId } }, error: null }) } }
}
function makeNoAuth() {
  return { auth: { getUser: jest.fn().mockResolvedValue({ data: { user: null }, error: new Error('no auth') }) } }
}

describe('GET /api/match-posts', () => {
  it('returns 401 when not authenticated', async () => {
    mockCreateClient.mockResolvedValue({
      ...makeNoAuth(),
      from: jest.fn().mockReturnThis(),
    } as any)
    const res = await GET(new NextRequest('http://localhost/api/match-posts'))
    expect(res.status).toBe(401)
  })

  it('returns 200 with posts array when authenticated', async () => {
    const fromMock = jest.fn().mockReturnValue({
      select: jest.fn().mockReturnThis(),
      eq: jest.fn().mockReturnThis(),
      order: jest.fn().mockResolvedValue({ data: [], error: null }),
    })
    mockCreateClient.mockResolvedValue({ ...makeAuth(), from: fromMock } as any)
    const res = await GET(new NextRequest('http://localhost/api/match-posts'))
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(Array.isArray(body.posts)).toBe(true)
  })
})

describe('POST /api/match-posts', () => {
  it('returns 401 when not authenticated', async () => {
    mockCreateClient.mockResolvedValue({ ...makeNoAuth(), from: jest.fn() } as any)
    const req = new NextRequest('http://localhost/api/match-posts', {
      method: 'POST',
      body: JSON.stringify({ type: 'standing' }),
    })
    expect((await POST(req)).status).toBe(401)
  })

  it('returns 400 for invalid type', async () => {
    mockCreateClient.mockResolvedValue({ ...makeAuth(), from: jest.fn() } as any)
    const req = new NextRequest('http://localhost/api/match-posts', {
      method: 'POST',
      body: JSON.stringify({ type: 'invalid' }),
    })
    expect((await POST(req)).status).toBe(400)
  })

  it('returns 400 for specific type missing date', async () => {
    mockCreateClient.mockResolvedValue({ ...makeAuth(), from: jest.fn() } as any)
    const req = new NextRequest('http://localhost/api/match-posts', {
      method: 'POST',
      body: JSON.stringify({ type: 'specific', hour: 8 }),
    })
    expect((await POST(req)).status).toBe(400)
  })

  it('returns 400 for specific type missing hour', async () => {
    mockCreateClient.mockResolvedValue({ ...makeAuth(), from: jest.fn() } as any)
    const req = new NextRequest('http://localhost/api/match-posts', {
      method: 'POST',
      body: JSON.stringify({ type: 'specific', date: '2026-03-01' }),
    })
    expect((await POST(req)).status).toBe(400)
  })

  it('returns 400 for note longer than 280 chars', async () => {
    mockCreateClient.mockResolvedValue({ ...makeAuth(), from: jest.fn() } as any)
    const req = new NextRequest('http://localhost/api/match-posts', {
      method: 'POST',
      body: JSON.stringify({ type: 'standing', note: 'x'.repeat(281) }),
    })
    expect((await POST(req)).status).toBe(400)
  })

  it('returns 400 for invalid desired_level_tier', async () => {
    mockCreateClient.mockResolvedValue({ ...makeAuth(), from: jest.fn() } as any)
    const req = new NextRequest('http://localhost/api/match-posts', {
      method: 'POST',
      body: JSON.stringify({ type: 'standing', desired_level_tier: 'Maestro' }),
    })
    expect((await POST(req)).status).toBe(400)
  })

  it('returns 403 when profile is not complete', async () => {
    const profileChain = {
      select: jest.fn().mockReturnThis(),
      eq: jest.fn().mockReturnThis(),
      single: jest.fn().mockResolvedValue({ data: { profile_completed: false }, error: null }),
    }
    mockCreateClient.mockResolvedValue({ ...makeAuth(), from: jest.fn().mockReturnValue(profileChain) } as any)
    const req = new NextRequest('http://localhost/api/match-posts', {
      method: 'POST',
      body: JSON.stringify({ type: 'standing' }),
    })
    expect((await POST(req)).status).toBe(403)
  })

  it('returns 201 for valid standing post', async () => {
    const profileChain = {
      select: jest.fn().mockReturnThis(),
      eq: jest.fn().mockReturnThis(),
      single: jest.fn().mockResolvedValue({ data: { profile_completed: true }, error: null }),
    }
    const insertChain = {
      insert: jest.fn().mockReturnThis(),
      select: jest.fn().mockReturnThis(),
      single: jest.fn().mockResolvedValue({
        data: { id: 'post-1', type: 'standing', user_id: 'user-1' },
        error: null,
      }),
    }
    mockCreateClient.mockResolvedValue({
      ...makeAuth(),
      from: jest.fn().mockReturnValueOnce(profileChain).mockReturnValue(insertChain),
    } as any)
    const req = new NextRequest('http://localhost/api/match-posts', {
      method: 'POST',
      body: JSON.stringify({ type: 'standing', note: 'Busco partido' }),
    })
    const res = await POST(req)
    expect(res.status).toBe(201)
    const body = await res.json()
    expect(body.post).toBeDefined()
  })
})
