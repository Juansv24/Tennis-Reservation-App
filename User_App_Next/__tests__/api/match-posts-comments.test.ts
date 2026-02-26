/**
 * @jest-environment node
 */
// ABOUTME: Integration tests for GET and POST /api/match-posts/[id]/comments.
// ABOUTME: Verifies auth, profile completeness gate, comment listing, content validation, and creation.
import { GET, POST } from '@/app/api/match-posts/[id]/comments/route'
import { NextRequest } from 'next/server'

jest.mock('@/lib/supabase/server', () => ({ createClient: jest.fn() }))
import { createClient } from '@/lib/supabase/server'
const mockCreateClient = createClient as jest.MockedFunction<typeof createClient>

const mockContext = (id = 'post-1') => ({ params: Promise.resolve({ id }) })

function makeAuth() {
  return { auth: { getUser: jest.fn().mockResolvedValue({ data: { user: { id: 'user-1' } }, error: null }) } }
}
function makeNoAuth() {
  return { auth: { getUser: jest.fn().mockResolvedValue({ data: { user: null }, error: new Error() }) } }
}

describe('GET /api/match-posts/[id]/comments', () => {
  it('returns 401 when not authenticated', async () => {
    mockCreateClient.mockResolvedValue({ ...makeNoAuth(), from: jest.fn() } as any)
    const res = await GET(new NextRequest('http://localhost/api/match-posts/post-1/comments'), mockContext())
    expect(res.status).toBe(401)
  })

  it('returns 200 with comments array', async () => {
    const chain = {
      select: jest.fn().mockReturnThis(),
      eq: jest.fn().mockReturnThis(),
      order: jest.fn().mockResolvedValue({ data: [], error: null }),
    }
    mockCreateClient.mockResolvedValue({ ...makeAuth(), from: jest.fn().mockReturnValue(chain) } as any)
    const res = await GET(new NextRequest('http://localhost/api/match-posts/post-1/comments'), mockContext())
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(Array.isArray(body.comments)).toBe(true)
  })
})

describe('POST /api/match-posts/[id]/comments', () => {
  it('returns 401 when not authenticated', async () => {
    mockCreateClient.mockResolvedValue({ ...makeNoAuth(), from: jest.fn() } as any)
    const req = new NextRequest('http://localhost/api/match-posts/post-1/comments', {
      method: 'POST', body: JSON.stringify({ content: 'Hola' }),
    })
    expect((await POST(req, mockContext())).status).toBe(401)
  })

  it('returns 400 when content is empty', async () => {
    mockCreateClient.mockResolvedValue({ ...makeAuth(), from: jest.fn() } as any)
    const req = new NextRequest('http://localhost/api/match-posts/post-1/comments', {
      method: 'POST', body: JSON.stringify({ content: '   ' }),
    })
    expect((await POST(req, mockContext())).status).toBe(400)
  })

  it('returns 400 when content exceeds 500 characters', async () => {
    mockCreateClient.mockResolvedValue({ ...makeAuth(), from: jest.fn() } as any)
    const req = new NextRequest('http://localhost/api/match-posts/post-1/comments', {
      method: 'POST', body: JSON.stringify({ content: 'x'.repeat(501) }),
    })
    expect((await POST(req, mockContext())).status).toBe(400)
  })

  it('returns 403 when profile is not complete', async () => {
    const profileChain = {
      select: jest.fn().mockReturnThis(),
      eq: jest.fn().mockReturnThis(),
      single: jest.fn().mockResolvedValue({ data: { profile_completed: false }, error: null }),
    }
    mockCreateClient.mockResolvedValue({ ...makeAuth(), from: jest.fn().mockReturnValue(profileChain) } as any)
    const req = new NextRequest('http://localhost/api/match-posts/post-1/comments', {
      method: 'POST', body: JSON.stringify({ content: 'Hola' }),
    })
    expect((await POST(req, mockContext())).status).toBe(403)
  })

  it('returns 201 with comment on success', async () => {
    const profileChain = {
      select: jest.fn().mockReturnThis(),
      eq: jest.fn().mockReturnThis(),
      single: jest.fn().mockResolvedValue({ data: { profile_completed: true }, error: null }),
    }
    const insertChain = {
      insert: jest.fn().mockReturnThis(),
      select: jest.fn().mockReturnThis(),
      single: jest.fn().mockResolvedValue({ data: { id: 'c-1', content: 'Hola', users: { full_name: 'Test' } }, error: null }),
    }
    mockCreateClient.mockResolvedValue({
      ...makeAuth(),
      from: jest.fn().mockReturnValueOnce(profileChain).mockReturnValue(insertChain),
    } as any)
    const req = new NextRequest('http://localhost/api/match-posts/post-1/comments', {
      method: 'POST', body: JSON.stringify({ content: 'Hola' }),
    })
    const res = await POST(req, mockContext())
    expect(res.status).toBe(201)
    expect((await res.json()).comment).toBeDefined()
  })
})
