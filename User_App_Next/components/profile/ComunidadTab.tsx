// ABOUTME: Comunidad tab root — shows partner suggestions and match post board.
// ABOUTME: Suggestions are passed as props (computed server-side). Posts are fetched on mount.
'use client'

import { useState, useEffect } from 'react'
import type { SuggestedPartner, MatchPostWithCount } from '@/types/database.types'
import PartnerCard from './PartnerCard'
import MatchPostFeed from './MatchPostFeed'
import MatchPostForm from './MatchPostForm'

interface Props {
  suggestions: SuggestedPartner[]
  currentUserId: string
}

type View = 'feed' | 'form'

export default function ComunidadTab({ suggestions, currentUserId }: Props) {
  const [posts, setPosts] = useState<MatchPostWithCount[]>([])
  const [loadingPosts, setLoadingPosts] = useState(true)
  const [view, setView] = useState<View>('feed')

  useEffect(() => {
    fetch('/api/match-posts')
      .then(r => r.json())
      .then(d => { setPosts(d.posts || []); setLoadingPosts(false) })
      .catch(() => setLoadingPosts(false))
  }, [])

  function handlePostCreated(post: MatchPostWithCount) {
    setPosts(prev => [post, ...prev])
    setView('feed')
  }

  function handlePostDeleted(id: string) {
    setPosts(prev => prev.filter(p => p.id !== id))
  }

  return (
    <div className="space-y-10">
      {/* Compañeros sugeridos */}
      <section>
        <h3 className="text-lg font-semibold text-us-open-blue mb-4">Compañeros sugeridos</h3>
        {suggestions.length === 0 ? (
          <p className="text-sm text-gray-500">
            Aún no hay compañeros sugeridos con tu nivel. A medida que más jugadores completen su perfil y reserven canchas aparecerán aquí.
          </p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {suggestions.map(s => (
              <PartnerCard key={s.user.id} partner={s} />
            ))}
          </div>
        )}
      </section>

      {/* Buscando partido */}
      <section>
        <h3 className="text-lg font-semibold text-us-open-blue mb-4">Buscar partido</h3>
        <div className="flex gap-2 mb-4">
          <button
            onClick={() => setView('feed')}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
              view === 'feed' ? 'bg-us-open-blue text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            Ver publicaciones
          </button>
          <button
            onClick={() => setView('form')}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
              view === 'form' ? 'bg-us-open-blue text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            Publicar
          </button>
        </div>
        {view === 'feed'
          ? <MatchPostFeed posts={posts} loading={loadingPosts} currentUserId={currentUserId} onDeleted={handlePostDeleted} />
          : <MatchPostForm onCreated={handlePostCreated} />
        }
      </section>
    </div>
  )
}
