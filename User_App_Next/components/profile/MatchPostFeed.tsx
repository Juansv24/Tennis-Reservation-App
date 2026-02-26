// ABOUTME: Displays the match post feed with expandable comment threads.
// ABOUTME: Each post can be deleted by its author. Comments load on expand.
'use client'

import { useState } from 'react'
import type { MatchPostWithCount, MatchPostComment } from '@/types/database.types'

interface FeedProps {
  posts: MatchPostWithCount[]
  loading: boolean
  currentUserId: string
  onDeleted: (id: string) => void
}

export default function MatchPostFeed({ posts, loading, currentUserId, onDeleted }: FeedProps) {
  if (loading) return <p className="text-sm text-gray-500">Cargando publicaciones...</p>
  if (posts.length === 0) return (
    <p className="text-sm text-gray-500">
      No hay publicaciones aún. ¡Sé el primero en buscar un partido!
    </p>
  )
  return (
    <div className="space-y-4">
      {posts.map(post => (
        <PostCard key={post.id} post={post} currentUserId={currentUserId} onDeleted={onDeleted} />
      ))}
    </div>
  )
}

function formatPostDate(dateStr: string, hour: number): string {
  const d = new Date(dateStr + 'T12:00:00')
  const DAYS = ['domingo', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado']
  const MONTHS = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
  const period = hour < 12 ? 'AM' : 'PM'
  return `${DAYS[d.getDay()]} ${d.getDate()} de ${MONTHS[d.getMonth()]} a las ${hour}:00 ${period}`
}

interface PostCardProps {
  post: MatchPostWithCount
  currentUserId: string
  onDeleted: (id: string) => void
}

function PostCard({ post, currentUserId, onDeleted }: PostCardProps) {
  const [expanded, setExpanded] = useState(false)
  const [comments, setComments] = useState<MatchPostComment[]>([])
  const [commentText, setCommentText] = useState('')
  const [loadingComments, setLoadingComments] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [commentCount, setCommentCount] = useState(post.comment_count)

  async function handleExpand() {
    if (expanded) { setExpanded(false); return }
    setExpanded(true)
    if (comments.length === 0) {
      setLoadingComments(true)
      const res = await fetch(`/api/match-posts/${post.id}/comments`)
      if (res.ok) {
        const data = await res.json()
        setComments(data.comments || [])
      }
      setLoadingComments(false)
    }
  }

  async function handleComment(e: React.FormEvent) {
    e.preventDefault()
    if (!commentText.trim()) return
    setSubmitting(true)
    const res = await fetch(`/api/match-posts/${post.id}/comments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: commentText.trim() }),
    })
    if (res.ok) {
      const data = await res.json()
      setComments(prev => [...prev, data.comment])
      setCommentText('')
      setCommentCount(c => c + 1)
    }
    setSubmitting(false)
  }

  async function handleDelete() {
    const res = await fetch(`/api/match-posts/${post.id}`, { method: 'DELETE' })
    if (res.ok) onDeleted(post.id)
  }

  return (
    <div className="border border-gray-200 rounded-lg p-4 space-y-2 bg-white">
      <div className="flex items-start justify-between gap-2">
        <div className="space-y-1 flex-1 min-w-0">
          <p className="font-medium text-gray-900">
            {post.users?.full_name}
            {post.users?.level_tier && (
              <span className="text-sm font-normal text-gray-500 ml-1">· {post.users.level_tier}</span>
            )}
          </p>
          <span className={`inline-block text-xs font-medium px-2 py-0.5 rounded-full ${
            post.type === 'specific' ? 'bg-orange-100 text-orange-700' : 'bg-purple-100 text-purple-700'
          }`}>
            {post.type === 'specific' ? 'Partido específico' : 'Disponibilidad general'}
          </span>
          {post.type === 'specific' && post.date && post.hour !== null && (
            <p className="text-sm text-gray-700">{formatPostDate(post.date, post.hour)}</p>
          )}
          {(post.desired_level_tier || post.desired_categoria) && (
            <p className="text-sm text-gray-500">
              Busca: {[post.desired_level_tier, post.desired_categoria].filter(Boolean).join(' / ')}
            </p>
          )}
          {post.note && <p className="text-sm text-gray-700 italic">"{post.note}"</p>}
        </div>
        {post.user_id === currentUserId && (
          <button
            onClick={handleDelete}
            className="flex-shrink-0 text-gray-400 hover:text-red-500 transition-colors p-1"
            title="Eliminar publicación"
          >
            🗑️
          </button>
        )}
      </div>

      <button onClick={handleExpand} className="text-xs text-us-open-light-blue hover:underline">
        {expanded ? 'Ocultar comentarios' : `Ver comentarios (${commentCount})`}
      </button>

      {expanded && (
        <div className="pt-2 border-t border-gray-100 space-y-2">
          {loadingComments && <p className="text-xs text-gray-400">Cargando...</p>}
          {comments.map(c => (
            <div key={c.id} className="text-sm">
              <span className="font-medium">{c.users?.full_name}: </span>
              <span className="text-gray-700">{c.content}</span>
            </div>
          ))}
          <form onSubmit={handleComment} className="flex gap-2 mt-2">
            <input
              value={commentText}
              onChange={e => setCommentText(e.target.value)}
              placeholder="Añadir comentario..."
              className="flex-1 border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-us-open-light-blue"
            />
            <button
              type="submit"
              disabled={submitting || !commentText.trim()}
              className="px-3 py-1.5 bg-us-open-blue text-white text-sm rounded-lg disabled:opacity-50 hover:bg-us-open-light-blue transition-colors"
            >
              Enviar
            </button>
          </form>
        </div>
      )}
    </div>
  )
}
