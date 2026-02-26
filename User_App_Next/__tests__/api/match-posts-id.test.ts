/**
 * @jest-environment node
 */
// ABOUTME: Integration tests for DELETE /api/match-posts/[id].
// ABOUTME: Verifies auth check, ownership check, and soft delete.
import { DELETE } from '@/app/api/match-posts/[id]/route'
import { NextRequest } from 'next/server'

jest.mock('@/lib/supabase/server', () => ({ createClient: jest.fn() }))
import { createClient } from '@/lib/supabase/server'
const mockCreateClient = createClient as jest.MockedFunction<typeof createClient>

const mockContext = (id = 'post-1') => ({ params: Promise.resolve({ id }) })

function makeSupabase(overrides: Partial<{
  auth: object
  from: jest.Mock
  select: jest.Mock
  eq: jest.Mock
  single: jest.Mock
  update: jest.Mock
}> = {}) {
  return {
    auth: { getUser: jest.fn().mockResolvedValue({ data: { user: { id: 'user-1' } }, error: null }) },
    from: jest.fn().mockReturnThis(),
    select: jest.fn().mockReturnThis(),
    eq: jest.fn().mockReturnThis(),
    single: jest.fn().mockResolvedValue({ data: { user_id: 'user-1' }, error: null }),
    update: jest.fn().mockReturnThis(),
    ...overrides,
  }
}

describe('DELETE /api/match-posts/[id]', () => {
  it('returns 401 when not authenticated', async () => {
    const mock = makeSupabase()
    mock.auth = { getUser: jest.fn().mockResolvedValue({ data: { user: null }, error: new Error('no auth') }) }
    mockCreateClient.mockResolvedValue(mock as any)
    const res = await DELETE(new NextRequest('http://localhost/api/match-posts/post-1', { method: 'DELETE' }), mockContext())
    expect(res.status).toBe(401)
  })

  it('returns 404 when post not found', async () => {
    const mock = makeSupabase()
    mock.single = jest.fn().mockResolvedValue({ data: null, error: null })
    mockCreateClient.mockResolvedValue(mock as any)
    const res = await DELETE(new NextRequest('http://localhost/api/match-posts/post-1', { method: 'DELETE' }), mockContext())
    expect(res.status).toBe(404)
  })

  it('returns 403 when user is not the post owner', async () => {
    const mock = makeSupabase()
    mock.single = jest.fn().mockResolvedValue({ data: { user_id: 'other-user' }, error: null })
    mockCreateClient.mockResolvedValue(mock as any)
    const res = await DELETE(new NextRequest('http://localhost/api/match-posts/post-1', { method: 'DELETE' }), mockContext())
    expect(res.status).toBe(403)
  })

  it('returns 200 on successful soft delete', async () => {
    const updateChain = { eq: jest.fn().mockResolvedValue({ error: null }) }
    const mock = makeSupabase()
    mock.update = jest.fn().mockReturnValue(updateChain)
    mockCreateClient.mockResolvedValue(mock as any)
    const res = await DELETE(new NextRequest('http://localhost/api/match-posts/post-1', { method: 'DELETE' }), mockContext())
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body).toEqual({ success: true })
    expect(mock.update).toHaveBeenCalledWith({ is_active: false })
    expect(updateChain.eq).toHaveBeenCalledWith('id', 'post-1')
  })
})
