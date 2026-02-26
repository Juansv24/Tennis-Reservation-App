/**
 * @jest-environment node
 */
// ABOUTME: Integration tests for the /api/profile GET and PUT routes.
// ABOUTME: Mocks Supabase client to test route logic in isolation.
import { GET, PUT } from '@/app/api/profile/route'
import { NextRequest } from 'next/server'

jest.mock('@/lib/supabase/server', () => ({
  createClient: jest.fn(),
}))

import { createClient } from '@/lib/supabase/server'
const mockCreateClient = createClient as jest.MockedFunction<typeof createClient>

function makeSupabaseMock(overrides: Record<string, any> = {}) {
  const updateChain = { eq: jest.fn().mockResolvedValue({ error: null }) }
  return {
    auth: { getUser: jest.fn().mockResolvedValue({ data: { user: { id: 'user-1' } }, error: null }) },
    from: jest.fn().mockReturnThis(),
    select: jest.fn().mockReturnThis(),
    eq: jest.fn().mockReturnThis(),
    single: jest.fn().mockResolvedValue({ data: { id: 'user-1', full_name: 'Test', profile_completed: false }, error: null }),
    update: jest.fn().mockReturnValue(updateChain),
    ...overrides,
  }
}

describe('GET /api/profile', () => {
  it('returns 401 when not authenticated', async () => {
    const mock = makeSupabaseMock()
    mock.auth = { getUser: jest.fn().mockResolvedValue({ data: { user: null }, error: new Error('no auth') }) }
    mockCreateClient.mockResolvedValue(mock as any)
    const res = await GET(new NextRequest('http://localhost/api/profile'))
    expect(res.status).toBe(401)
  })

  it('returns 200 with profile when authenticated', async () => {
    mockCreateClient.mockResolvedValue(makeSupabaseMock() as any)
    const res = await GET(new NextRequest('http://localhost/api/profile'))
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.profile).toBeDefined()
  })
})

describe('PUT /api/profile', () => {
  it('returns 401 when not authenticated', async () => {
    const mock = makeSupabaseMock()
    mock.auth = { getUser: jest.fn().mockResolvedValue({ data: { user: null }, error: new Error('no auth') }) }
    mockCreateClient.mockResolvedValue(mock as any)
    const req = new NextRequest('http://localhost/api/profile', {
      method: 'PUT',
      body: JSON.stringify({ level_tier: 'Intermedio' }),
    })
    const res = await PUT(req)
    expect(res.status).toBe(401)
  })

  it('returns 400 for invalid level_tier', async () => {
    mockCreateClient.mockResolvedValue(makeSupabaseMock() as any)
    const req = new NextRequest('http://localhost/api/profile', {
      method: 'PUT',
      body: JSON.stringify({ level_tier: 'Maestro' }),
    })
    const res = await PUT(req)
    expect(res.status).toBe(400)
  })

  it('returns 400 for invalid gender', async () => {
    mockCreateClient.mockResolvedValue(makeSupabaseMock() as any)
    const req = new NextRequest('http://localhost/api/profile', {
      method: 'PUT',
      body: JSON.stringify({ gender: 'alien' }),
    })
    const res = await PUT(req)
    expect(res.status).toBe(400)
  })

  it('returns 400 for invalid age', async () => {
    mockCreateClient.mockResolvedValue(makeSupabaseMock() as any)
    const req = new NextRequest('http://localhost/api/profile', {
      method: 'PUT',
      body: JSON.stringify({ age: 200 }),
    })
    const res = await PUT(req)
    expect(res.status).toBe(400)
  })

  it('returns 200 on valid input', async () => {
    mockCreateClient.mockResolvedValue(makeSupabaseMock() as any)
    const req = new NextRequest('http://localhost/api/profile', {
      method: 'PUT',
      body: JSON.stringify({ level_tier: 'Intermedio', gender: 'masculino', age: 30 }),
    })
    const res = await PUT(req)
    expect(res.status).toBe(200)
  })
})
